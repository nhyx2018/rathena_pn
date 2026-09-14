"""Behavioral checks for stale, failed, corrupt backups and stopped/erroring services."""
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('health', Path(__file__).resolve().parents[1]/'admin/health_check.py')
health = importlib.util.module_from_spec(spec); spec.loader.exec_module(health)


class HealthTests(unittest.TestCase):
    def backup(self, root, now, **overrides):
        path = root/('ragnarok-'+now.strftime('%Y%m%dT%H%M%S%fZ')+'.sql.json')
        archive = path.with_suffix('.gz'); archive.write_bytes(b'verified compressed backup fixture')
        data = {'created_utc': now.strftime('%Y%m%dT%H%M%S%fZ'), 'passed': True,
                'restore': {'passed': True}, 'archive_bytes': archive.stat().st_size,
                'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}
        data.update(overrides); path.write_text(json.dumps(data))
        return path

    def test_backup_integrity_and_expiration(self):
        now = datetime.now(timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertFalse(health.backup_status(root, now, 30)['passed'])
            path = self.backup(root, now-timedelta(hours=1))
            self.assertTrue(health.backup_status(root, now, 30)['passed'])
            self.assertFalse(health.backup_status(root, now+timedelta(hours=31), 30)['passed'])
            path.with_suffix('.gz').write_bytes(b'corrupt')
            self.assertFalse(health.backup_status(root, now, 30)['passed'])

    def test_new_failure_cannot_be_hidden_by_older_success(self):
        now = datetime.now(timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.backup(root, now-timedelta(hours=1))
            latest = self.backup(root, now, passed=False)
            self.assertFalse(health.backup_status(root, now, 30)['passed'])
            latest.write_text('{invalid')
            self.assertFalse(health.backup_status(root, now, 30)['passed'])

    def test_restore_failure_future_and_missing_archive(self):
        now = datetime.now(timezone.utc)
        for overrides in ({'restore': {'performed': False}}, {'archive_sha256': '0'*64}):
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); self.backup(root, now, **overrides)
                self.assertFalse(health.backup_status(root, now, 30)['passed'])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); path = self.backup(root, now+timedelta(hours=2))
            self.assertFalse(health.backup_status(root, now, 30)['passed'])
            path.with_suffix('.gz').unlink()
            self.assertFalse(health.backup_status(root, now+timedelta(hours=2), 30)['passed'])

    def test_service_states_and_recent_errors(self):
        for state, logs, expected in (
            ({'Running': True}, '[Info]: [SQL]: connected', True),
            ({'Running': False}, '', False),
            ({'Running': True, 'Paused': True}, '', False),
            ({'Running': True, 'Health': {'Status': 'unhealthy'}}, '', False),
            ({'Running': True}, '\x1b[31m[Error]: connection failed', False),
            ({'Running': True}, '[Warning]: Connection to Char Server lost.', False),
            ({'Running': True}, "[Warning]: Unable to resolve char-server 'fixture'; retrying later.", False),
            ({'Running': True}, '[SQL]: DB error - private content', False)):
            with patch.object(health, 'command', side_effect=[json.dumps(state), logs]):
                result = health.inspect_service('fixture', 15)
                self.assertEqual(result['passed'], expected)
                self.assertNotIn('private content', json.dumps(result))


if __name__ == '__main__':
    unittest.main()
