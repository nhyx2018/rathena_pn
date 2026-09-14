"""Run the shipping PowerShell verifier on complete, damaged and invalid installations."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[2]/'client-patch/client_usability/tools/client/verify-client.ps1'


@unittest.skipUnless(sys.platform == 'win32', 'Native Windows PowerShell is required')
class ManifestTests(unittest.TestCase):
    def run_case(self, entries, files, expected):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, value in files.items():
                target=root/name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(value)
            (root/'client-manifest.json').write_text(json.dumps(entries), encoding='utf-8')
            result = subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(SCRIPT),'-ClientRoot',str(root)], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, expected, result.stdout+result.stderr)

    def entry(self, name, data=b'expected'):
        return {'path':name, 'bytes':len(data), 'sha256':hashlib.sha256(data).hexdigest()}

    def test_fresh_install_and_extra_player_files(self):
        self.run_case([self.entry('SystemEN/itemInfo.lua')], {'SystemEN/itemInfo.lua':b'expected','ScreenShot/picture.png':b'player file'}, 0)

    def test_multiple_files_are_verified_individually(self):
        rows = [self.entry('BankUI.dll'),self.entry('SystemEN/itemInfo.lua',b'second file')]
        self.run_case(rows, {'BankUI.dll':b'expected','SystemEN/itemInfo.lua':b'second file'}, 0)
        self.run_case(rows, {'BankUI.dll':b'expected','SystemEN/itemInfo.lua':b'wrong value'}, 1)

    def test_damaged_missing_and_old_patch(self):
        for files in ({}, {'BankUI.dll':b'bad'}, {'BankUI.dll':b'obsolete'}):
            self.run_case([self.entry('BankUI.dll')], files, 1)

    def test_new_patch_matches_new_manifest(self):
        self.run_case([self.entry('BankUI.dll',b'patched')], {'BankUI.dll':b'patched'}, 0)

    def test_rejects_empty_duplicate_and_escaping_paths(self):
        for entries in ([], [self.entry('../outside')], [self.entry('C:/outside')],
                        [self.entry('data/file'), self.entry('DATA/FILE')],
                        [{'path':'safe', 'bytes':1, 'sha256':'invalid'}]):
            self.run_case(entries, {}, 1)


if __name__ == '__main__':
    unittest.main()
