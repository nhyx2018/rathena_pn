"""Install the tested bank extension with byte backups and a rollback receipt."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
ORIGINAL='ca4820f0a86c06cf2cea7fc4173ae3f6fd1b362cab9dcfa703c8319891510d82'

def digest(data): return hashlib.sha256(data).hexdigest()
def atomic(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    staged=path.with_name(path.name+'.pn-bank-new')
    with staged.open('xb') as stream: stream.write(data)
    os.replace(staged,path)

def idle():
    check=subprocess.run(['powershell.exe','-NoProfile','-Command',
        "if (Get-Process Ragexe -ErrorAction SilentlyContinue) { exit 1 }"],capture_output=True)
    if check.returncode: raise RuntimeError('Close Ragexe before replacing its loaded extensions.')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client-root',type=Path,required=True)
    parser.add_argument('--build',type=Path)
    parser.add_argument('--backup',type=Path,required=True)
    parser.add_argument('--rollback',action='store_true')
    args=parser.parse_args();root=args.client_root.resolve();backup=args.backup.resolve()
    idle()
    if args.rollback:
        receipt=json.loads((backup/'receipt.json').read_text())
        assert receipt['client_root']==str(root)
        for name,row in receipt['files'].items():
            assert digest((root/name).read_bytes())==row['after'],f'File changed since install: {name}'
        for name,row in receipt['files'].items():
            if row['before'] is None: (root/name).unlink()
            else: atomic(root/name,(backup/name).read_bytes())
        receipt['rolled_back']=True
        (backup/'receipt.json').write_text(json.dumps(receipt,indent=2))
        print('Restored original client files.');return
    assert args.build and (root/'Ragexe.exe').is_file()
    original=root/('FontScaleOriginal.dll' if (root/'FontScaleOriginal.dll').is_file() else 'FontScale.dll')
    assert digest(original.read_bytes())==ORIGINAL,'This installer requires the verified PN font extension.'
    files={'FontScaleOriginal.dll':original.read_bytes(),
        'FontScale.dll':(args.build/'FontScale.dll').read_bytes(),
        'BankUI.dll':(args.build/'BankUI.dll').read_bytes(),
        'BankUI.ini':(HERE/'BankUI.ini').read_bytes(),
        'BankUI-LICENSE.txt':(HERE/'vendor/MinHook/LICENSE.txt').read_bytes(),
        'SystemEN/AccountBankInfo.lua':(REPO/'client-patch/client_compat/SystemEN/AccountBankInfo.lua').read_bytes(),
        'tools/client/start-client.ps1':(REPO/'client-patch/client_usability/tools/client/start-client.ps1').read_bytes()}
    loader=(root/'SystemEN/itemInfo.lua').read_bytes()
    if b'dofile("SystemEN/AccountBankInfo.lua")' not in loader:
        newline=b'\r\n' if b'\r\n' in loader else b'\n'
        loader=loader.rstrip(b'\r\n')+newline+b'dofile("SystemEN/AccountBankInfo.lua")'+newline
    files['SystemEN/itemInfo.lua']=loader
    for name in ('FontScale.dll','BankUI.dll'):
        data=files[name];offset=struct.unpack_from('<I',data,60)[0]
        assert data[:2]==b'MZ' and data[offset:offset+4]==b'PE\0\0' and struct.unpack_from('<H',data,offset+4)[0]==0x14c
    backup.mkdir(parents=True,exist_ok=False)
    unchanged={name:digest((root/name).read_bytes()) for name in ('Ragexe.exe','FontScale.ini','DATA.INI')}
    receipt={'client_root':str(root),'installed':False,'files':{},'preserved':unchanged}
    for name,data in files.items():
        prior=(root/name).read_bytes() if (root/name).is_file() else None
        if prior is not None:
            saved=backup/name;saved.parent.mkdir(parents=True,exist_ok=True);saved.write_bytes(prior)
        receipt['files'][name]={'before':digest(prior) if prior is not None else None,'after':digest(data)}
    (backup/'receipt.json').write_text(json.dumps(receipt,indent=2))
    written=[]
    try:
        for name,data in files.items(): atomic(root/name,data);written.append(name)
        for name,data in files.items(): assert (root/name).read_bytes()==data
        assert all(digest((root/name).read_bytes())==value for name,value in unchanged.items())
        subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',
            str(root/'tools/client/start-client.ps1'),'-CheckOnly','-ClientRoot',str(root)],check=True)
        receipt['installed']=True
    except Exception:
        for name in reversed(written):
            if receipt['files'][name]['before'] is None: (root/name).unlink()
            else: atomic(root/name,(backup/name).read_bytes())
        receipt['automatic_rollback']=True
        raise
    finally: (backup/'receipt.json').write_text(json.dumps(receipt,indent=2))
    print('Installed account bank; original client executable, font settings and archives preserved.')

if __name__=='__main__': main()
