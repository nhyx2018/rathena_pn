"""Offline release integrity checks for the portable client ZIP."""

import importlib.util
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import zipfile


SPEC = importlib.util.spec_from_file_location(
    "build_client_update", Path(__file__).with_name("build_client_update.py"))
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class ClientUpdateTests(unittest.TestCase):
    def test_package_matches_reviewed_payloads_and_check_gate(self):
        with zipfile.ZipFile(builder.OUTPUT) as current, zipfile.ZipFile(
                builder.PACKAGES / "remediation-20260918" /
                "PN-Client-Update-20260918-LevelCap-285-65-Fixed.zip") as prior:
            for name in builder.ZIP_MEMBERS[:3]:
                self.assertEqual(current.read(name), prior.read(name), name)
        self.assertEqual(builder.check()["sha256"], builder.PACKAGE_SHA256)

    def test_rebuild_is_byte_identical(self):
        with TemporaryDirectory() as temp:
            first, second = (Path(temp) / name for name in ("first.zip", "second.zip"))
            builder.build(first, Path(temp) / "first.json")
            builder.build(second, Path(temp) / "second.json")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(builder.digest(first.read_bytes()), builder.PACKAGE_SHA256)

    def test_changed_clean_manifest_is_rejected_before_output(self):
        with TemporaryDirectory() as temp:
            clean = Path(temp) / "clean"
            clean.mkdir()
            rows = json.loads((builder.CLEAN / "client-manifest.json").read_text())
            rows[0]["bytes"] += 1
            (clean / "client-manifest.json").write_text(json.dumps(rows))
            shutil.copy2(builder.CLEAN / "RELEASE.json", clean / "RELEASE.json")
            output = Path(temp) / "bad.zip"
            with patch.object(builder, "CLEAN", clean):
                with self.assertRaisesRegex(RuntimeError, "Reviewed input changed"):
                    builder.build(output, Path(temp) / "bad.json")
            self.assertFalse(output.exists())

    def test_personal_state_and_path_escape_are_rejected(self):
        original = json.loads((builder.CLEAN / "client-manifest.json").read_text())
        for bad in ("AI/USER_AI/data/H_personal.lua", "../outside.txt", "C:/outside.txt"):
            with self.subTest(bad=bad):
                rows = [dict(row) for row in original]
                rows[0]["path"] = bad
                with self.assertRaisesRegex(RuntimeError, "Personal AI|Unsafe manifest"):
                    builder.validate_rows(rows)

    def test_tampered_receipt_is_rejected(self):
        with TemporaryDirectory() as temp:
            output, report = Path(temp) / "package.zip", Path(temp) / "receipt.json"
            builder.build(output, report)
            data = json.loads(report.read_text())
            data["sha256"] = "0" * 64
            report.write_text(json.dumps(data))
            with self.assertRaisesRegex(RuntimeError, "receipt differs"):
                builder.check(output, report)


if __name__ == "__main__":
    unittest.main()
