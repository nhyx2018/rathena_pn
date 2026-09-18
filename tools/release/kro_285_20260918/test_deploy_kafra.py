"""Offline file and rollback checks; no Docker or firewall command runs."""

import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location("deploy_kafra", Path(__file__).with_name("deploy_kafra.py"))
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)


class KafraDeploymentTests(unittest.TestCase):
    def test_partial_firewall_block_restores_initial_state(self):
        present = set()
        events = []

        def command(name, action, *args):
            events.append((name, action))
            if name == "ip6tables" and action == "-I":
                raise RuntimeError("IPv6 insertion failed")
            if action == "-I":
                present.add(name)
            elif action == "-D":
                present.remove(name)

        with patch.object(deploy, "rule_present", side_effect=lambda name: name in present), \
                patch.object(deploy, "run", side_effect=command):
            with self.assertRaisesRegex(RuntimeError, "IPv6 insertion failed"):
                deploy.block_login()
        self.assertEqual(present, set())
        self.assertEqual(events[-1], ("iptables", "-D"))

    def fixture(self, root):
        root = Path(root)
        live, candidate, backup = (root / name for name in ("live", "candidate", "backup"))
        old = live / deploy.NAME
        new = candidate / "candidate" / deploy.NAME
        old.parent.mkdir(parents=True)
        new.parent.mkdir(parents=True)
        old.write_bytes(b"old script")
        new.write_bytes(b"new script")
        (candidate / "manifest.json").write_text(json.dumps({
            "path": deploy.NAME, "before_sha256": deploy.sha(old),
            "after_sha256": deploy.sha(new),
        }))
        return live, candidate, backup, old, new

    def test_success_keeps_verified_backup_and_installed_hash(self):
        with TemporaryDirectory() as temp:
            live, candidate, backup, old, new = self.fixture(temp)
            events = []
            with patch.multiple(deploy, LIVE=live, CANDIDATE=candidate, BACKUP=backup), \
                    patch.object(deploy, "running", return_value=True), \
                    patch.object(deploy, "online_count", return_value=0), \
                    patch.object(deploy, "block_login", side_effect=lambda: events.append("block")), \
                    patch.object(deploy, "open_login", side_effect=lambda: events.append("open")), \
                    patch.object(deploy, "run"), \
                    patch.object(deploy, "start_map", return_value="Map Server is now online"):
                deploy.deploy()
            self.assertEqual(old.read_bytes(), new.read_bytes())
            self.assertEqual((backup / deploy.NAME).read_bytes(), b"old script")
            self.assertEqual(events, ["block", "open"])
            self.assertFalse(json.loads((backup / "receipt.json").read_text())["admission_closed"])

    def test_startup_failure_restores_original_before_reopening(self):
        with TemporaryDirectory() as temp:
            live, candidate, backup, old, new = self.fixture(temp)
            events = []
            attempts = iter((RuntimeError("new startup failed"), "Map Server is now online"))

            def startup():
                result = next(attempts)
                if isinstance(result, Exception):
                    raise result
                return result

            with patch.multiple(deploy, LIVE=live, CANDIDATE=candidate, BACKUP=backup), \
                    patch.object(deploy, "running", return_value=True), \
                    patch.object(deploy, "online_count", return_value=0), \
                    patch.object(deploy, "block_login", side_effect=lambda: events.append("block")), \
                    patch.object(deploy, "open_login", side_effect=lambda: events.append("open")), \
                    patch.object(deploy, "run"), \
                    patch.object(deploy, "start_map", side_effect=startup):
                with self.assertRaisesRegex(RuntimeError, "new startup failed"):
                    deploy.deploy()
            self.assertEqual(old.read_bytes(), b"old script")
            self.assertEqual(events, ["block", "open"])


if __name__ == "__main__":
    unittest.main()
