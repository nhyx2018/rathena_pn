"""Two authenticated fixture accounts: party/re-entry plus actual combat packets."""
import json
import os
from pathlib import Path
import re
import struct
import time
import bank_live_client as bank

bank.GAME='storage-20260913-game'
bank.DB='storage-20260913-runtime-db'


class Client(bank.Client):
    def __init__(self,index):
        self.index=index
        super().__init__(attach=False,account_id=99000011+index*2,character_id=99000012+index*2,
                         username=('acceptance'+str(index)).encode(),password=b'validation-only')
    def command(self,text):
        time.sleep(.55)
        message=('ReleaseProbe'+str(self.index)+' : '+text+'\0').encode()
        self.world.sendall(struct.pack('<HH',0xf3,len(message)+4)+message)
        return bank.drain(self.world,.5)
    def close(self): self.world.close();self.char.close()


def expect(c,cmd,pattern):
    data=c.command(cmd);found=re.search(pattern,data)
    assert found,(cmd,data.hex())
    return found
def state(c): return expect(c,'@bhstate',rb'BH_STATE (\d+) (\d+) (\d+) ([^\x00]+)').groups()
def load(c): c.world.sendall(struct.pack('<H',0x7d));bank.drain(c.world,1)


def main():
    inspected=json.loads(bank.command(['docker','inspect',bank.GAME]))[0]
    assert inspected['Config']['Labels'].get('pn.bank.fixture')=='true'
    assert os.readlink('/proc/self/ns/net')==os.readlink('/proc/'+str(inspected['State']['Pid'])+'/ns/net')
    assert bank.sql('SELECT DATABASE()')=='bank_runtime'
    assert bank.sql('SELECT COUNT(*) FROM `char` WHERE online<>0')=='0'
    bank.sql("UPDATE login SET userid='acceptance0',user_pass='validation-only',group_id=99 WHERE account_id=99000011")
    bank.sql("UPDATE `char` SET name='ReleaseProbe0' WHERE char_id=99000012")
    bank.sql("INSERT INTO login(account_id,userid,user_pass,sex,email,group_id) VALUES(99000013,'acceptance1','validation-only','M','fixture@localhost',99)")
    bank.sql("INSERT INTO `char`(char_id,account_id,char_num,name,class,base_level,job_level,str,`int`,dex,sex,last_map,last_x,last_y,save_map,save_x,save_y,hp,max_hp,sp,max_sp,zeny) VALUES(99000014,99000013,0,'ReleaseProbe1',4252,275,50,100,100,100,'M','prontera',150,180,'prontera',150,180,10000,10000,1000,1000,1000000)")
    a=Client(0);b=Client(1);result={'passed':False,'production_data_used':False}
    try:
        expect(a,'@bhparty',rb'BH_CREATE 1');expect(b,'@bhjoin',rb'BH_JOIN 1')
        x,y=state(a),state(b);assert x[0]==y[0] and x[1]==b'1' and y[1]==b'0'
        expect(a,'@bhleader',rb'BH_LEADER 1')
        assert state(a)[1]==b'0' and state(b)[1]==b'1'
        instance=int(expect(b,'@bhinstance',rb'BH_INSTANCE (\d+)')[1]);assert instance>0
        time.sleep(2)
        for c in (a,b): expect(c,'@bhenter',rb'BH_ENTER 0');load(c)
        x,y=state(a),state(b);assert int(x[2])==int(y[2])==instance and x[3]==y[3]
        b.close();time.sleep(3);assert int(state(a)[2])==instance
        b=Client(1);expect(b,'@bhenter',rb'BH_ENTER 0');load(b)
        assert int(state(b)[2])==instance and state(b)[1]==b'1'
        result['party']={'passed':True,'checks':['two accounts join','leadership transfer','shared instance entry','leader disconnect','relogin and same-instance re-entry']}
        a.close();a=None
        expect(b,'@allskill',rb'All skills have been added')
        dummy=int(expect(b,'@bhcombat',rb'BH_DUMMY (\d+)')[1]);load(b)
        def hp(): return int(expect(b,'@bhhp',rb'BH_HP (\d+)')[1])
        damage={}
        for kind in ('physical','fire_vs_neutral','fire_vs_water'):
            if kind=='fire_vs_water':expect(b,'@bhwater',rb'BH_WATER')
            values=[]
            for _ in range(5):
                before=hp()
                request=struct.pack('<HIB',0x437,dummy,0) if kind=='physical' else struct.pack('<HHHI',0x438,1,19,dummy)
                b.world.sendall(request);reply=bank.drain(b.world,5);after=hp()
                assert 0<after<before,(kind,before,after,reply.hex())
                values.append(before-after)
            damage[kind]=values
        assert sum(damage['fire_vs_water']) < sum(damage['fire_vs_neutral'])
        result.update(passed=True,combat={'passed':True,'damage':damage},
            boundary='Real party builtins and actual map combat pipeline on a controlled monster; full quests/bosses/rendered timing are separate checks')
    finally:
        if a:a.close()
        b.close()
        (Path(os.environ['BANK_FIXTURE_ROOT'])/'party-combat.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
