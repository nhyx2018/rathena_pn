"""Build a 285/65 client level-table overlay from the effective client GRFs.

The source external settings contain other client-specific settings. This tool
changes only the two fourth-job caps in each of the three effective tables.
"""

import argparse
import configparser
from pathlib import Path
import re
import struct
import sys
import zlib


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from client_release_audit import expand, index  # noqa: E402


PREFIX = b"data\\luafiles514\\lua files\\service_korea\\"
NAMES = tuple(
    PREFIX + ("externalsettings_kr" + suffix + ".lub").encode("ascii")
    for suffix in ("", "_qm", "_sak")
)
FIELDS = ((b"BaseLevel4th", b"275", b"285"),
          (b"JobLevel4th", b"60", b"65"))


def archive_order(client: Path) -> list[tuple[int, str]]:
    ini = configparser.ConfigParser(interpolation=None)
    if not ini.read(client / "DATA.INI", encoding="utf-8-sig"):
        raise ValueError("DATA.INI was not found")
    order = sorted((int(slot), archive) for slot, archive in ini["Data"].items())
    if not order or [slot for slot, _ in order] != list(range(len(order))):
        raise ValueError("DATA.INI archive slots must be contiguous from zero")
    if len(order) > 10:
        raise ValueError("The client supports at most ten archive slots")
    if any(Path(name).name != name or not name.lower().endswith(".grf")
           for _, name in order):
        raise ValueError("DATA.INI must name local GRF files")
    return order


def effective_tables(client: Path) -> dict[bytes, tuple[bytes, str]]:
    wanted = {name.lower(): name for name in NAMES}
    found: dict[bytes, tuple[bytes, str]] = {}
    for _, archive in archive_order(client):
        path = client / archive
        rows = index(path)
        with path.open("rb") as stream:
            for name, packed_size, length, flags, offset in rows:
                key = name.replace(b"/", b"\\").lower()
                if key not in wanted or key in found:
                    continue
                if flags & 6 or not flags & 1:
                    raise ValueError(f"{archive}: {name!r} is encrypted or deleted")
                stream.seek(46 + offset)
                packed = stream.read(packed_size)
                if len(packed) != packed_size:
                    raise ValueError(f"{archive}: truncated {name!r}")
                try:
                    raw = expand(packed, length)
                except (ValueError, zlib.error):
                    if len(packed) != length:
                        raise
                    raw = packed
                found[key] = (raw, archive)
        if len(found) == len(NAMES):
            break
    missing = [name.decode("ascii") for name in NAMES if name.lower() not in found]
    if missing:
        raise ValueError(f"Missing effective client tables: {missing}")
    for name in NAMES:
        loose = client.joinpath(*name.decode("ascii").split("\\"))
        if loose.exists():
            raise ValueError(f"Loose client file can override the GRF: {loose}")
    return found


def patch_table(raw: bytes, name: bytes) -> bytes:
    if raw.startswith(b"\x1bLua"):
        raise ValueError(f"{name!r}: compiled Lua cannot be patched as text")
    blocks = list(re.finditer(
        rb"(?ms)^[ \t]*MaxLevelTable[ \t]*=[ \t]*\{.*?^[ \t]*\}", raw))
    if len(blocks) != 1:
        raise ValueError(f"{name!r}: expected one MaxLevelTable")
    block = blocks[0]
    result = block.group()
    for field, old, new in FIELDS:
        pattern = re.compile(rb"(?m)^([ \t]*" + field + rb"[ \t]*=[ \t]*)(\d+)([ \t]*,)")
        matches = list(pattern.finditer(result))
        if len(matches) != 1 or matches[0].group(2) not in (old, new):
            raise ValueError(f"{name!r}: unexpected {field.decode()} value or count")
        match = matches[0]
        result = result[:match.start(2)] + new + result[match.end(2):]
    return raw[:block.start()] + result + raw[block.end():]


def build(entries: dict[bytes, bytes]) -> bytes:
    body, table = bytearray(), bytearray()
    for name, raw in sorted(entries.items()):
        packed = zlib.compress(raw, 9)
        table += name + b"\0" + struct.pack(
            "<IIIBI", len(packed), len(packed), len(raw), 1, len(body))
        body += packed
    packed_table = zlib.compress(table, 9)
    return (b"Master of Magic\0" + bytes(14)
            + struct.pack("<IIII", len(body), 0, len(entries) + 7, 0x200)
            + body + struct.pack("<II", len(packed_table), len(table))
            + packed_table)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client", type=Path, required=True,
                        help="Client directory containing DATA.INI and its GRFs")
    parser.add_argument("--output", type=Path,
                        help="Write the generated overlay GRF here")
    parser.add_argument("--check", action="store_true",
                        help="Validate and build in memory without writing files")
    args = parser.parse_args()
    if args.check == bool(args.output):
        parser.error("Choose exactly one of --check and --output")
    originals = effective_tables(args.client)
    entries = {name: patch_table(originals[name.lower()][0], name) for name in NAMES}
    grf = build(entries)
    # The existing GRF reader independently checks the archive round trip.
    sys.path.insert(0, str(ROOT / "client-patch" / "client_compat"))
    from merge_grfs import read  # noqa: E402
    if read(grf) != entries:
        raise ValueError("Generated GRF did not round trip")
    for name in NAMES:
        print(f"{name.decode()}: {originals[name.lower()][1]} -> 285/65")
    if args.output:
        args.output.write_bytes(grf)
        print(f"Built {args.output}: {len(grf):,} bytes")
    else:
        print(f"Validated three-entry overlay in memory: {len(grf):,} bytes")


if __name__ == "__main__":
    main()
