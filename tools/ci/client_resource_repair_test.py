#!/usr/bin/env python3
"""Verify the actual item loader and the narrow unidentified-helmet repair."""
import argparse
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lua', type=Path, required=True)
    parser.add_argument('--client', type=Path, required=True)
    parser.add_argument('--require-installed', action='store_true')
    args = parser.parse_args()
    patch = ROOT / 'client-patch/client_compat/SystemEN/ItemResourceRepair.lua'
    program = r'''
dofile('SystemEN/itemInfo.lua')
local function clone(v)
  if type(v) ~= 'table' then return v end
  local copy = {}; for k, x in pairs(v) do copy[k] = clone(x) end; return copy
end
local function equal(a, b)
  if type(a) ~= type(b) then return false end
  if type(a) ~= 'table' then return a == b end
  for k, v in pairs(a) do if not equal(v, b[k]) then return false end end
  for k in pairs(b) do if a[k] == nil then return false end end
  return true
end
local ids = {5581,5582}; for id=400529,400546 do ids[#ids+1]=id end
local missing='\197\245\177\184'
local helmet='\199\239\184\167'
assert(tbl[2228].unidentifiedResourceName == helmet, 'standard helmet donor changed')
local before=clone(tbl)
if REQUIRE_INSTALLED then
  for _,id in ipairs(ids) do assert(tbl[id].unidentifiedResourceName == helmet, 'missing installed helmet repair: '..id) end
end
-- Reproduce the original affected metadata in memory even after installation.
for _,id in ipairs(ids) do tbl[id].unidentifiedResourceName=missing end
dofile(PATCH)
local allowed={};for _,id in ipairs(ids) do allowed[id]=true end
local count=0
for id,entry in pairs(tbl) do
  count=count+1
  if allowed[id] then
    assert(entry.unidentifiedResourceName == helmet, 'helmet resource was not repaired: '..id)
    local expected=clone(before[id]);expected.unidentifiedResourceName=helmet
    assert(equal(entry,expected),'unrelated item field changed: '..id)
  else assert(equal(entry,before[id]),'unrelated item changed: '..id) end
end
local once=clone(tbl);dofile(PATCH);assert(equal(tbl,once),'repair is not idempotent')
-- An independently corrected resource must not be overwritten.
tbl[5581].unidentifiedResourceName='custom-corrected';dofile(PATCH)
assert(tbl[5581].unidentifiedResourceName=='custom-corrected')
print('PASS: '..count..' item records preserved; 20 helmet resources repaired; repeat loads and custom corrections safe')
'''.replace('REQUIRE_INSTALLED', 'true' if args.require_installed else 'false').replace('PATCH', json.dumps(patch.as_posix()))
    result = subprocess.run([str(args.lua.resolve()), '-'], input=program, text=True,
                            cwd=args.client, capture_output=True)
    print(result.stdout, end='')
    if result.returncode:
        raise SystemExit(result.stderr)


if __name__ == '__main__':
    main()
