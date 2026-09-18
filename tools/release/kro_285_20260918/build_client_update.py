"""Build and verify the portable 285/65 client update from pinned inputs."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile


HERE = Path(__file__).resolve().parent
PACKAGES = Path(os.environ["PN_CLIENT_PACKAGES_ROOT"]).resolve() if os.environ.get(
    "PN_CLIENT_PACKAGES_ROOT") else HERE.parent
CLEAN = PACKAGES / "improvement-pass-20260914" / "PN-Client-Clean"
LEVEL = PACKAGES / "kro-285-20260917"
OUTPUT = PACKAGES / "remediation-20260918" / "PN-Client-Update-20260918-LevelCap-285-65-Verified.zip"
REPORT = PACKAGES / "remediation-20260918" / "client-package-verified.json"

# Reviewed inputs. Changing a pin requires a new release review.
BASELINE_MANIFEST_SHA256 = "1bf20666650402a6fa904359baa361185a7ffe845eb46bbc82eba45c28c815bd"
BASELINE_RELEASE_SHA256 = "804ef2ea9e855070e8781e26fbe0281a97126ee02e126970ab63b87ba59fd14a"
GRF_SHA256 = "c4e8767352df87f16ea2841b47a691e4b1a2891f4530d829fb1daf7b83c1606a"
RELEASE_SHA256 = "2a66690c520d80fb804399e376d4930700dabdac91e8e62a4264a30164b2de8b"
PACKAGE_SHA256 = "adbf0be5a2a953a64bb4ddfd00d9c6890f7663676fc4197bba1fd2411a9837d7"
MANIFEST_COUNT = 5621
ZIP_TIME = (2026, 9, 18, 0, 0, 0)
ZIP_MEMBERS = (
    "PN-Client/client_repairs.grf",
    "PN-Client/RELEASE.json",
    "PN-Client/client-manifest.json",
    "PN-Client/UPDATE-20260918.txt",
)
README = """PN CLIENT LEVEL CAP UPDATE - 18 SEPTEMBER 2026

This update changes the fourth/expanded fourth class display cap to Base 285 / Job 65.
It applies to the clean September 14 PN client or a client already updated through
that release, with client_repairs.grf in DATA.INI slot 0.

Close Ragnarok and back up client_repairs.grf, RELEASE.json, and
client-manifest.json. Open this ZIP's PN-Client folder and copy its CONTENTS
into your installed PN-Client folder, replacing matching files. Alternatively,
extract the ZIP beside the installed PN-Client folder and merge it there.
Run Check Client, then Verify Client.

