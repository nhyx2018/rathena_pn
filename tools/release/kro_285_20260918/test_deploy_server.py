"""Offline safety regressions for the 285/65 deployment controller."""

import importlib.util
import gzip
import json
from pathlib import Path
import random
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location(
    "deploy_server", Path(__file__).with_name("deploy_server.py"))
deploy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(deploy)


class DeploymentSafetyTests(unittest.TestCase):
    def test_sql_backup_stream_has_bounded_wait_and_cleans_partial_file(self):
        with TemporaryDirectory() as temp:
            output = Path(temp) / "backup.sql.gz"
            with self.assertRaises(subprocess.TimeoutExpired):
                deploy.compressed_backup(
                    [sys.executable, "-c", "import time; time.sleep(10)"],
                    output, timeout=0.2)
            self.assertFalse(output.exists())

    def test_sql_backup_stream_preserves_content(self):
        with TemporaryDirectory() as temp:
            output = Path(temp) / "backup.sql.gz"
            source = random.Random(1).randbytes(8192)
            deploy.compressed_backup(
                [sys.executable, "-c",
                 "import random,sys;sys.stdout.buffer.write(random.Random(1).randbytes(8192))"],
                output, timeout=5)
            self.assertEqual(gzip.decompress(output.read_bytes()), source)

    def test_firewall_reopen_compensates_second_family_failure(self):
        present = {"iptables": True, "ip6tables": True}

        def fake_run(command, operation, *args, **kwargs):
            if operation == "-C":
                return type("Result", (), {"returncode": 0 if present[command] else 1})()
            if command == "ip6tables" and operation == "-D":
                raise RuntimeError("IPv6 rule deletion failed")
            present[command] = operation == "-I"

        with patch.object(deploy, "run", side_effect=fake_run):
            with self.assertRaisesRegex(RuntimeError, "IPv6 rule deletion failed"):
                deploy.reopen_admission()
        self.assertEqual(present, {"iptables": True, "ip6tables": True})

    def test_restore_checks_admission_before_mutation(self):
        with patch.object(deploy, "admission_blocked", return_value=False), \
                patch.object(deploy, "copy_atomic") as copy:
            with self.assertRaisesRegex(RuntimeError, "Block both"):
                deploy.restore()
            copy.assert_not_called()

    def test_candidate_gate_rejects_unbound_binary(self):
        with TemporaryDirectory() as temp:
            candidate = Path(temp)
            (candidate / "validation").mkdir()
            (candidate / "map-server").write_bytes(b"candidate binary")
            (candidate / "validation/isolated-gate.json").write_text(json.dumps({
                "passed": True, "startup_errors": 0,
            }))
            with patch.object(deploy, "CANDIDATE", candidate):
                with self.assertRaisesRegex(RuntimeError, "Validated map-server binary differs"):
                    deploy.ensure_candidate()

    def test_failed_backup_preparation_removes_partial_directory(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            live, backup = root / "live", root / "backup"
            (live / "one.txt").parent.mkdir()
            (live / "one.txt").write_bytes(b"baseline")
            with patch.multiple(deploy, LIVE=live, BACKUP=backup,
                                FILES=("one.txt",), BASELINE={"one.txt": deploy.sha(live / "one.txt")}), \
                    patch.object(deploy, "sql_backup", side_effect=RuntimeError("SQL backup failed")):
                with self.assertRaisesRegex(RuntimeError, "SQL backup failed"):
                    deploy.prepare_backup({"one.txt": "candidate"})
            self.assertFalse(backup.exists())
            self.assertFalse(backup.with_name("backup.preparing").exists())

    def test_rollback_rejects_persisted_high_levels_and_reopens_unchanged_login(self):
        with TemporaryDirectory() as temp:
            with patch.object(deploy, "BACKUP", Path(temp)), \
                    patch.object(deploy, "admission_blocked", return_value=False), \
                    patch.object(deploy, "block_admission") as block, \
                    patch.object(deploy, "online_count", return_value=0), \
                    patch.object(deploy, "over_old_cap_count", return_value=1), \
                    patch.object(deploy, "reopen_admission") as reopen, \
                    patch.object(deploy, "restore") as restore:
                with self.assertRaisesRegex(RuntimeError, "levels above"):
                    deploy.rollback()
                block.assert_called_once()
                reopen.assert_called_once()
                restore.assert_not_called()

    def test_rollback_blocks_first_then_records_baseline(self):
        with TemporaryDirectory() as temp:
            backup = Path(temp)
            (backup / "receipt.json").write_text(json.dumps({
                "applied": True, "admission_closed": False, "completed": True}))
            events = []
            with patch.object(deploy, "BACKUP", backup), \
                    patch.object(deploy, "admission_blocked", return_value=False), \
                    patch.object(deploy, "block_admission", side_effect=lambda: events.append("block")), \
                    patch.object(deploy, "online_count", side_effect=lambda: events.append("online") or 0), \
                    patch.object(deploy, "over_old_cap_count", side_effect=lambda: events.append("levels") or 0), \
                    patch.object(deploy, "restore", side_effect=lambda: events.append("restore")):
                deploy.rollback()
            self.assertEqual(events, ["block", "online", "levels", "restore"])
            receipt = json.loads((backup / "receipt.json").read_text())
            self.assertFalse(receipt["applied"])
            self.assertFalse(receipt["completed"])
            self.assertTrue(receipt["rolled_back"])
            self.assertEqual(receipt["installed"], deploy.BASELINE)


if __name__ == "__main__":
    unittest.main()
