"""Guarded, one-file production rollout for the Kafra lottery correction.

Stage this directory at /app/rathena-builds/kafra-lottery-20260918, then run
`python3 deploy_kafra.py` on the server. It does not deploy from this workstation.
"""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time


LIVE = Path("/app/rathena")
CANDIDATE = Path("/app/rathena-builds/kafra-lottery-20260918")
BACKUP = Path("/app/rathena-deploy-backups/kafra-lottery-20260918")
NAME = "npc/cities/aldebaran.txt"
RULE = ("DOCKER-USER", "-i", "ens18", "-p", "tcp", "--dport", "6900", "-j", "REJECT")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*args, check=True, timeout=120):
    return subprocess.run(args, capture_output=True, text=True, check=check, timeout=timeout)


def rule_present(command):
    return run(command, "-C", *RULE, check=False).returncode == 0


def block_login():
    if any(rule_present(command) for command in ("iptables", "ip6tables")):
        raise RuntimeError("An existing login firewall rule needs operator review")
    added = []
    try:
        for command in ("iptables", "ip6tables"):
            run(command, "-I", *RULE)
            added.append(command)
        if not all(rule_present(command) for command in ("iptables", "ip6tables")):
            raise RuntimeError("Both login firewall families must be blocked")
    except Exception:
        for command in added:
            if rule_present(command):
                run(command, "-D", *RULE)
        raise


def open_login():
    removed = []
    try:
        for command in ("iptables", "ip6tables"):
            if rule_present(command):
                run(command, "-D", *RULE)
                removed.append(command)
        if any(rule_present(command) for command in ("iptables", "ip6tables")):
            raise RuntimeError("A login firewall rule remains")
    except Exception:
        for command in removed:
            if not rule_present(command):
                run(command, "-I", *RULE)
        raise


def online_count():
    query = "SELECT COUNT(*) FROM `char` WHERE online<>0"
    result = run("docker", "exec", "rathena-db", "sh", "-c",
                 'MYSQL_PWD="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}" '
                 'exec mariadb -uroot --batch --raw -N ragnarok -e "$1"',
                 "sh", query)
    return int(result.stdout.strip())


def running(name):
    return run("docker", "inspect", "--format", "{{.State.Running}}", name).stdout.strip() == "true"


def copy_atomic(source, dest):
    temp = dest.with_name(dest.name + ".kafra-new")
    if temp.exists():
        raise RuntimeError(f"Stale temporary file: {temp}")
    try:
        shutil.copy2(source, temp)
        os.replace(temp, dest)
    finally:
        if temp.exists():
            temp.unlink()


def start_map():
    since = datetime.now(timezone.utc).isoformat()
    run("docker", "start", "rathena-map")
    for _ in range(90):
        if not running("rathena-map"):
            raise RuntimeError("Map container exited")
        result = run("docker", "logs", "--since", since, "rathena-map", check=False)
        log = re.sub(r"\x1b\[[0-9;]*[mK]", "", result.stdout + result.stderr)
        if "[Error]" in log or "[Fatal" in log:
            raise RuntimeError("Map startup logged an error")
        if "Map Server is now online" in log:
            return log
        time.sleep(1)
    raise RuntimeError("Map readiness marker missing")


def deploy():
    manifest = json.loads((CANDIDATE / "manifest.json").read_text())
    if manifest["path"] != NAME:
        raise RuntimeError("Unexpected candidate path")
    before, after = manifest["before_sha256"], manifest["after_sha256"]
    if sha(LIVE / NAME) != before or sha(CANDIDATE / "candidate" / NAME) != after:
        raise RuntimeError("Live baseline or candidate hash differs")
    if BACKUP.exists():
        raise RuntimeError("Rollback backup already exists")
    if not all(running(name) for name in ("rathena-login", "rathena-char", "rathena-map", "rathena-db")):
        raise RuntimeError("Expected production containers are not running")
    block_login()
    changed = False
    stopped = False
    try:
        if online_count():
            raise RuntimeError("Players are online")
        pending = BACKUP.with_name(BACKUP.name + ".preparing")
        if pending.exists():
            raise RuntimeError("Incomplete backup preparation already exists")
        pending.mkdir(mode=0o700)
        try:
            old = pending / NAME
            old.parent.mkdir(parents=True)
            shutil.copy2(LIVE / NAME, old)
            if sha(old) != before:
                raise RuntimeError("Backup hash differs")
            os.replace(pending, BACKUP)
        except Exception:
            shutil.rmtree(pending)
            raise
        run("docker", "stop", "-t", "30", "rathena-map", timeout=50)
        stopped = True
        copy_atomic(CANDIDATE / "candidate" / NAME, LIVE / NAME)
        changed = True
        if sha(LIVE / NAME) != after:
            raise RuntimeError("Installed hash differs")
        log = start_map()
        stopped = False
        (BACKUP / "startup.log").write_text(log)
        (BACKUP / "receipt.json").write_text(json.dumps({
            "validated": True, "admission_closed": True,
            "before_sha256": before, "installed_sha256": sha(LIVE / NAME),
            "online_before": 0,
        }, indent=2) + "\n")
        open_login()
    except Exception:
        if changed:
            run("docker", "stop", "-t", "30", "rathena-map", timeout=50, check=False)
            if sha(BACKUP / NAME) != before:
                raise RuntimeError("Rollback backup changed; admission remains blocked")
            copy_atomic(BACKUP / NAME, LIVE / NAME)
            start_map()
        elif stopped and not running("rathena-map"):
            start_map()
        open_login()
        raise
    (BACKUP / "receipt.json").write_text(json.dumps({
        "deployed": True, "admission_closed": False,
        "before_sha256": before, "installed_sha256": sha(LIVE / NAME),
        "online_before": 0,
    }, indent=2) + "\n")


if __name__ == "__main__":
    deploy()
