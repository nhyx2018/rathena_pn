"""Fresh schema, synthetic accounts, actual login/char/map; private Docker network."""
from pathlib import Path
import json
import os
import re
import shutil
import subprocess
import time

ROOT=Path(os.environ.get('PN_STORAGE_TEST_ROOT', '/tmp/pn-multi-storage-proof')).resolve()
ROOT.mkdir(parents=True, exist_ok=True)
CAND=Path(os.environ.get('PN_STORAGE_CANDIDATE', str(Path(__file__).resolve().parents[2]))).resolve()
OUT=ROOT/'runtime'
DB='storage-20260913-runtime-db'
GAME='storage-20260913-game'
NET='storage-20260913-runtime-internal'
report={'passed':False,'production_data_used':False}

def run(args,**kw):return subprocess.run(args,check=True,**kw)
def sql(query,db=None,check=True):
    return subprocess.run(['docker','exec','-i',DB,'mariadb','--protocol=TCP','-h127.0.0.1','-uroot','-pbank-runtime-only','--batch','--raw','-N']+([db] if db else []),
                          input=query,text=True,capture_output=True,check=check)
def log_ready():
    for _ in range(240):
        log=OUT/'runtime-map.log'
        if log.exists() and b'Map Server is now online' in log.read_bytes():return
        time.sleep(.5)
    raise RuntimeError('Isolated login/char/map handshake did not complete')

# Refuse to touch pre-existing Docker resources, even if their names match fixtures.
for fixture in (DB,GAME):
    assert subprocess.run(['docker','container','inspect',fixture],capture_output=True).returncode != 0, 'Fixture name already in use: '+fixture
assert subprocess.run(['docker','network','inspect',NET],capture_output=True).returncode != 0, 'Fixture network already exists'

