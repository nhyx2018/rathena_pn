"""Package the future 285/65 operations scripts with deterministic metadata."""

import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import os


HERE = Path(__file__).resolve().parent
PACKAGES = Path(os.environ["PN_CLIENT_PACKAGES_ROOT"]).resolve() if os.environ.get(
    "PN_CLIENT_PACKAGES_ROOT") else HERE.parent
WORK = PACKAGES / "remediation-20260918"
SOURCE = WORK / "levelcap-ops"
OUTPUT = WORK / "LevelCap-285-Operations-20260918-Verified.tar.gz"
RECEIPT = WORK / "server-ops-package-verified.json"
NAMES = (
    "deploy_server.py",
    "isolated_gate.py",
    "test_deploy_server.py",
    "validation/client-install.json",
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def build():
    payloads = {}
    for name in NAMES:
        path = SOURCE / name
        if not path.is_file() or path.is_symlink():
            raise RuntimeError(f"Unexpected operations source: {name}")
        payloads[name] = path.read_bytes()
    proof = json.loads(payloads["validation/client-install.json"])
    if (proof.get("installed") is not True or
            proof.get("new_sha256") !=
            "c4e8767352df87f16ea2841b47a691e4b1a2891f4530d829fb1daf7b83c1606a" or
            "backup" in proof):
        raise RuntimeError("Client install proof is missing, changed, or contains a local path")
    fd, temp_name = tempfile.mkstemp(prefix=OUTPUT.name + ".", suffix=".tmp", dir=WORK)
    os.close(fd)
    temp = Path(temp_name)
    try:
        with temp.open("wb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, compresslevel=9, mtime=0) as compressed:
                with tarfile.open(fileobj=compressed, mode="w") as archive:
                    for name, data in payloads.items():
                        info = tarfile.TarInfo(name)
                        info.size = len(data)
                        info.mode = 0o644
                        info.mtime = 0
                        archive.addfile(info, io.BytesIO(data))
        with tarfile.open(temp, "r:gz") as archive:
            if archive.getnames() != list(NAMES):
                raise RuntimeError("Operations archive has unexpected members")
            for name, data in payloads.items():
                if archive.extractfile(name).read() != data:
                    raise RuntimeError(f"Operations archive changed {name}")
        if OUTPUT.exists() and OUTPUT.read_bytes() != temp.read_bytes():
            raise RuntimeError("Existing operations archive differs; review before replacing")
        os.replace(temp, OUTPUT)
    finally:
        temp.unlink(missing_ok=True)
    report = {
        "package": OUTPUT.name,
        "sha256": sha(OUTPUT.read_bytes()),
        "bytes": OUTPUT.stat().st_size,
        "members": {name: sha(data) for name, data in payloads.items()},
    }
    RECEIPT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    build()
