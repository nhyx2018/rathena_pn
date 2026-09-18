"""Guarded production rollout of the scoped 285/65 server changes.

Apply leaves login admission closed. Open only after client installation passes.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time


LIVE = Path("/app/rathena")
CANDIDATE = Path("/app/rathena-builds/kro-285-20260917")
BACKUP = Path("/app/rathena-deploy-backups/kro-285-20260917-r2")
CLIENT_INSTALL_PROOF = CANDIDATE / "validation/client-install.json"
CLIENT_GRF_SHA256 = "c4e8767352df87f16ea2841b47a691e4b1a2891f4530d829fb1daf7b83c1606a"
FILES = (
    "src/map/map.hpp", "conf/battle/player.conf", "conf/battle/homunc.conf",
    "db/re/job_exp.yml", "db/re/job_stats.yml", "db/re/statpoint.yml",
    "db/re/exp_homun.yml", "db/re/job_basepoints.yml", "map-server",
)
BASELINE = {
    "src/map/map.hpp": "f4b3e9e40bc7e9ad6357855fe75176ef2c4b521cec61d9a21362a5826905fe34",
    "conf/battle/player.conf": "32e5e5cdb5c78c86cb0936759d3be6d5e5e973d6c8a1ccb7fba6b45f9e424e5c",
    "conf/battle/homunc.conf": "1e8bb115fcc30e9e018050b23a0fe60bd6c5913674397f54ef53c09fd7c55659",
    "db/re/job_exp.yml": "6cb91d2e37364fb0bb90e9bf4003f141605e48164544b693eb154f1d6f2e8a09",
    "db/re/job_stats.yml": "44df1b20a1d6412ad93bb18715361ddebd79af07551a0fb68e43bf2c49b8db8b",
    "db/re/statpoint.yml": "63d89dccba0026d37ade97aa6bfdf26137edc1982eef606392435042f94b8985",
    "db/re/exp_homun.yml": "386ac97674d9c63d471bdab73ca17fdf21e3a1814099666f9aa43ca4a385ec4f",
    "db/re/job_basepoints.yml": "25aa54807fa011a8e0e86236bfaacda2b3cc512d34f11fd1fa437ee251d22117",
    "map-server": "455ab58bc569c708783f04eccc2adce78c863286f8ce8577e4933c845997c825",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*cmd, check=True, timeout=120):
    return subprocess.run(cmd, capture_output=True, text=True, check=check, timeout=timeout)


def running(name):
    return run("docker", "inspect", "--format", "{{.State.Running}}", name).stdout.strip() == "true"


def online_count():
    result = run("docker", "exec", "rathena-db", "sh", "-c",
                 'MYSQL_PWD="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}" '
                 'exec mariadb -uroot --batch --raw -N ragnarok '
                 '-e "$1"', "sh", "SELECT COUNT(*) FROM `char` WHERE online<>0")
    return int(result.stdout.strip())


FIREWALL_RULE = ("DOCKER-USER", "-i", "ens18", "-p", "tcp", "--dport", "6900", "-j", "REJECT")


def admission_blocked():
    return all(rule_present(command) for command in ("iptables", "ip6tables"))


def rule_present(command):
    return run(command, "-C", *FIREWALL_RULE, check=False).returncode == 0


def block_admission():
    for command in ("iptables", "ip6tables"):
        if not rule_present(command):
            run(command, "-I", *FIREWALL_RULE)
    if not admission_blocked():
        raise RuntimeError("External login admission could not be blocked for IPv4 and IPv6")


def reopen_admission():
    removed = []
    try:
        for command in ("iptables", "ip6tables"):
            if rule_present(command):
                run(command, "-D", *FIREWALL_RULE)
                removed.append(command)
        if any(rule_present(command) for command in ("iptables", "ip6tables")):
            raise RuntimeError("External login admission remains partly blocked")
    except Exception:
        # Fail closed if one firewall family could not be reopened.
        for command in removed:
            if not rule_present(command):
                run(command, "-I", *FIREWALL_RULE)
        raise


def ensure_candidate():
    gate = json.loads((CANDIDATE / "validation/isolated-gate.json").read_text())
    if not gate["passed"] or gate["startup_errors"]:
        raise RuntimeError("Isolated production-built startup gate did not pass")
    if gate.get("map_server_sha256") != sha(CANDIDATE / "map-server"):
        raise RuntimeError("Validated map-server binary differs from candidate")
    manifest = json.loads((CANDIDATE / "candidate-overlay.json").read_text())
    wanted = set(FILES) - {"map-server"}
    by_name = {row["path"]: row["sha256"] for row in manifest["entries"]}
    if not wanted.issubset(by_name):
        raise RuntimeError("Candidate overlay lacks scoped source files")
    for name in wanted:
        if sha(CANDIDATE / name) != by_name[name]:
            raise RuntimeError(f"Candidate source drift: {name}")
    for name in FILES:
        if sha(LIVE / name) != BASELINE[name]:
            raise RuntimeError(f"Live drift: {name}")
    if not all(running(name) for name in
               ("rathena-login", "rathena-char", "rathena-map", "rathena-db")):
        raise RuntimeError("Expected live login/char/map/database containers")
    if online_count():
        raise RuntimeError("Players are online")
    if not admission_blocked():
        raise RuntimeError("External login admission is not blocked")
    return {name: sha(CANDIDATE / name) for name in FILES}


def compressed_backup(cmd, path, timeout=120):
    # Both children write to OS-managed pipes/files. Waiting on the dump can
    # therefore time out even when it stops producing output without exiting.
    compressor_code = (
        "import gzip,shutil,sys;"
        "out=gzip.GzipFile(fileobj=sys.stdout.buffer,mode='wb',compresslevel=6,mtime=0);"
        "shutil.copyfileobj(sys.stdin.buffer,out,1024*1024);out.close()"
    )
    dump = compressor = None
    try:
        with tempfile.TemporaryFile() as errors, path.open("wb") as output:
            compressor = subprocess.Popen(
                [sys.executable, "-c", compressor_code],
                stdin=subprocess.PIPE, stdout=output, stderr=errors)
            try:
                dump = subprocess.Popen(cmd, stdout=compressor.stdin, stderr=errors)
            finally:
                compressor.stdin.close()
            dump_status = dump.wait(timeout=timeout)
            compressor_status = compressor.wait(timeout=30)
            errors.seek(0)
            error = errors.read(300).decode(errors="replace")
        if dump_status or compressor_status or path.stat().st_size < 1024:
            raise RuntimeError(f"SQL backup failed: {error}")
    except Exception:
        for proc in (dump, compressor):
            if proc is not None and proc.poll() is None:
                proc.kill()
        for proc in (dump, compressor):
            if proc is not None:
                proc.wait(timeout=10)
        path.unlink(missing_ok=True)
        raise


def sql_backup(path):
    cmd = ["docker", "exec", "rathena-db", "sh", "-c",
           'MYSQL_PWD="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}" '
           'exec mariadb-dump -uroot --single-transaction --routines --triggers ragnarok']
    compressed_backup(cmd, path)
    path.chmod(0o600)
    return sha(path)


def copy_atomic(source, dest):
    temp = dest.with_name(dest.name + ".kro285-new")
    if temp.exists():
        raise RuntimeError(f"Stale deployment temp file: {temp}")
    shutil.copy2(source, temp)
    os.replace(temp, dest)


def wait_map(since):
    for _ in range(90):
        if not running("rathena-map"):
            raise RuntimeError("Map container exited")
        raw = run("docker", "logs", "--since", since, "rathena-map", check=False).stdout
        raw += run("docker", "logs", "--since", since, "rathena-map", check=False).stderr
        log = re.sub(r"\x1b\[[0-9;]*[mK]", "", raw)
        if "[Error]" in log or "[Fatal" in log:
            raise RuntimeError("Map startup logged an error")
        if "Map Server is now online" in log:
            return log
        time.sleep(1)
    raise RuntimeError("Map readiness marker missing")


def restore():
    if not admission_blocked():
        raise RuntimeError("Block both login firewall families before restoring files")
    if online_count():
        raise RuntimeError("Players appeared before rollback")
    # Check every rollback source before stopping the map service or replacing anything.
    for name in FILES:
        source = BACKUP / "files" / name
        if sha(source) != BASELINE[name]:
            raise RuntimeError(f"Backup checksum mismatch: {name}")
    if running("rathena-map"):
        run("docker", "stop", "-t", "30", "rathena-map", timeout=50)
    for name in FILES:
        source = BACKUP / "files" / name
        copy_atomic(source, LIVE / name)
    since = datetime.now(timezone.utc).isoformat()
    run("docker", "start", "rathena-map")
    (BACKUP / "rollback-startup.log").write_text(wait_map(since))
    reopen_admission()


def over_old_cap_count():
    query = ("SELECT "
             "(SELECT COUNT(*) FROM `char` WHERE base_level>275 OR job_level>60) + "
             "(SELECT COUNT(*) FROM homunculus WHERE level>275)")
    result = run("docker", "exec", "rathena-db", "sh", "-c",
                 'MYSQL_PWD="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}" '
                 'exec mariadb -uroot --batch --raw -N ragnarok -e "$1"',
                 "sh", query)
    return int(result.stdout.strip())


def prepare_backup(after):
    pending = BACKUP.with_name(BACKUP.name + ".preparing")
    if BACKUP.exists() or pending.exists():
        raise RuntimeError("Backup target already exists; inspect it before retrying")
    pending.mkdir(mode=0o700)
    try:
        (pending / "files").mkdir(mode=0o700)
        for name in FILES:
            dest = pending / "files" / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(LIVE / name, dest)
            if sha(dest) != BASELINE[name]:
                raise RuntimeError(f"Backup copy mismatch: {name}")
        sql_digest = sql_backup(pending / "ragnarok-before.sql.gz")
        receipt = {"applied": False, "admission_closed": True,
                   "baseline": BASELINE, "candidate": after,
                   "sql_backup_sha256": sql_digest}
        (pending / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        os.replace(pending, BACKUP)
        return receipt
    except Exception:
        shutil.rmtree(pending)
        raise


def apply():
    after = ensure_candidate()
    receipt = None
    try:
        receipt = prepare_backup(after)
        if online_count():
            raise RuntimeError("Players appeared after admission closed")
        run("docker", "stop", "-t", "30", "rathena-map", timeout=50)
        installed = {}
        for name in FILES:
            copy_atomic(CANDIDATE / name, LIVE / name)
            installed[name] = sha(LIVE / name)
            if installed[name] != after[name]:
                raise RuntimeError(f"Installed checksum mismatch: {name}")
        since = datetime.now(timezone.utc).isoformat()
        run("docker", "start", "rathena-map")
        (BACKUP / "live-startup.log").write_text(wait_map(since))
        receipt["applied"] = True
        receipt["installed"] = installed
        (BACKUP / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        print("APPLIED: map ready; external login admission remains blocked")
    except Exception:
        if receipt is not None:
            restore()
            receipt["rolled_back"] = True
            (BACKUP / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        else:
            # No production file has changed yet; undo the maintenance block.
            reopen_admission()
        raise


def open_login():
    receipt = json.loads((BACKUP / "receipt.json").read_text())
    if not receipt["applied"] or not receipt["admission_closed"]:
        raise RuntimeError("No pending applied release")
    proof = json.loads(CLIENT_INSTALL_PROOF.read_text())
    if not proof.get("installed") or proof.get("new_sha256") != CLIENT_GRF_SHA256:
        raise RuntimeError("Matching client installation proof is missing")
    if (not running("rathena-login") or not running("rathena-char") or
            not running("rathena-map") or online_count() or not admission_blocked()):
        raise RuntimeError("Unexpected admission/map/player state")
    for name in FILES:
        if sha(LIVE / name) != receipt["candidate"][name]:
            raise RuntimeError(f"Post-install drift: {name}")
    reopen_admission()
    receipt["admission_closed"] = False
    receipt["completed"] = True
    (BACKUP / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print("COMPLETE: login admission reopened")


def rollback():
    if not BACKUP.is_dir():
        raise RuntimeError("Rollback backup does not exist")
    was_blocked = admission_blocked()
    block_admission()
    try:
        if online_count() or over_old_cap_count():
            raise RuntimeError("Rollback requires zero online players and no levels above 275/60/275")
    except Exception:
        if not was_blocked:
            reopen_admission()
        raise
    restore()
    receipt = json.loads((BACKUP / "receipt.json").read_text())
    receipt.update(applied=False, admission_closed=False, completed=False,
                   rolled_back=True, installed=BASELINE)
    (BACKUP / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("apply", "open", "rollback"))
    mode = parser.parse_args().mode
    if mode == "apply":
        apply()
    elif mode == "open":
        open_login()
    else:
        rollback()