This archive includes all prior client repair resources. It does not add
the August 2026 kRO class skills or other unrelated content.
"""


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_pinned(path, expected):
    data = path.read_bytes()
    if digest(data) != expected:
        raise RuntimeError(f"Reviewed input changed: {path.name}")
    return data


def validate_rows(rows):
    if not isinstance(rows, list) or len(rows) != MANIFEST_COUNT:
        raise RuntimeError("Unexpected clean baseline manifest length")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"path", "bytes", "sha256"}:
            raise RuntimeError("Invalid manifest row")
        name = row["path"]
        if (not isinstance(name, str) or not name or "\\" in name or ":" in name or
                name.startswith("/") or
                any(part in ("", ".", "..") for part in name.split("/"))):
            raise RuntimeError(f"Unsafe manifest path: {name!r}")
        if name.casefold() in seen:
            raise RuntimeError(f"Duplicate manifest path: {name}")
        seen.add(name.casefold())
        if re.match(r"(?i)^AI/USER_AI/data/H_", name):
            raise RuntimeError(f"Personal AI state in baseline: {name}")
        if (type(row["bytes"]) is not int or row["bytes"] < 0 or
                not isinstance(row["sha256"], str) or
                not re.fullmatch(r"[0-9a-f]{64}", row["sha256"])):
            raise RuntimeError(f"Invalid manifest digest or size: {name}")
    for name in ("client_repairs.grf", "RELEASE.json"):
        if sum(row["path"] == name for row in rows) != 1:
            raise RuntimeError(f"Baseline has no unique {name} row")


def release_bytes(clean_release):
    release = json.loads(clean_release)
    if release.get("release_id") != "client-20260914-rewards-items":
        raise RuntimeError("Unexpected baseline release")
    release["release_id"] = "client-20260917-level-285-65"
    release["verification"] = (
        "merged GRF resource preservation, three effective 285/65 level tables, "
        "local client validation; rendered gameplay remains partial"
    )
    release["fixes"] = list(release.get("fixes", [])) + [
        "fourth and expanded fourth class Base 285 / Job 65 level display"
    ]
    # Preserve the reviewed installed release's Windows newlines.
    data = (json.dumps(release, indent=2) + "\n").encode("utf-8").replace(b"\n", b"\r\n")
    if digest(data) != RELEASE_SHA256:
        raise RuntimeError("Generated release metadata differs from reviewed release")
    return data


def expected_members():
    baseline = read_pinned(CLEAN / "client-manifest.json", BASELINE_MANIFEST_SHA256)
    clean_release = read_pinned(CLEAN / "RELEASE.json", BASELINE_RELEASE_SHA256)
    rows = json.loads(baseline)
    validate_rows(rows)
    replacement = {
        "client_repairs.grf": read_pinned(LEVEL / "client_repairs_285.grf", GRF_SHA256),
        "RELEASE.json": release_bytes(clean_release),
    }
    for row in rows:
        if row["path"] in replacement:
            data = replacement[row["path"]]
            row.update(bytes=len(data), sha256=digest(data))
    manifest = (json.dumps(rows, indent=2) + "\n").encode("utf-8")
    return {
        ZIP_MEMBERS[0]: replacement["client_repairs.grf"],
        ZIP_MEMBERS[1]: replacement["RELEASE.json"],
        ZIP_MEMBERS[2]: manifest,
        ZIP_MEMBERS[3]: README.encode("utf-8"),
    }


def verify_archive(path, members):
    with zipfile.ZipFile(path) as archive:
        if archive.namelist() != list(ZIP_MEMBERS) or archive.testzip() is not None:
            raise RuntimeError("Unexpected ZIP members or CRC failure")
        for name, data in members.items():
            info = archive.getinfo(name)
            if info.date_time != ZIP_TIME or info.file_size != len(data):
                raise RuntimeError(f"ZIP member metadata changed: {name}")
            if archive.read(name) != data:
                raise RuntimeError(f"ZIP member content changed: {name}")
    if digest(path.read_bytes()) != PACKAGE_SHA256:
        raise RuntimeError("ZIP bytes differ from reviewed deterministic package")


def smoke_client(path):
    """Run the real client level-table checker against the ZIP's GRF payload."""
    rows = json.loads((CLEAN / "client-manifest.json").read_bytes())
    data_ini_row = next(row for row in rows if row["path"] == "DATA.INI")
    data_ini = read_pinned(CLEAN / "DATA.INI", data_ini_row["sha256"])
    checker = PACKAGES.parent / "Data/server-work/rathena_pn_push/client-patch/level_cap_285/build_grf.py"
    with tempfile.TemporaryDirectory(prefix="pn-client-smoke-") as temp:
        stage = Path(temp)
        (stage / "DATA.INI").write_bytes(data_ini)
        with zipfile.ZipFile(path) as archive:
            (stage / "client_repairs.grf").write_bytes(archive.read(ZIP_MEMBERS[0]))
        result = subprocess.run(
            [sys.executable, str(checker), "--client", str(stage), "--check"],
            capture_output=True, text=True, timeout=60, check=False)
        if result.returncode or result.stdout.count("-> 285/65") != 3:
            raise RuntimeError(f"Staged client level-table smoke failed: {result.stderr or result.stdout}")


def receipt(output, members):
    return {
        "package": output.name,
        "sha256": digest(output.read_bytes()),
        "bytes": output.stat().st_size,
        "manifest_entries": MANIFEST_COUNT,
        "manifest_sha256": digest(members[ZIP_MEMBERS[2]]),
        "client_grf_sha256": GRF_SHA256,
        "release_sha256": RELEASE_SHA256,
        "baseline_manifest_sha256": BASELINE_MANIFEST_SHA256,
        "baseline_release_sha256": BASELINE_RELEASE_SHA256,
    }


def build(output=OUTPUT, report_path=REPORT):
    members = expected_members()
    if output.exists():
        verify_archive(output, members)
        smoke_client(output)
    else:
        fd, temp_name = tempfile.mkstemp(prefix=output.name + ".", suffix=".tmp", dir=output.parent)
        os.close(fd)
        temp = Path(temp_name)
        try:
            with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED,
                                 compresslevel=9, allowZip64=True) as archive:
                for name in ZIP_MEMBERS:
                    info = zipfile.ZipInfo(name, ZIP_TIME)
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.create_system = 3
                    info.external_attr = 0o100644 << 16
                    archive.writestr(info, members[name], compress_type=zipfile.ZIP_DEFLATED,
                                     compresslevel=9)
            verify_archive(temp, members)
            smoke_client(temp)
            os.replace(temp, output)
        finally:
            temp.unlink(missing_ok=True)
    result = receipt(output, members)
    report_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    return result


def check(output=OUTPUT, report_path=REPORT):
    members = expected_members()
    verify_archive(output, members)
    smoke_client(output)
    result = receipt(output, members)
    if json.loads(report_path.read_text(encoding="utf-8")) != result:
        raise RuntimeError("Client package receipt differs from verified ZIP")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Verify the existing ZIP and receipt")
    args = parser.parse_args()
    print(json.dumps(check() if args.check else build(), indent=2))
