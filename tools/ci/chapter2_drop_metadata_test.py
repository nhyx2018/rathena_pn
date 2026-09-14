#!/usr/bin/env python3
"""Validate missing Chapter 2 drop metadata through the actual Lua 5.1 loader."""
import argparse
import json
from pathlib import Path
import subprocess

from audit_enchant_upgrades import renewal_records

ROOT = Path(__file__).resolve().parents[2]
IDS = (1002678, 1002679, 1002681, 1002683, 1002693, 1002695, 1002702, 1002705)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lua', type=Path, required=True)
    parser.add_argument('--client', type=Path, required=True)
    parser.add_argument('--require-installed', action='store_true')
    parser.add_argument('--dump', type=Path, help='Optional complete metadata TSV for asset audits')
    args = parser.parse_args()
    records = {}
    for row in renewal_records(ROOT, 'db/item_db.yml'):
        if row['Id'] in IDS:
            records.setdefault(row['Id'], {}).update(row)
    assert set(records) == set(IDS)
    assert all(row['Type'] == 'Etc' and row.get('Slots', 0) == 0 for row in records.values())
    expected = '{' + ','.join(
        f'[{item}]=' + '{name=' + json.dumps(row['Name']) + ',weight=' + json.dumps(format(row.get('Weight', 0)/10, 'g')) + '}'
        for item, row in records.items()) + '}'
    patch = ROOT / 'client-patch/chapter2_native/SystemEN/itemInfo_Chapter2Materials.lua'
    prelude = '\n'.join((
        'local expected=' + expected,
        'local patch=' + json.dumps(patch.as_posix()),
        'local require_installed=' + str(args.require_installed).lower(),
        'local dump=' + (json.dumps(args.dump.resolve().as_posix()) if args.dump else 'nil'),
    ))
    code = r'''
assert(_VERSION == 'Lua 5.1')
dofile('SystemEN/itemInfo.lua')
local function clone(v)
  if type(v) ~= 'table' then return v end
  local t={}; for k,x in pairs(v) do t[k]=clone(x) end; return t
end
local function equal(a,b)
  if type(a) ~= type(b) then return false end
  if type(a) ~= 'table' then return a==b end
  for k,v in pairs(a) do if not equal(v,b[k]) then return false end end
  for k in pairs(b) do if a[k]==nil then return false end end
  return true
end
local before=clone(tbl)
local missing=0
for id in pairs(expected) do
  if not tbl[id] then missing=missing+1 end
  if require_installed then assert(tbl[id], 'Installed loader missing item '..id) end
  tbl[id]=nil -- Reproduce all eight absent definitions, including after installation.
end
dofile(patch); F_itemInfoMerge(tbl_chapter2materials)
for id,record in pairs(before) do
  if not expected[id] then assert(equal(tbl[id],record),'Unrelated item changed: '..id) end
end
local total=0
for id,record in pairs(tbl) do
  total=total+1
  assert(before[id] or expected[id], 'Unexpected new item: '..id)
  if expected[id] then
    local e=expected[id]
    assert(record.identifiedDisplayName==e.name and record.unidentifiedDisplayName==e.name)
    assert(record.identifiedResourceName=='EpisodClear20' and record.unidentifiedResourceName=='EpisodClear20')
    assert(record.slotCount==0 and record.ClassNum==0 and record.costume==false)
    assert(equal(record.identifiedDescriptionName, {'Type: Etc','Weight: '..e.weight}))
    if require_installed then assert(equal(before[id],record),'Installed metadata differs: '..id) end
  end
end
local once=clone(tbl)
dofile(patch); F_itemInfoMerge(tbl_chapter2materials)
assert(equal(tbl,once),'Repeated load changed metadata')
for id in pairs(expected) do tbl[id].identifiedDisplayName='Independent translation '..id end
local custom=clone(tbl)
dofile(patch); F_itemInfoMerge(tbl_chapter2materials)
assert(equal(tbl,custom),'Existing translation was overwritten')
tbl=once
local registered={}
function AddItem(id,uname,uresource,name,resource,slots,classnum)
  assert(tbl[id] and not registered[id], 'Unexpected or duplicate registration')
  registered[id]=true
  if expected[id] then
    assert(name==expected[id].name and uname==name)
    assert(resource=='EpisodClear20' and uresource==resource)
    assert(slots==0 and classnum==0)
  end
  return true
end
function AddItemIdentifiedDesc(id,line) assert(type(line)=='string'); return true end
function AddItemUnidentifiedDesc(id,line) assert(type(line)=='string'); return true end
function AddItemIsCostume(id,value) if expected[id] then assert(value==false) end; return true end
function AddItemEffectInfo() return true end
function AddItemPackageID() return true end
local ok,msg=main(); assert(ok,msg)
local count=0; for _ in pairs(registered) do count=count+1 end
assert(count==total)
for id in pairs(expected) do assert(registered[id], 'Item not registered: '..id) end
if dump then
  local ids={}; for id in pairs(tbl) do ids[#ids+1]=id end; table.sort(ids)
  local function hex(s) return (s:gsub('.',function(c) return string.format('%02x',c:byte()) end)) end
  local f=assert(io.open(dump,'wb'))
  for _,id in ipairs(ids) do
    local r=tbl[id]
    f:write(id,'\t',hex(r.identifiedDisplayName),'\t',hex(r.identifiedResourceName),'\t',hex(r.unidentifiedResourceName),'\t',r.ClassNum or 0,'\n')
  end
  f:close()
end
print('PASS: eight drop definitions; '..missing..' absent before repair; '..total..' actual AddItem registrations; unrelated metadata preserved; repeat loads and translations safe')
'''
    result = subprocess.run([str(args.lua.resolve()), '-'], cwd=args.client,
                            input=prelude + code, text=True, capture_output=True, timeout=120)
    print(result.stdout, end='')
    if result.returncode:
        raise SystemExit(result.stderr)


if __name__ == '__main__':
    main()
