"""Conservation across actual bank, storage, cart, trade, mail and vending packets."""
import json
import os
import struct
import time
import bank_live_client as bank
import multi_storage_live_client as storage


class Client(storage.Client):
    def __init__(self,peer=False):
        self.name='EconomyPeer' if peer else 'BankFixture0'
        options=dict(account_id=99000021,character_id=99000022,username=b'economypeer',password=b'fixture-only') if peer else {}
        super().__init__(**options)
        self.attach()
    def chat(self,text):
        time.sleep(.55)
        message=(self.name+' : '+text+'\0').encode()
        self.world.sendall(struct.pack('<HH',0xf3,len(message)+4)+message)
        return bank.drain(self.world,.5)
    def close(self):
        self.companion.close();super().close()


def count():
    parts=["SELECT amount FROM inventory WHERE nameid=501", "SELECT amount FROM cart_inventory WHERE nameid=501", "SELECT amount FROM storage WHERE nameid=501", "SELECT amount FROM mail_attachments WHERE nameid=501"]
    return int(bank.sql('SELECT COALESCE(SUM(amount),0) FROM ('+' UNION ALL '.join(parts)+') AS totals'))
def wallets(): return bank.sql('SELECT char_id,zeny FROM `char` WHERE char_id IN (99000012,99000022) ORDER BY char_id')
def exchange(a,b):
    a.world.sendall(struct.pack('<HI',0xe4,b.aid));bank.drain(b.world,.3)
    b.world.sendall(struct.pack('<HB',0xe6,3));wire=bank.drain(a.world,.3);bank.drain(b.world,.3)
    assert struct.pack('<HB',0x1f5,3) in wire,('Trade accept acknowledgement missing',wire.hex())
def complete(a,b):
    for c in (a,b):c.world.sendall(struct.pack('<H',0xeb));bank.drain(c.world,.2)
    for c in (a,b):c.world.sendall(struct.pack('<H',0xef));bank.drain(c.world,.3)
    time.sleep(.4)


