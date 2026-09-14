"""Check delayed RODEX claims against banking on the disposable storage fixture.

Uses actual authenticated game/companion packets and pauses only the fixture's
character process. --observe records the old behavior without calling it a pass.
"""
import argparse
import json
import os
from pathlib import Path
import struct
import time
import bank_live_client as bank

bank.GAME = 'storage-20260913-game'
bank.DB = 'storage-20260913-runtime-db'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--observe', action='store_true')
    args = parser.parse_args()
    inspect = json.loads(bank.command(['docker', 'inspect', bank.GAME]))[0]
    assert inspect['Config']['Labels'].get('pn.bank.fixture') == 'true'
    assert os.readlink('/proc/self/ns/net') == os.readlink('/proc/' + str(inspect['State']['Pid']) + '/ns/net')
    assert bank.sql('SELECT DATABASE()') == 'bank_runtime'
    assert bank.sql('SELECT COUNT(*) FROM `char` WHERE online<>0') == '0'
    maximum = 2147483647
    bank.sql(f'UPDATE `char` SET zeny={maximum-100} WHERE char_id={bank.CID}')
    bank.sql(f"UPDATE acc_reg_num SET value=1000 WHERE account_id={bank.AID} AND `key`='#BANKVAULT'")
    bank.sql(f"INSERT INTO mail(id,send_name,send_id,dest_name,dest_id,title,message,time,status,zeny,type) VALUES (99001,'AuditFixture',0,'BankFixture0',{bank.CID},'Capacity check','Synthetic delayed claim',UNIX_TIMESTAMP(),2,100,0)")
    c = bank.Client()
    before = c.refresh()
    total_before = before['wallet'] + before['bank'] + 100
    paused = False
    try:
        bank.command(['docker', 'exec', bank.GAME, 'sh', '-c', 'kill -STOP $(pidof char-server)'])
        paused = True
        c.world.sendall(struct.pack('<HQB', 0x9f1, 99001, 0))
        bank.drain(c.world, .5)
        response = c.send(c.bytes(2, 100))
    finally:
        if paused:
            bank.command(['docker', 'exec', bank.GAME, 'sh', '-c', 'kill -CONT $(pidof char-server)'])
    bank.drain(c.world, 1)
    after = c.wait() if response['result'] == 1 else c.refresh()
    remaining_mail = int(bank.sql('SELECT zeny FROM mail WHERE id=99001'))
    total_after = after['wallet'] + after['bank'] + remaining_mail
    result = {'passed': total_after == total_before and response['result'] == 4,
              'production_data_used': False, 'observed_only': args.observe,
              'scenario': 'mail claim reserved wallet capacity before bank withdrawal',
              'bank_result': response['result'], 'wallet_before': before['wallet'],
              'wallet_after': after['wallet'], 'bank_before': before['bank'],
              'bank_after': after['bank'], 'mail_after': remaining_mail,
              'total_before': total_before, 'total_after': total_after,
              'lost_zeny': total_before-total_after}
    c.close()
    if args.observe:
        print(json.dumps(result, indent=2), flush=True)
        return
    assert result['passed'], result
    cases = [result]
    time.sleep(2)
    # One remaining physical slot: a mail claim and bank ticket both need it.
    slots = int(bank.sql(f'SELECT inventory_slots FROM `char` WHERE char_id={bank.CID}'))
    assert 2 <= slots <= 200
    bank.sql(f'DELETE FROM inventory WHERE char_id={bank.CID}')
    rows = ','.join(f'({bank.CID},1201,1,1,{99000000+i})' for i in range(slots-1))
    bank.sql('INSERT INTO inventory(char_id,nameid,amount,identify,unique_id) VALUES '+rows)
    bank.sql(f"UPDATE acc_reg_num SET value=10000000 WHERE account_id={bank.AID} AND `key`='#BANKVAULT'")
    bank.sql(f"INSERT INTO mail(id,send_name,dest_name,dest_id,title,message,time,status,type) VALUES(99002,'AuditFixture','BankFixture0',{bank.CID},'Item capacity','Synthetic item claim',UNIX_TIMESTAMP(),2,0)")
    bank.sql('INSERT INTO mail_attachments(id,`index`,nameid,amount,identify) VALUES(99002,0,501,1,1)')
    c = bank.Client()
    try:
        bank.command(['docker','exec',bank.GAME,'sh','-c','kill -STOP $(pidof char-server)'])
        c.world.sendall(struct.pack('<HQB',0x9f3,99002,0))
        bank.drain(c.world,.5)
        response = c.send(c.bytes(5,1))
    finally:
        bank.command(['docker','exec',bank.GAME,'sh','-c','kill -CONT $(pidof char-server)'])
    bank.drain(c.world,1)
    after = c.refresh()
    assert response['result'] == 4 and after['bank'] == 10000000 and after['notes'] == 0, response
    c.close(); time.sleep(2)
    assert bank.sql(f'SELECT SUM(amount) FROM inventory WHERE char_id={bank.CID} AND nameid=501') == '1'
    assert bank.sql(f'SELECT COUNT(*) FROM inventory WHERE char_id={bank.CID}') == str(slots)
    assert bank.sql('SELECT COUNT(*) FROM mail_attachments WHERE id=99002') == '0'
    cases.append({'passed':True,'scenario':'delayed item claim keeps the last inventory slot; no lost item or bank debit'})
    # While composing, attachment snapshots must not be changed by the companion.
    c = bank.Client()
    c.world.sendall(struct.pack('<H24s',0xa08,b'BankFixture1'))
    wire = bank.drain(c.world,.4)
    assert struct.pack('<H',0xa12) in wire, 'Mail composer acknowledgement missing'
    before = c.refresh()
    response = c.send(c.bytes(1,100))
    assert response['result'] == 4 and response['wallet'] == before['wallet'] and response['bank'] == before['bank'], response
    c.world.sendall(struct.pack('<H',0xa03));bank.drain(c.world,.3)
    after = c.action(1,100)
    assert after['wallet'] == before['wallet']-100 and after['bank'] == before['bank']+100
    c.close();time.sleep(2)
    c=bank.Client();assert c.state['wallet']==after['wallet'] and c.state['bank']==after['bank'];c.close()
    cases.append({'passed':True,'scenario':'mail composer blocks bank mutation; cancelling permits an exact persisted deposit'})
    print(json.dumps({'passed':True,'production_data_used':False,'scenarios':cases},indent=2),flush=True)


if __name__ == '__main__':
    main()
