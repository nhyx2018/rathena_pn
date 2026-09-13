"""Actual character SQL code, a disposable MariaDB, fault injection and a DB crash."""
from pathlib import Path
import json
import hashlib
import os
import re
import subprocess
import time

ROOT = Path(os.environ.get('PN_STORAGE_TEST_ROOT', '/tmp/pn-multi-storage-proof')).resolve()
ROOT.mkdir(parents=True, exist_ok=True)
CAND = Path(os.environ.get('PN_STORAGE_CANDIDATE', str(Path(__file__).resolve().parents[2]))).resolve()
DB = 'storage-20260913-db'
NET = 'storage-20260913-internal'
PROBE = 'storage-20260913-crash-probe'
report = {'passed': False, 'production_database_accessed': False}

def run(args, **kw):
    return subprocess.run(args, check=True, **kw)

def sql(query, check=True):
    return subprocess.run(['docker','exec','-i',DB,'mariadb','--protocol=TCP','-h127.0.0.1','-uroot','-pstorage-validation-only','--batch','--raw','-N'],
                          input=query,text=True,capture_output=True,check=check)

def ready():
    for _ in range(60):
        if sql('SELECT 1',False).returncode == 0:
            return
        time.sleep(.5)
    raise RuntimeError('Disposable DB did not become ready')

# Refuse to touch pre-existing Docker resources, even if their names match fixtures.
for fixture in (DB,PROBE):
    assert subprocess.run(['docker','container','inspect',fixture],capture_output=True).returncode != 0, 'Fixture name already in use: '+fixture
assert subprocess.run(['docker','network','inspect',NET],capture_output=True).returncode != 0, 'Fixture network already exists'

created = False
try:
    run(['docker','network','create','--internal',NET],capture_output=True)
    created = True
    run(['docker','run','-d','--name',DB,'--network',NET,'--memory','512m','--cpus','1',
         '-e','MARIADB_ROOT_PASSWORD=storage-validation-only','mariadb:noble'],capture_output=True)
    ready()
    main = (CAND/'sql-files/main.sql').read_text()
    sql('CREATE DATABASE storage_probe; USE storage_probe;\n'+main)
    command = ('g++ -g -O1 -std=c++17 -DPACKETVER=20260219 -I./src -I./3rdparty/libconfig -I./3rdparty/rapidyaml/src '
               '-I./3rdparty/rapidyaml/ext/c4core/src -I/usr/include/mysql -I/usr/include/mysql/mysql '
               'tools/ci/multi_storage_sql_runtime.cpp src/char/obj/*.o 3rdparty/libconfig/obj/libconfig.a '
               'src/common/obj/common.a 3rdparty/rapidyaml/obj/ryml.a -lz -ldl -lmariadb -Wl,--wrap=main -o /evidence/storage-sql-probe')
    with (ROOT/'sql-probe-build.log').open('wb') as log:
        run(['docker','run','--rm','--network','none','-v',str(CAND)+':/rathena:ro','-v',str(ROOT)+':/evidence',
             '-w','/rathena','--entrypoint','sh',os.environ.get('PN_STORAGE_IMAGE','rathena:local'),'-c',command],stdout=log,stderr=subprocess.STDOUT)
    with (ROOT/'sql-runtime.log').open('wb') as log:
        run(['docker','run','--rm','--network',NET,'-v',str(ROOT)+':/evidence','-v',str(CAND)+':/rathena:ro','-w','/rathena','--entrypoint','/evidence/storage-sql-probe',
             os.environ.get('PN_STORAGE_IMAGE','rathena:local')],stdout=log,stderr=subprocess.STDOUT,timeout=45)
    output = (ROOT/'sql-runtime.log').read_text(errors='replace')
    match = re.search(r'STORAGE_SQL_PASS (\d+)',output)
    assert match, output[-1500:]
    report['sql_checks'] = int(match[1])
    print('SQL checks passed:',match[1],flush=True)
    def data_dump():
        return run(['docker','exec',DB,'mariadb-dump','-uroot','-pstorage-validation-only',
            '--compact','--skip-comments','--no-create-info','--skip-add-locks','--skip-disable-keys',
            '--skip-extended-insert','--order-by-primary','storage_probe'],capture_output=True).stdout
    before = data_dump()
    sql('USE storage_probe;\n'+(CAND/'sql-files/upgrades/upgrade_20260913_multi_storage.sql').read_text())
    assert data_dump() == before, 'Repeat migration changed fixture rows'
    report['repeat_migration'] = {'passed': True, 'ordered_data_sha256': hashlib.sha256(before).hexdigest()}
    run(['docker','run','-d','--name',PROBE,'--network',NET,'-v',str(ROOT)+':/evidence',
         '-v',str(CAND)+':/rathena:ro','-w','/rathena',
         '--entrypoint','/evidence/storage-sql-probe',os.environ.get('PN_STORAGE_IMAGE','rathena:local'),'crash'],capture_output=True)
    for _ in range(40):
        sleeping = sql("SELECT COUNT(*) FROM information_schema.PROCESSLIST WHERE DB='storage_probe' AND STATE='User sleep'",False)
        if sleeping.returncode == 0 and sleeping.stdout.strip() == '1': break
        time.sleep(.25)
    else: raise RuntimeError('Crash probe did not reach the journal trigger')
    run(['docker','kill','--signal','KILL',DB],capture_output=True)
    exit_code = run(['docker','wait',PROBE],text=True,capture_output=True,timeout=15).stdout.strip()
    crash_log = run(['docker','logs',PROBE],text=True,capture_output=True)
    (ROOT/'sql-crash.log').write_text(crash_log.stdout+crash_log.stderr)
    assert exit_code == '0' and 'CRASH_RETURN 0' in crash_log.stdout
    run(['docker','start',DB],capture_output=True); ready()
    actual = sql("USE storage_probe; SELECT zeny FROM `char` WHERE char_id=99001313; SELECT SUM(amount) FROM inventory WHERE nameid=501; SELECT COUNT(*) FROM inventory; SELECT COUNT(*) FROM pn_storage_02; SELECT COUNT(*) FROM pn_storage_commits;").stdout.split()
    assert actual == ['2000000000','2','2','0','0'], actual
    report['real_database_crash'] = {'passed': True, 'kill_point': 'After source, page and wallet writes; before journal/COMMIT', 'recovered_wallet': int(actual[0]), 'source_rows': int(actual[2]), 'uncommitted_page_rows': 0, 'uncommitted_journal_rows': 0}
    report['passed'] = True
    print('Real MariaDB crash recovery passed.',flush=True)
finally:
    if created:
        subprocess.run(['docker','rm','-f','-v',PROBE,DB],capture_output=True)
        subprocess.run(['docker','network','rm',NET],capture_output=True)
    (ROOT/'sql-report.json').write_text(json.dumps(report,indent=2))
