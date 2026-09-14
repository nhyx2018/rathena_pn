"""Read production guide dialogs through real packets; only the guarded synthetic fixture."""
import json
import os
from pathlib import Path
import re
import struct
import time
from multi_storage_live_client import Client, GAME, AID, CID, sql, command, drain, packets


def snapshot():
    return {name: sql(query) for name, query in {
        'quests': f'SELECT * FROM quest WHERE char_id={CID} ORDER BY quest_id',
        'registers': f'SELECT * FROM char_reg_num WHERE char_id={CID} ORDER BY `key`,`index`',
        'items': f'SELECT * FROM inventory WHERE char_id={CID} ORDER BY id',
        'wallet': f'SELECT zeny FROM `char` WHERE char_id={CID}',
        'bank': f'SELECT * FROM acc_reg_num WHERE account_id={AID} ORDER BY `key`,`index`',
    }.items()}


def main():
    inspected = json.loads(command(['docker','inspect',GAME]))[0]
    assert inspected['Config']['Labels'].get('pn.bank.fixture') == 'true'
    assert os.readlink('/proc/self/ns/net') == os.readlink('/proc/'+str(inspected['State']['Pid'])+'/ns/net')
    assert sql('SELECT DATABASE()') == 'bank_runtime'
    log = (Path(os.environ['BANK_FIXTURE_ROOT'])/'runtime/runtime-map.log').read_text(errors='replace')
    gid = int(re.search(r'GUIDE_FIXTURE_NPC_ID=(\d+)', log)[1])
    cases = [
        ('new character', 99, [], {}, [1], 'Prepare for Base Level 200'),
        ('chapter one entry', 200, [], {}, [1], 'Small Ash Tree'),
        ('chapter one in progress', 220, [(18368,0,0)], {}, [1], 'Continue Chapter 1'),
        ('chapter two level lock', 224, [(18377,2,0)], {}, [1], 'Reach Base Level 225'),
        ('chapter two start', 225, [(18377,2,0)], {}, [1], 'Bring 5 Apples'),
    ]
    for stage, expected in [(1,'Guardian El'),(2,'Crossroads'),(3,'Karilon'),(4,'Karilon'),
                            (5,'Orion'),(6,'Flame Researcher'),(7,'Flame Researcher'),
                            (8,'Nyrholt Keeper'),(9,'Nyrholt'),(10,'Folnir'),
                            (11,'Phantom'),(12,'complete Chapter 2'),(99,'not recognized')]:
        cases.append((f'chapter two stage {stage}', 250, [(18377,2,0)], {'CH2_Step':stage}, [1], expected))
    cases += [
        ('chapter two complete', 250, [(18377,2,0),(27101,2,0)], {'CH2_Step':12}, [1], 'Chapter 2 is complete'),
        ('biosphere level lock', 239, [], {}, [2,1], 'unlock at Base Level 240'),
        ('biosphere available', 240, [], {}, [2,1], 'Severe Cold: Available'),
        ('biosphere cooldown', 240, [(17612,0,int(time.time())+3600)], {}, [2,1], 'Severe Cold: On cooldown'),
        ('biosphere expired cooldown', 240, [(17612,0,1)], {}, [2,1], 'Severe Cold: Available'),
        ('phantom story lock', 250, [], {}, [2,2], 'Complete Chapter 2'),
        ('phantom available', 250, [(27101,2,0)], {}, [2,2], 'Available: accept'),
        ('phantom in progress', 250, [(27101,2,0),(27119,0,0)], {}, [2,2], 'In progress'),
        ('phantom reward ready', 250, [(27101,2,0),(27119,0,0)], {'CH2_DailyPhantom':1}, [2,2], 'Ready to report'),
        ('phantom cooldown', 250, [(27101,2,0),(27119,2,0)], {'CH2_Daily_CD_27119':int(time.time())+3600}, [2,2], 'On cooldown'),
        ('phantom timer expired', 250, [(27101,2,0),(27119,2,0)], {'CH2_Daily_CD_27119':1}, [2,2], 'Available: accept'),
        ('patrol locked', 250, [], {}, [2,3], 'Gimli report'),
        ('patrol side story', 250, [(17769,2,0)], {}, [2,3], 'Lugenburg Brothers'),
        ('patrol available', 250, [(17769,2,0),(17776,2,0)], {}, [2,3], 'Available: choose'),
        ('zero cell prerequisites', 200, [], {}, [4], 'Finish Chapter 1'),
        ('episode twenty one prerequisites', 220, [], {}, [5], 'Finish Episode 20'),
    ]
    results = []
    initial = Client(); initial.close(); time.sleep(2)
    guide_keys = ('CH2_Step','CH2_Crossroads','CH2_Nyrholt','CH2_Phantom','CH2_DailyPhantom',
                  'CH2_Daily_CD_27119','EP21_LugenburgDone','EP21_RaisedDaily','EP21_RaisedQuest',
                  'EP21_Gimli_Complete','EP21_Main_Complete')
    keys_sql = ','.join("'"+key+"'" for key in guide_keys)
    for label, level, quests, registers, choices, expected in cases:
        assert sql('SELECT COUNT(*) FROM `char` WHERE online<>0') == '0'
        sql(f"UPDATE `char` SET base_level={level},last_map='pn_office',last_x=108,last_y=79 WHERE char_id={CID}")
        sql(f'DELETE FROM quest WHERE char_id={CID}; DELETE FROM char_reg_num WHERE char_id={CID} AND `key` IN ({keys_sql})')
        for quest, state, timer in quests:
            sql(f"INSERT INTO quest(char_id,quest_id,state,time) VALUES({CID},{quest},'{state}',{timer})")
        for key, value in registers.items():
            assert re.fullmatch(r'[A-Za-z0-9_]+', key)
            sql(f"INSERT INTO char_reg_num(char_id,`key`,`index`,value) VALUES({CID},'{key}',0,{value})")
        c = Client()
        # Login initialization may set unrelated default registers; baseline after login.
        before = snapshot()
        c.world.sendall(struct.pack('<HIB',0x90,gid,0))
        wire = drain(c.world,.5); c.menu(wire)
        for index, choice in enumerate(choices):
            wire = c.choose(choice)
            if index+1 < len(choices):
                c.menu(wire)
        messages = '\n'.join(p[8:].rstrip(b'\0').decode('utf-8','replace') for p in packets(wire,0xb4,9))
        assert expected in messages, (label, expected, messages, wire.hex())
        c.end_dialog()
        c.close()
        for _ in range(30):
            if sql(f'SELECT online FROM `char` WHERE char_id={CID}') == '0': break
            time.sleep(.2)
        assert snapshot() == before, 'Guide mutated persistent state: '+label
        results.append({'case':label,'passed':True,'persistent_state_unchanged':True})
    print(json.dumps({'passed':True,'cases':results,'scope':'Actual server dialogs and persistence; not a rendered gameplay session'},indent=2))


if __name__ == '__main__':
    main()
