"""Start the production-built 285/65 map server against disposable SQL."""

import json
import hashlib
from pathlib import Path
import re
import subprocess
import time


ROOT = Path("/app/rathena-builds/kro-285-20260917")
OUT = ROOT / "validation"
NET = "kro285-validation"
DB = "kro285-validation-db"
IMAGE = "rathena:local"
PASSWORD = "validation-only"
OUT.mkdir(exist_ok=True)


def run(*cmd, input=None, timeout=900, check=True):
    return subprocess.run(cmd, input=input, capture_output=True, timeout=timeout, check=check)


if run("docker", "container", "inspect", DB, check=False).returncode == 0:
    raise RuntimeError("Disposable DB name already exists")
if run("docker", "network", "inspect", NET, check=False).returncode == 0:
    raise RuntimeError("Disposable network name already exists")

created_net = created_db = False
try:
    run("docker", "network", "create", "--internal", NET)
    created_net = True
    run("docker", "run", "-d", "--name", DB, "--network", NET,
        "-e", f"MARIADB_ROOT_PASSWORD={PASSWORD}",
        "-e", "MARIADB_DATABASE=ragnarok_ci", "mariadb:noble")
    created_db = True
    sql_cmd = ("docker", "exec", "-e", f"MYSQL_PWD={PASSWORD}", "-i",
               DB, "mariadb", "-uroot", "ragnarok_ci")
    for _ in range(120):
        if run(*sql_cmd, input=b"SELECT 1;", check=False).returncode == 0:
            break
        time.sleep(1)
    else:
        raise RuntimeError("Disposable SQL did not become ready")
    names = re.findall(r"< (sql-files/[^ ]+\.sql)", (ROOT / "tools/ci/sql.sh").read_text())
    if len(names) < 15:
        raise RuntimeError("Missing SQL schema list")
    for name in names:
        run(*sql_cmd, input=(ROOT / name).read_bytes())
    run(*sql_cmd, input=(
        "CREATE USER 'validation'@'%' IDENTIFIED BY 'validation-only';"
        "GRANT ALL ON ragnarok_ci.* TO 'validation'@'%';"
    ).encode())

    config = []
    for prefix in ("login_server", "ipban_db", "char_server", "map_server",
                   "web_server", "log_db"):
        config += [f"{prefix}_ip: {DB}", f"{prefix}_port: 3306",
                   f"{prefix}_id: validation", f"{prefix}_pw: {PASSWORD}",
                   f"{prefix}_db: ragnarok_ci"]
    (ROOT / "conf/import/inter_conf.txt").write_text("\n".join(config) + "\n")
    (ROOT / "conf/import/map_conf.txt").write_text(
        "bind_ip: 127.0.0.1\nmap_ip: 127.0.0.1\nchar_ip: 127.0.0.1\n"
        "char_port: 16121\nmap_port: 15121\nuserid: s1\npasswd: p1\n")
    (ROOT / "conf/import/char_conf.txt").write_text(
        "bind_ip: 127.0.0.1\nchar_ip: 127.0.0.1\nlogin_ip: 127.0.0.1\n"
        "login_port: 16900\nchar_port: 16121\nuserid: s1\npasswd: p1\n")
    (ROOT / "conf/import/login_conf.txt").write_text(
        "bind_ip: 127.0.0.1\nlogin_port: 16900\n")

    cmd = ("docker", "run", "--rm", "--network", NET,
           "--mount", f"type=bind,src={ROOT},dst=/rathena",
           "-w", "/rathena", IMAGE, "sh", "-c", "./map-server --run-once")
    result = run(*cmd, timeout=360, check=False)
    log = (result.stdout + result.stderr).decode("utf-8", errors="replace")
    (OUT / "startup.log").write_text(log)
    import sys
    sys.path.insert(0, str(ROOT / "tools/ci"))
    from release_checks import startup_errors
    errors = startup_errors(log)
    if result.returncode:
        errors.append(f"map-server exit code {result.returncode}")
    if errors:
        (OUT / "startup-errors.json").write_text(json.dumps(errors, indent=2) + "\n")
        raise RuntimeError(f"Production-built startup failed: {errors[:3]}")
    (OUT / "isolated-gate.json").write_text(json.dumps({
        "passed": True, "schema_files": len(names),
        "startup_errors": 0, "internal_network": NET,
        "map_server_sha256": hashlib.sha256((ROOT / "map-server").read_bytes()).hexdigest(),
    }, indent=2) + "\n")
    print(f"PASS: {len(names)} SQL files, production-built map startup")
finally:
    if created_db:
        logs = run("docker", "logs", DB, check=False)
        (OUT / "sql.log").write_bytes(logs.stdout + logs.stderr)
        run("docker", "rm", "-f", DB, check=False)
    if created_net:
        run("docker", "network", "rm", NET, check=False)
