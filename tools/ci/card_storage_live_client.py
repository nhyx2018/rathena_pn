"""Card-only inventory/cart deposit matrix against an isolated native game fixture."""
from pathlib import Path
import json
import os
import re
import time
from multi_storage_live_client import Client, GAME, AID, CID, sql, command, items

NONCARDS = (501, 601, 909, 1201, 2301, 1750, 616, 6024, 12781, 9001, 10001, 24000)
CARDS = (4001, 4002, 300001)


def snapshot():
    return [sql(query) for query in (
        f'SELECT * FROM inventory WHERE char_id={CID} ORDER BY id',
        f'SELECT * FROM cart_inventory WHERE char_id={CID} ORDER BY id',
        f'SELECT * FROM pn_card_storage WHERE account_id={AID} ORDER BY id',
        f'SELECT zeny FROM `char` WHERE char_id={CID}',
        f'SELECT * FROM pn_storage_commits WHERE account_id={AID} ORDER BY nonce_hi,nonce_lo,request_id')]


def main():
    inspect = json.loads(command(['docker', 'inspect', GAME]))[0]
    assert inspect['Config']['Labels'].get('pn.bank.fixture') == 'true'
    assert os.readlink('/proc/self/ns/net') == os.readlink('/proc/'+str(inspect['State']['Pid'])+'/ns/net')
    assert sql('SELECT DATABASE()') == 'bank_runtime'
    rejected = accepted = 0
    scenarios = []
    for group in (0, 99):
        assert sql('SELECT COUNT(*) FROM `char` WHERE online<>0') == '0'
        sql(f'UPDATE login SET group_id={group} WHERE account_id={AID}')
        for table in ('inventory', 'cart_inventory'):
            sql(f'DELETE FROM {table} WHERE char_id={CID}')
            rows = ','.join(f'({CID},{item},3,1,{4001 if item == 1201 else 0})' for item in NONCARDS+CARDS)
            sql(f'INSERT INTO {table}(char_id,nameid,amount,identify,card0) VALUES '+rows)
        sql(f'DELETE FROM pn_card_storage WHERE account_id={AID}')
        label = 'Card Storage' if group == 0 else 'General Items'
        if group == 99:
            sql(f"REPLACE INTO acc_reg_str(account_id,`key`,`index`,value) VALUES ({AID},'#PNStorageName$',116,'{label}')")
        c = Client()
        cart_wire = c.chat('@storagefixturecart')
        assert b'Fixture cart: 1' in cart_wire
        c.cart.update(items(cart_wire, 1))
        assert all(item in c.inventory and item in c.cart for item in NONCARDS+CARDS)
        assert c.open(label) == {}
        for route, packet, source in (('inventory', 0x364, c.inventory), ('cart', 0x129, c.cart)):
            before = snapshot()
            for item in NONCARDS:
                wire = c.transfer(packet, source[item][0], 1, .25)
                assert b'Card Storage accepts card items only.' in wire, (group, route, item, wire.hex())
                assert snapshot() == before, (group, route, item, 'rejected deposit changed persistent data')
                rejected += 1
            scenarios.append(f'group {group}: {len(NONCARDS)} non-card items rejected from {route} without item, wallet or journal changes')
            for item in CARDS:
                quantity = 2 if route == 'inventory' else 1
                c.transfer(packet, source[item][0], quantity)
                expected = 2 if route == 'inventory' else 3
                assert sql(f'SELECT SUM(amount) FROM pn_card_storage WHERE account_id={AID} AND nameid={item}') == str(expected)
                accepted += 1
            scenarios.append(f'group {group}: normal and six-digit-ID cards accepted from {route} and stacked correctly')
        if group == 99:
            before = snapshot()
            c.chat('@storeall')
            assert snapshot() == before, 'GM bulk storage command bypassed the open Card Storage page'
            scenarios.append('GM privilege, carded equipment, page rename and bulk storage cannot bypass the card filter')
        c.close_storage()
        stored = c.open(label)
        assert set(stored) == set(CARDS)
        for item in CARDS:
            c.transfer(0x365, stored[item][0], 3)
            assert sql(f'SELECT SUM(amount) FROM inventory WHERE char_id={CID} AND nameid={item}') == '4'
            assert sql(f'SELECT SUM(amount) FROM cart_inventory WHERE char_id={CID} AND nameid={item}') == '2'
        assert sql(f'SELECT COUNT(*) FROM pn_card_storage WHERE account_id={AID}') == '0'
        c.close_storage(); c.close(); time.sleep(2)
        scenarios.append(f'group {group}: card withdrawal preserves the total inventory/cart item count')
    for role in ('map', 'char'):
        path = Path(os.environ['BANK_FIXTURE_ROOT'])/'runtime'/f'runtime-{role}.log'
        log = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', path.read_text(errors='replace'))
        assert not re.search(r'\[Error\]|\[Fatal', log), role+' runtime error'
    print(json.dumps({'passed': True, 'production_data_used': False,
                      'noncard_deposits_rejected': rejected, 'card_deposits_accepted': accepted,
                      'noncard_item_ids': NONCARDS, 'card_item_ids': CARDS, 'scenarios': scenarios}, indent=2))


if __name__ == '__main__': main()
