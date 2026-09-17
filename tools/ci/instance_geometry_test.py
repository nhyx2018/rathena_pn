#!/usr/bin/env python3
"""Check effective instance maps, entry cells and literal creation/entry names."""
import json
import re
import struct
import zlib
from pathlib import Path
from audit_enchant_upgrades import renewal_records
from instance_access_manifest_test import enabled_scripts

root = Path(__file__).resolve().parents[2]
rows = {}
for row in renewal_records(root, 'db/instance_db.yml'):
    rows.setdefault(row['Id'], {}).update(row)
cells = {}
for rel in ('db/import/map_cache.dat', 'db/re/map_cache.dat', 'db/map_cache.dat'):
    p = root / rel
    if not p.exists():
        continue
    data = p.read_bytes()
    pos = 8
    for _ in range(struct.unpack_from('<H', data, 4)[0]):
        name, w, h, size = struct.unpack_from('<12shhi', data, pos)
        pos += 20
        cells.setdefault(name.split(b'\x00')[0].decode(), (w, h, zlib.decompress(data[pos:pos + size])))
        pos += size
issues = []
for row in rows.values():
    for name in [row['Enter']['Map'], *row.get('AdditionalMaps', {})]:
        if name not in cells:
            issues.append((row['Name'], 'missing map', name))
    e = row['Enter']
    name = e['Map']
    x = e['X']
    y = e['Y']
    if name not in cells:
        continue
    w, h, g = cells[name]
    if not (0 <= x < w and 0 <= y < h) or g[y * w + x] not in (0, 3, 6):
        issues.append((row['Name'], 'blocked entrance', name, x, y))
names = {r['Name'] for r in rows.values()}
for rel in sorted(enabled_scripts(root)):
    s = (root / rel).read_text(errors='replace')
    s = re.sub('/\\*.*?\\*/', '', s, flags=re.S)
    s = re.sub('//[^\\n]*', '', s)
    for name in re.findall('instance_(?:create|enter)\\s*\\(?\\s*"([^"]+)"', s):
        if name not in names:
            issues.append((rel, 'unknown instance', name))
print(json.dumps({'definitions': len(rows), 'issues': issues}, indent=2))
assert not issues, issues