created=False
try:
    if OUT.exists():
        assert OUT.resolve().parent == ROOT.resolve()
        attempt = 1
        while (ROOT / f'runtime-attempt-{attempt:02d}').exists(): attempt += 1
        OUT.rename(ROOT / f'runtime-attempt-{attempt:02d}')
    OUT.mkdir(exist_ok=False)
    config=OUT/'conf';shutil.copytree(CAND/'conf',config)
    settings=[]
    for prefix in ('login_server','ipban_db','char_server','map_server','web_server','log_db'):
        settings += [f'{prefix}_ip: {DB}',f'{prefix}_port: 3306',f'{prefix}_id: root',f'{prefix}_pw: bank-runtime-only',f'{prefix}_db: bank_runtime']
    (config/'import/inter_conf.txt').write_text('\n'.join(settings)+'\n')
    (config/'import/map_conf.txt').write_text('bind_ip: 127.0.0.1\nmap_ip: 127.0.0.1\nchar_ip: 127.0.0.1\nchar_port: 6121\nmap_port: 5121\nuserid: s1\npasswd: p1\n')
    (config/'import/char_conf.txt').write_text('bind_ip: 127.0.0.1\nchar_ip: 127.0.0.1\nlogin_ip: 127.0.0.1\nlogin_port: 6900\nchar_port: 6121\nuserid: s1\npasswd: p1\n')
    (config/'import/login_conf.txt').write_text('bind_ip: 127.0.0.1\nlogin_port: 6900\n')
    run(['docker','network','create','--internal',NET],capture_output=True);created=True
    run(['docker','run','-d','--name',DB,'--network',NET,'--memory','768m','--cpus','1',
         '-e','MARIADB_ROOT_PASSWORD=bank-runtime-only','mariadb:noble'],capture_output=True)
    for _ in range(60):
        if sql('SELECT 1',check=False).returncode==0:break
        time.sleep(.5)
    else:raise RuntimeError('Disposable SQL did not become ready')
    sql('CREATE DATABASE bank_runtime')
    files=re.findall(r'< (sql-files/[^ ]+\.sql)',(CAND/'tools/ci/sql.sh').read_text())
    for name in files:sql((CAND/name).read_text(),'bank_runtime')
    sql("INSERT INTO login (account_id,userid,user_pass,sex,email,group_id) VALUES (99000011,'bankfixture','bank-fixture-only','M','fixture@localhost',0)",'bank_runtime')
    for slot in (0,1):
        sql(f"INSERT INTO `char` (char_id,account_id,char_num,name,class,base_level,job_level,str,sex,last_map,last_x,last_y,save_map,save_x,save_y,hp,max_hp,sp,max_sp,zeny) VALUES ({99000012+slot},99000011,{slot},'BankFixture{slot}',4252,275,50,100,'M','prontera',150,180,'prontera',150,180,10000,10000,1000,1000,1000000)",'bank_runtime')
    sql("INSERT INTO acc_reg_num(account_id,`key`,`index`,value) VALUES (99000011,'#BANKVAULT',0,1000000000)",'bank_runtime')
    sql("INSERT INTO inventory (char_id,nameid,amount,identify,refine,bound,unique_id,card0) VALUES (99000012,6024,1,1,0,0,0,0),(99000012,12781,10,1,0,0,0,0),(99000012,1201,1,1,10,2,987654321,4001)",'bank_runtime')
    with (config/'import/map_conf.txt').open('a') as f:f.write('npc: /evidence/bank-open-fixture.txt\n')
    with (config/'import/log_conf.txt').open('a') as f:f.write('\nlog_zeny: 1\n')
    (OUT/'bank-open-fixture.txt').write_text('prontera,150,181,4\tscript\tBankOpenFixture\t4_F_KAFRA1,{\nopenbank; end;\nOnInit: debugmes "BANK_FIXTURE_NPC_ID="+getnpcid(0); end;\n}\n')
    with (OUT/'bank-open-fixture.txt').open('a') as f:
        f.write('-\tscript\tStorageCartFixture\t-1,{\nOnCart: skill "MC_PUSHCART",10,3;setcart 1;dispbottom "Fixture cart: "+checkcart();end;\nOnInit: bindatcmd "storagefixturecart",strnpcinfo(3)+"::OnCart",0,99;end;\n}\n')
        f.write('-\tscript\tStorageLocationFixture\t-1,{\nOnInit: debugmes "STORAGE_FIXTURE_NPC_ID="+getnpcid(0,"PN Mystic Box")+",WALKABLE="+checkcell("prontera",158,185,CELL_CHKPASS);end;\n}\n')
    boot='''#!/bin/sh
set -eu
./login-server > /evidence/runtime-login.log 2>&1 &
./char-server > /evidence/runtime-char.log 2>&1 &
./map-server > /evidence/runtime-map.log 2>&1 &
wait
'''
    (OUT/'boot.sh').write_text(boot)
    run(['docker','run','-d','--name',GAME,'--label','pn.bank.fixture=true','--network',NET,'--memory','4g','--cpus','3',
         '-v',str(CAND)+':/rathena','-v',str(config)+':/rathena/conf:ro','-v',str(OUT)+':/evidence',
         '-w','/rathena','--entrypoint','sh',os.environ.get('PN_STORAGE_IMAGE','rathena:local'),'/evidence/boot.sh'],capture_output=True)
    log_ready()
    for role in ('login','char','map'):
        text=(OUT/f'runtime-{role}.log').read_text(errors='replace')
        clean=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',text)
        assert not re.search(r'\[Error\]|\[Fatal',clean),f'Initial startup error in {role}'
        (OUT/f'{role}-startup.log').write_text(text)
    print('Fresh-schema startup passed; running real authenticated multi-storage sessions.',flush=True)
    pid=run(['docker','inspect','--format','{{.State.Pid}}',GAME],capture_output=True,text=True).stdout.strip()
    client = Path(os.environ.get('PN_STORAGE_LIVE_CLIENT', str(CAND/'tools/ci/multi_storage_live_client.py'))).resolve()
    completed=subprocess.run(['nsenter','-t',pid,'-n','python3',str(client)],
                             text=True,capture_output=True,timeout=600,env=dict(os.environ,BANK_FIXTURE_ROOT=str(ROOT)))
    (OUT/'client.log').write_text(completed.stdout+completed.stderr)
    completed.check_returncode()
    report.update(json.loads(completed.stdout))
    print(json.dumps(report,indent=2),flush=True)
finally:
    if created:
        subprocess.run(['docker','rm','-f','-v',GAME,DB],capture_output=True)
        subprocess.run(['docker','network','rm',NET],capture_output=True)
    (ROOT/'live-report.json').write_text(json.dumps(report,indent=2))
