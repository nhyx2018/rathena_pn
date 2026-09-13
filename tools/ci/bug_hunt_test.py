"""A failing check must not hide later results or produce a passing report."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import bug_hunt


class BugHuntTests(unittest.TestCase):
    def test_failure_keeps_later_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / 'repo'
            ci = root / 'tools/ci'
            ci.mkdir(parents=True)
            (ci / 'fail.py').write_text('print("reproduced defect"); raise SystemExit(7)')
            (ci / 'pass.py').write_text('print("later check executed")')
            output = Path(folder) / 'evidence'
            stamp = {'git_commit': 'test', 'input_sha256': {}, 'server_binary_sha256': {}}
            with patch.object(bug_hunt, 'ROOT', root), patch.object(bug_hunt, 'SUITES', {'release': ['fail.py', 'pass.py']}), \
                 patch.object(bug_hunt, 'identity', return_value=stamp), \
                 patch.object(bug_hunt.sys, 'platform', 'linux'), \
                 patch.object(bug_hunt.sys, 'argv', ['bug_hunt', '--output', str(output)]):
                self.assertEqual(bug_hunt.main(), 1)
            report = json.loads((output / 'report.json').read_text())
            self.assertEqual([r['status'] for r in report['checks']], ['failed', 'passed'])
            self.assertEqual(report['checks'][0]['exit_code'], 7)
            self.assertFalse(report['offline_checks_passed'])
            self.assertFalse(report['acceptance_complete'])
            self.assertIn('later check executed', (output / 'logs/pass.log').read_text())


if __name__ == '__main__':
    unittest.main()
