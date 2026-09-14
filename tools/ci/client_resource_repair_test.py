#!/usr/bin/env python3
"""Verify actual item loading, reviewed resource repairs and field preservation."""
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
local fixes = {
    {5054, 'identifiedResourceName', '\190\238\188\188\189\197\184\182\189\186\197\169', '\190\238\187\245\189\197\184\182\189\186\197\169'},
    {6417, 'unidentifiedResourceName', '\176\179\180\217\191\173\184\197', '\176\179\180\217\183\161\191\173\184\197'},
    {11534, 'unidentifiedResourceName', '\190\198\192\218\193\234\189\186', '\190\223\192\218\193\234\189\186'},
}
assert(tbl[5096].identifiedResourceName == fixes[1][4], 'Assassin Mask donor changed')
assert(tbl[6417].identifiedResourceName == fixes[2][4], 'Silvervine artwork changed')
assert(tbl[11534].identifiedResourceName == fixes[3][4], 'Coconut Juice artwork changed')
local before=clone(tbl)
if REQUIRE_INSTALLED then
  for _,id in ipairs(ids) do assert(tbl[id].unidentifiedResourceName == helmet, 'missing installed helmet repair: '..id) end
  for _,fix in ipairs(fixes) do assert(tbl[fix[1]][fix[2]] == fix[4], 'missing installed resource repair: '..fix[1]) end
end
-- Reproduce the original affected metadata in memory even after installation.
for _,id in ipairs(ids) do tbl[id].unidentifiedResourceName=missing end
for _,fix in ipairs(fixes) do tbl[fix[1]][fix[2]]=fix[3] end
dofile(PATCH)
local allowed={}
for _,id in ipairs(ids) do allowed[id]={unidentifiedResourceName=helmet} end
for _,fix in ipairs(fixes) do allowed[fix[1]]={[fix[2]]=fix[4]} end
local count=0
for id,entry in pairs(tbl) do
  count=count+1
  if allowed[id] then
    local expected=clone(before[id])
    for field,value in pairs(allowed[id]) do
      assert(entry[field] == value, 'resource was not repaired: '..id..' '..field)
      expected[field]=value
    end
    assert(equal(entry,expected),'unrelated item field changed: '..id)
  else assert(equal(entry,before[id]),'unrelated item changed: '..id) end
end
local once=clone(tbl);dofile(PATCH);assert(equal(tbl,once),'repair is not idempotent')
-- An independently corrected resource must not be overwritten.
tbl[5581].unidentifiedResourceName='custom-corrected';dofile(PATCH)
assert(tbl[5581].unidentifiedResourceName=='custom-corrected')
for _,fix in ipairs(fixes) do tbl[fix[1]][fix[2]]='custom-corrected' end
dofile(PATCH)
for _,fix in ipairs(fixes) do assert(tbl[fix[1]][fix[2]]=='custom-corrected') end
print('PASS: '..count..' item records preserved; 23 reviewed resource references repaired; repeat loads and custom corrections safe')
'''.replace('REQUIRE_INSTALLED', 'true' if args.require_installed else 'false').replace('PATCH', json.dumps(patch.as_posix()))
    result = subprocess.run([str(args.lua.resolve()), '-'], input=program, text=True,
                            cwd=args.client, capture_output=True)
    print(result.stdout, end='')
    if result.returncode:
        raise SystemExit(result.stderr)


if __name__ == '__main__':
    main()
