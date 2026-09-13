"""Authenticated native NPC/storage packets; explicitly isolated Docker fixture only."""
from pathlib import Path
import json
import os
import re
import socket
import struct
import time
import bank_live_client as bank

GAME = 'storage-20260913-game'
DB = 'storage-20260913-runtime-db'
bank.GAME, bank.DB = GAME, DB
AID, CID = bank.AID, bank.CID
sql, command, drain = bank.sql, bank.command, bank.drain
cases = []


def packets(wire, kind, minimum=4):
    marker = struct.pack('<H', kind)
    start = 0
    while True:
        pos = wire.find(marker, start)
        if pos < 0: return
        start = pos + 2
        if pos + 4 > len(wire): continue
        size = struct.unpack_from('<H', wire, pos + 2)[0]
        if minimum <= size <= len(wire) - pos:
            yield wire[pos:pos + size]


def items(wire, container):
    found = {}
    for kind, stride in ((0xb09, 34), (0xb39, 68)):
        for packet in packets(wire, kind, 5):
            if packet[4] != container or (len(packet)-5) % stride: continue
            for offset in range(5, len(packet), stride):
                index, item = struct.unpack_from('<HI', packet, offset)
                found.setdefault(item, []).append(index)
    return found


class Client(bank.Client):
    def __init__(self, slot=0):
        captured = []
        def capture(*args, **kw):
            result = drain(*args, **kw); captured.append(result); return result
        bank.drain = capture
        try: super().__init__(slot, attach=False)
        finally: bank.drain = drain
        self.inventory = items(b''.join(captured), 0)
        self.cart = items(b''.join(captured), 1)
        self.slot = slot

    def chat(self, text):
        time.sleep(.55)
        message = f'BankFixture{self.slot} : {text}\0'.encode()
        self.world.sendall(struct.pack('<HH', 0xf3, 4+len(message)) + message)
        return drain(self.world, .4)

    def menu(self, wire=None):
        if wire is None: wire = self.chat('@storage')
        menus = list(packets(wire, 0xb7, 9))
        assert menus, ('NPC menu missing', wire.hex())
        packet = menus[-1]; self.npc = struct.unpack_from('<I', packet, 4)[0]
        self.labels = packet[8:].rstrip(b'\0').decode().split(':')
        return self.labels

    def choose(self, choice):
        self.world.sendall(struct.pack('<HIB', 0xb8, self.npc, choice))
        return drain(self.world, .4)

    def pick(self, label):
        labels = [re.sub(r'\^[0-9A-Fa-f]{6}', '', value) for value in self.labels]
        assert label in labels, (label, labels)
        return self.choose(labels.index(label)+1)

    def next(self):
        self.world.sendall(struct.pack('<HI', 0xb9, self.npc))
        return drain(self.world, .4)

    def end_dialog(self):
        self.world.sendall(struct.pack('<HI', 0x146, self.npc)); return drain(self.world, .4)

    def open(self, label):
        self.menu(); assert label in self.labels, (label, self.labels)
        wire = self.pick(label)
        if struct.pack('<HI', 0xb6, self.npc) in wire:
            wire += self.end_dialog()
        starts = [p for p in packets(wire, 0xb08, 6) if p[4] == 2]
        assert starts and starts[-1][5:].rstrip(b'\0').decode() == label, (label, wire.hex())
        assert struct.pack('<H', 0xf2) in wire, 'Storage amount packet missing'
        amount_pos = wire.rindex(struct.pack('<H', 0xf2))
        assert struct.unpack_from('<H', wire, amount_pos+4)[0] == 600
        return items(wire, 2)

    def close_storage(self):
        self.world.sendall(struct.pack('<H', 0x193)); drain(self.world, .35)

    def transfer(self, packet, index, amount, seconds=.65):
        self.world.sendall(struct.pack('<HHi', packet, index, amount))
        return drain(self.world, seconds)

    def purchase_prompt(self, label, direct=False):
        self.menu()
        if not direct: self.menu(self.pick('Expand Storages'))
        wire = self.pick(label)
        self.menu(wire)
        assert self.labels == ['Unlock for 50,000,000 zeny', 'Cancel'], self.labels
        assert b'600-slot page' in wire and b'character wallet' in wire, wire.hex()
        return wire

    def unlock(self, label, direct=False):
        self.purchase_prompt(label, direct)
        return self.pick('Unlock for 50,000,000 zeny')

    def close(self):
        self.world.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
        self.world.close(); self.char.close()


