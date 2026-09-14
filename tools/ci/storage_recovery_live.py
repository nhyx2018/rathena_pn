"""Populate every personal storage page, then restore a complete fixture backup.

Runs the real multi-storage protocol suite first. Never restores production.
"""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import yaml
import multi_storage_live_client as storage


def main():
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured): storage.main()
    protocol = json.loads(captured.getvalue())
    assert protocol['passed'] and not protocol['production_data_used']
    root = Path(os.environ['BANK_FIXTURE_ROOT'])
    repo = Path(__file__).resolve().parents[2]
    assert storage.sql('SELECT COUNT(*) FROM `char` WHERE online<>0') == '0'
    pages = yaml.safe_load((repo/'conf/pn_storage.yml').read_text())['Body']
    assert len(pages) == 18
    coverage = []
    for page in pages:
        table, page_id = page['Table'], page['ID']
        assert table == 'storage' or table.startswith('pn_')
        owner = 'char_id' if page_id == 117 else 'account_id'
        owner_id = storage.CID if page_id == 117 else storage.AID
        # These are additional synthetic records after genuine protocol transfers.
        # Full item metadata is intentional, including wide unsigned unique IDs.
        item = 4001 if page_id == 116 else 1202
        bound = 4 if page_id == 117 else 0
        storage.sql(f"INSERT INTO `{table}`({owner},nameid,amount,identify,refine,bound,unique_id,card0,option_id0,option_val0,option_parm0,enchantgrade) VALUES({owner_id},{item},1,1,12,{bound},{18446744073709551000+page_id},4002,1,37,3,2)")
        storage.sql(f"REPLACE INTO acc_reg_num(account_id,`key`,`index`,value) VALUES({storage.AID},'#PNStoragePaid',{page_id},1)")
        storage.sql(f"REPLACE INTO acc_reg_str(account_id,`key`,`index`,value) VALUES({storage.AID},'#PNStorageName$',{page_id},'Recovered Page {page_id}')")
        count = int(storage.sql(f'SELECT COUNT(*) FROM `{table}`'))
        coverage.append({'page':page_id,'table':table,'owner':owner,'rows':count})
    storage.sql(f"REPLACE INTO acc_reg_num(account_id,`key`,`index`,value) VALUES({storage.AID},'#BANKVAULT',0,9223372036854775000)")
    output=root/'backup-recovery'
    completed=subprocess.run([sys.executable,str(repo/'tools/admin/database_backup.py'),'--container',storage.DB,'--database','bank_runtime','--output',str(output),'--check-restore'],text=True,capture_output=True)
    (root/'backup-recovery.log').write_text(completed.stdout+completed.stderr)
    completed.check_returncode()
    backup=json.loads(completed.stdout)
    assert backup['passed'] and backup['restore']['passed']
    assert backup['sql_sha256']==backup['restore']['restored_sql_sha256']
    result={'passed':True,'production_data_used':False,'storage_protocol_scenarios':protocol['scenarios'],
            'restored_pages':coverage,'backup':backup,
            'coverage':['all 18 personal pages','account and character ownership','paid-page entitlements','page names',
                        'signed 64-bit bank balance','unsigned 64-bit item identity','refine/cards/options/grade/binding',
                        'inventory/cart and completed storage journals from real protocol operations'],
            'boundary':'Synthetic data and process/database recovery; not physical host power loss'}
    print(json.dumps(result,indent=2))


if __name__=='__main__': main()