def main():
    info=json.loads(bank.command(['docker','inspect',storage.GAME]))[0]
    assert info['Config']['Labels'].get('pn.bank.fixture')=='true'
    assert os.readlink('/proc/self/ns/net')==os.readlink('/proc/'+str(info['State']['Pid'])+'/ns/net')
    assert bank.sql('SELECT DATABASE()')=='bank_runtime'
    assert bank.sql('SELECT COUNT(*) FROM `char` WHERE online<>0')=='0'
    bank.sql("INSERT INTO login(account_id,userid,user_pass,sex,email,group_id) VALUES(99000021,'economypeer','fixture-only','M','fixture@localhost',0)")
    bank.sql("INSERT INTO `char`(char_id,account_id,char_num,name,class,base_level,job_level,str,sex,last_map,last_x,last_y,save_map,save_x,save_y,hp,max_hp,sp,max_sp,zeny) VALUES(99000022,99000021,0,'EconomyPeer',4252,275,50,100,'M','prontera',151,180,'prontera',151,180,10000,10000,1000,1000,1000000)")
    for cid in (99000012,99000022):
        bank.sql(f'INSERT INTO inventory(char_id,nameid,amount,identify) VALUES({cid},501,20,1)')
        # Granted fixture skills survive recalculation outside a merchant tree.
        bank.sql(f'INSERT INTO skill(char_id,id,lv,flag) VALUES({cid},1,9,3),({cid},39,10,3),({cid},41,10,3)')
    a=Client();b=Client(True);cases=[]
    try:
        expected=count();assert expected==40
        before=a.refresh();a.action(1,1000);a.action(2,1000);a.action(5,1);after=a.action(6,1)
        assert after['wallet']==before['wallet'] and after['bank']==before['bank']-4000 and after['notes']==before['notes']
        cases.append('bank deposit/withdraw and ticket round trip preserve quantities and charge exactly 4000 in fees')
        assert b'Fixture cart: 1' in a.chat('@storagefixturecart')
        a.open('Storage I');a.transfer(0x364,a.inventory[501][0],5);a.close_storage()
        stored=a.open('Storage I');a.transfer(0x128,stored[501][0],2);a.close_storage()
        a.transfer(0x127,2,2)
        assert count()==expected
        cases.append('inventory to storage to cart to inventory conserves all potion units')
        before=wallets();exchange(a,b)
        a.world.sendall(struct.pack('<HHi',0xe8,a.inventory[501][0],1));bank.drain(a.world,.3)
        b.world.sendall(struct.pack('<HHi',0xe8,0,1000));bank.drain(b.world,.3)
        complete(a,b)
        assert count()==expected and wallets()!=before
        committed=wallets()
        for c in (a,b):c.world.sendall(struct.pack('<H',0xef));bank.drain(c.world,.2)
        assert count()==expected and wallets()==committed
        cases.append('two-account item-for-zeny trade and duplicate final confirmations conserve items and money')
        # Open a real vending shop from the peer's cart and buy one unit.
        assert b'AUDIT_VENDING_AREA ' in a.chat('@auditvendarea')
        for c in (a,b):
            c.world.sendall(struct.pack('<H',0x7d));bank.drain(c.world,.5)
        assert b'Fixture cart: 1' in b.chat('@storagefixturecart')
        b.transfer(0x126,b.inventory[501][0],1)
        b.world.sendall(struct.pack('<HHHI',0x438,1,41,b.aid));skill_wire=bank.drain(b.world,1)
        packet=struct.pack('<HH80sBHHI',0x1b2,93,b'Audit Shop',1,2,1,1000)
        b.world.sendall(packet);open_wire=bank.drain(b.world,.7)
        a.world.sendall(struct.pack('<HI',0x130,b.aid));wire=bank.drain(a.world,.5)
        listings=list(storage.packets(wire,0xb3d,12));assert listings,('Vending list missing',skill_wire.hex(),open_wire.hex(),wire.hex())
        shop=listings[-1];uid=struct.unpack_from('<I',shop,8)[0]
        price,amount,index=struct.unpack_from('<IHH',shop,12);assert price==1000 and amount==1
        buy=struct.pack('<HHIIHH',0x801,16,b.aid,uid,1,index)
        a.world.sendall(buy);bank.drain(a.world,.7);bank.drain(b.world,.3)
        assert count()==expected and wallets()==before
        a.world.sendall(buy);bank.drain(a.world,.3)
        assert count()==expected and wallets()==before
        b.world.sendall(struct.pack('<H',0x12e));bank.drain(b.world,.3)
        cases.append('native vending purchase transfers the exact price; a sold-out replay gives no extra item')
        # Send one potion via RODEX, then claim it from a fresh recipient session.
        a.world.sendall(struct.pack('<H24s',0xa08,b'EconomyPeer'));bank.drain(a.world,.3)
        a.world.sendall(struct.pack('<HHH',0xa04,a.inventory[501][0],1));bank.drain(a.world,.3)
        title=b'Audit transfer\0';body=b'Synthetic conservation check\0'
        mail=struct.pack('<HH24s24sQHHI',0xa6e,68+len(title)+len(body),b'EconomyPeer',b'BankFixture0',0,len(title),len(body),b.cid)+title+body
        a.world.sendall(mail);bank.drain(a.world,.8)
        a.world.sendall(struct.pack('<H',0xa03));bank.drain(a.world,.3)
        assert count()==expected
        mail_id=int(bank.sql("SELECT id FROM mail WHERE dest_id=99000022 AND title='Audit transfer' ORDER BY id DESC LIMIT 1"))
        b.close();time.sleep(2);b=Client(True)
        b.world.sendall(struct.pack('<HBQ',0x9ea,0,mail_id));bank.drain(b.world,.4)
        b.world.sendall(struct.pack('<HQB',0x9f3,mail_id,0));bank.drain(b.world,.8)
        b.world.sendall(struct.pack('<HQB',0x9f3,mail_id,0));bank.drain(b.world,.3)
        a.close();a=None;b.close();b=None;time.sleep(2)
        assert count()==expected
        assert bank.sql(f'SELECT COUNT(*) FROM mail_attachments WHERE id={mail_id}')=='0'
        cases.append('RODEX send, relog, attachment claim and repeated claim conserve item quantities')
    finally:
        if a:a.close()
        if b:b.close()
    print(json.dumps({'passed':True,'production_data_used':False,'scenarios':cases,'potions_before':expected,'potions_after':count()},indent=2))


if __name__=='__main__':main()