def main():
    inspect = json.loads(command(['docker', 'inspect', GAME]))[0]
    assert inspect['Config']['Labels'].get('pn.bank.fixture') == 'true'
    assert os.readlink('/proc/self/ns/net') == os.readlink('/proc/'+str(inspect['State']['Pid'])+'/ns/net')
    assert sql('SELECT DATABASE()') == 'bank_runtime'
    assert sql('SELECT COUNT(*) FROM `char` WHERE online<>0') == '0'
    sql(f'UPDATE `char` SET zeny=1000000000 WHERE char_id={CID}')
    sql(f'UPDATE `char` SET zeny=49999999 WHERE char_id={CID+1}')
    sql(f'DELETE FROM inventory WHERE char_id IN ({CID},{CID+1})')
    sql(f"INSERT INTO inventory(char_id,nameid,amount,identify,bound,refine,unique_id,card0,option_id0,option_val0,enchantgrade) VALUES ({CID},501,20,1,0,0,0,0,0,0,0),({CID},4001,5,1,0,0,0,0,0,0,0),({CID},1201,1,1,4,10,98765001,4001,1,27,2),({CID},1202,1,1,0,8,98765002,4002,2,11,1)")
    c = Client()
    labels = c.menu()
    assert len(labels) == 23 and labels[0] == 'Expand Storages'
    assert labels[1:4] == ['Storage I', 'Storage II', 'Storage III']
    assert labels[4:6] == ['Guild Storage', 'Master Storage I']
    assert sum(s.startswith('^FF0000') for s in labels) == 12
    assert labels[18:20] == ['Card Storage', 'Character Bound Storage']
    c.pick('Close'); c.end_dialog()
    cases.append('all screenshot menu entries and twelve initially locked pages')
    c.menu(c.chat('@mstorage'))
    assert c.labels == labels
    c.pick('Close'); c.end_dialog()
    cases.append('both player commands show Expand Storages as the first visible menu option')
    log = (Path(os.environ['BANK_FIXTURE_ROOT'])/'runtime/runtime-map.log').read_text(errors='replace')
    match = re.search(r'STORAGE_FIXTURE_NPC_ID=(\d+),WALKABLE=(\d+)', log)
    assert match and int(match[1]) > 0 and match[2] == '1', 'Mystic Box must exist on a walkable Prontera cell'
    time.sleep(.55)
    c.world.sendall(struct.pack('<HIB', 0x90, int(match[1]), 0))
    c.menu(drain(c.world, .4))
    assert c.labels == labels, 'Clicking the real Mystic Box NPC must open the same menu'
    c.menu(c.pick('Storage IV'))
    assert c.labels == ['Unlock for 50,000,000 zeny', 'Cancel']
    c.menu(c.pick('Cancel')); c.pick('Close'); c.end_dialog()
    cases.append('visible Mystic Box NPC opens multi-storage and locked-page purchase confirmation')
    wallet = sql(f'SELECT zeny FROM `char` WHERE char_id={CID}')
    journal = sql('SELECT COUNT(*) FROM pn_storage_commits')
    c.purchase_prompt('Storage IV', direct=True)
    assert sql(f'SELECT zeny FROM `char` WHERE char_id={CID}') == wallet
    c.menu(c.pick('Cancel')); c.pick('Close'); c.end_dialog()
    c.purchase_prompt('Storage IV')
    c.choose(255)  # Native menu Escape/cancel; 0x146 only acknowledges close/close2.
    assert sql(f'SELECT zeny FROM `char` WHERE char_id={CID}') == wallet
    assert sql('SELECT COUNT(*) FROM pn_storage_commits') == journal
    assert sql(f"SELECT COUNT(*) FROM acc_reg_num WHERE account_id={AID} AND `key`='#PNStoragePaid'") == '0'
    cases.append('direct and expansion-list confirmations do not charge on inspection, Cancel or menu Escape')
    assert c.open('Storage I') == {}
    c.transfer(0x364, c.inventory[501][0], 2)
    assert sql(f'SELECT amount FROM storage WHERE account_id={AID} AND nameid=501') == '2'
    assert sql(f'SELECT amount FROM inventory WHERE char_id={CID} AND nameid=501') == '18'
    c.close_storage()
    assert c.open('Storage II') == {}
    c.transfer(0x364, c.inventory[501][0], 3)
    assert sql(f'SELECT amount FROM pn_storage_02 WHERE account_id={AID} AND nameid=501') == '3'
    c.close_storage(); stored = c.open('Storage I')
    c.transfer(0x365, stored[501][0], 1)
    assert sql(f'SELECT amount FROM storage WHERE account_id={AID} AND nameid=501') == '1'
    c.close_storage()
    cases.append('independent normal and premium pages, native deposit and withdrawal, immediate SQL persistence')
    c.open('Card Storage')
    count = sql('SELECT COUNT(*) FROM pn_storage_commits')
    c.transfer(0x364, c.inventory[501][0], 1)
    assert sql('SELECT COUNT(*) FROM pn_storage_commits') == count
    assert sql('SELECT COUNT(*) FROM pn_card_storage') == '0'
    c.transfer(0x364, c.inventory[4001][0], 2)
    assert sql('SELECT nameid,amount FROM pn_card_storage') == '4001\t2'
    c.close_storage()
    c.open('Character Bound Storage')
    c.transfer(0x364, c.inventory[501][0], 1)
    assert sql('SELECT COUNT(*) FROM pn_character_storage') == '0'
    c.transfer(0x364, c.inventory[1201][0], 1)
    assert sql('SELECT char_id,bound,refine,unique_id,card0,option_id0,option_val0,enchantgrade FROM pn_character_storage') == f'{CID}\t4\t10\t98765001\t4001\t1\t27\t2'
    c.close_storage()
    cases.append('card-only and character-bound filters preserve metadata and reject invalid deposits')
    c.menu(); c.menu(c.pick('Rename Storages')); wire = c.pick('Storage II')
    value = b'Supplies\0'
    c.world.sendall(struct.pack('<HHI', 0x1d5, 8+len(value), c.npc)+value)
    assert b'name saved' in drain(c.world, .4)
    c.menu(c.next()); c.menu(c.pick('Reorder Storages')); c.menu(c.pick('Supplies')); c.choose(1)
    assert c.menu(c.next())[1] == 'Supplies'
    c.pick('Close'); c.end_dialog()
    assert c.open('Supplies')[501]; c.close_storage()
    cases.append('rename and reorder keep the same page inventory and native window title')
    wire = c.unlock('Storage IV', direct=True)
    assert b'now unlocked' in wire, wire.hex()
    assert sql(f'SELECT zeny FROM `char` WHERE char_id={CID}') == '950000000'
    assert sql(f"SELECT value FROM acc_reg_num WHERE account_id={AID} AND `key`='#PNStoragePaid' AND `index`=102") == '1'
    c.menu(c.next()); c.pick('Close'); c.end_dialog()
    assert c.open('Storage IV') == {}; c.close_storage()
    cases.append('confirmed expansion charges exactly 50M character zeny and unlocks one 600-slot page')
    c.close(); time.sleep(2); c = Client(1)
    labels = c.menu()
    assert labels[1] == 'Supplies', (labels, sql("SELECT * FROM acc_reg_num WHERE `key` LIKE '#PNStorage%' ORDER BY `key`,`index`"), sql("SELECT * FROM acc_reg_str WHERE `key` LIKE '#PNStorage%'"))
    c.pick('Close'); c.end_dialog()
    assert 501 in c.open('Supplies'); c.close_storage()
    assert 4001 in c.open('Card Storage'); c.close_storage()
    assert c.open('Character Bound Storage') == {}; c.close_storage()
    assert c.open('Storage IV') == {}; c.close_storage()
    wire = c.unlock('Storage V', direct=True); assert b'need 50,000,000' in wire
    assert sql(f'SELECT zeny FROM `char` WHERE char_id={CID+1}') == '49999999'
    assert sql(f"SELECT COUNT(*) FROM acc_reg_num WHERE account_id={AID} AND `key`='#PNStoragePaid' AND `index`=103") == '0'
    c.menu(c.next()); c.pick('Close'); c.end_dialog(); c.close(); time.sleep(2)
    cases.append('sibling shares account pages, names, order and unlocks; private bound page stays separate; insufficient funds rejected')
    c = Client(); c.open('Master Storage I')
    before = sql(f'SELECT amount FROM inventory WHERE char_id={CID} AND nameid=501')
    sql("CREATE TRIGGER storage_runtime_fault BEFORE INSERT ON pn_storage_commits FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='intentional storage fixture fault'")
    c.transfer(0x364, c.inventory[501][0], 1, 1.3)
    assert sql(f'SELECT amount FROM inventory WHERE char_id={CID} AND nameid=501') == before
    assert sql('SELECT COUNT(*) FROM pn_master_storage_01') == '0'
    c.close(); time.sleep(.3); sql('DROP TRIGGER storage_runtime_fault'); time.sleep(2)
    c = Client(); assert 501 in c.open('Master Storage I'); c.close_storage()
    assert sql(f'SELECT amount FROM inventory WHERE char_id={CID} AND nameid=501') == str(int(before)-1)
    cases.append('failed transfer rolls back both containers, then retries safely after client disconnect')
    sql("CREATE TRIGGER storage_runtime_fault BEFORE INSERT ON pn_storage_commits FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='intentional expansion fixture fault'")
    c.unlock('Storage V'); time.sleep(1)
    assert sql(f'SELECT zeny FROM `char` WHERE char_id={CID}') == '950000000'
    assert sql(f"SELECT COUNT(*) FROM acc_reg_num WHERE account_id={AID} AND `key`='#PNStoragePaid' AND `index`=103") == '0'
    c.close(); sql('DROP TRIGGER storage_runtime_fault'); time.sleep(2)
    c = Client(); assert sql(f'SELECT zeny FROM `char` WHERE char_id={CID}') == '900000000'
    assert c.open('Storage V') == {}; c.close_storage()
    assert sql('SELECT COUNT(*) FROM pn_storage_commits WHERE action=3') == '2'
    cases.append('failed expansion and disconnected confirmation charge once after recovery')
    cart_wire = c.chat('@storagefixturecart')
    assert b'Fixture cart: 1' in cart_wire, ('Fixture cart not active', cart_wire.hex())
    stored = c.open('Supplies')
    c.transfer(0x128, stored[501][0], 1)
    assert sql(f'SELECT amount FROM cart_inventory WHERE char_id={CID} AND nameid=501') == '1'
    c.transfer(0x129, 2, 1)
    assert sql(f'SELECT COUNT(*) FROM cart_inventory WHERE char_id={CID}') == '0'
    assert sql('SELECT COUNT(*) FROM pn_storage_commits WHERE action=2') == '2'
    c.close_storage()
    cases.append('native storage-to-cart and cart-to-storage transfers commit both containers')
    before = sql(f'SELECT amount FROM inventory WHERE char_id={CID} AND nameid=501')
    stored = c.open('Supplies')
    for index, amount in ((0,1),(65535,1),(c.inventory[501][0],0),(c.inventory[501][0],-1),(c.inventory[501][0],2147483647)):
        c.transfer(0x364, index, amount, .15)
    assert sql(f'SELECT amount FROM inventory WHERE char_id={CID} AND nameid=501') == before
    c.close_storage()
    cases.append('invalid indices, negative/zero and oversized quantities cannot move items')
    c.menu(); wire = c.choose(c.labels.index('Guild Storage')+1)+c.end_dialog()
    assert b'Guild Storage is unavailable' in wire
    cases.append('guild page uses native membership and permission checks')
    c.close(); time.sleep(2)
    # Fill a separate page while the synthetic character is offline.
    rows = ','.join(f'({AID},1201,1,1,{80000000+i})' for i in range(600))
    sql('INSERT INTO pn_storage_03(account_id,nameid,amount,identify,unique_id) VALUES '+rows)
    c = Client(); full = c.open('Storage III'); assert len(full[1201]) == 600
    count = sql('SELECT COUNT(*) FROM pn_storage_commits')
    c.transfer(0x364, c.inventory[1202][0], 1)
    assert sql('SELECT COUNT(*) FROM pn_storage_commits') == count
    assert sql(f'SELECT COUNT(*) FROM inventory WHERE char_id={CID} AND nameid=1202') == '1'
    c.close_storage()
    cases.append('all 600 slots load through split client packets and a full page rejects an extra item')
    c.open('Master Storage I'); c.transfer(0x364, c.inventory[501][0], 1); c.close_storage()
    expected = sql(f'SELECT amount FROM inventory WHERE char_id={CID} AND nameid=501')
    command(['docker','exec',GAME,'sh','-c','kill -KILL $(pidof map-server)']); c.close(); bank.start_map()
    c = Client(); assert sql(f'SELECT amount FROM inventory WHERE char_id={CID} AND nameid=501') == expected
    assert 501 in c.open('Master Storage I')
    sql("CREATE TRIGGER storage_runtime_fault BEFORE INSERT ON pn_storage_commits FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='intentional crash fixture fault'")
    c.transfer(0x364, c.inventory[501][0], 1)
    command(['docker','exec',GAME,'sh','-c','kill -KILL $(pidof map-server)']); c.close()
    sql('DROP TRIGGER storage_runtime_fault'); bank.start_map(); c = Client()
    assert sql(f'SELECT amount FROM inventory WHERE char_id={CID} AND nameid=501') == expected
    cases.append('committed transfer survives a map crash; an uncommitted transfer rolls back after a map crash')
    c.close(); time.sleep(2)
    sql(f'UPDATE login SET group_id=99 WHERE account_id={AID}')
    c = Client()
    c.purchase_prompt('Storage VI', direct=True)
    c.menu(c.pick('Cancel'))
    assert c.labels[0] == 'Expand Storages'
    c.pick('Close'); c.end_dialog(); c.close(); time.sleep(2)
    cases.append('GM level 99 uses the same command menu and locked-page purchase confirmation')
    result = {'passed': True, 'production_data_used': False, 'scenarios': cases}
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
