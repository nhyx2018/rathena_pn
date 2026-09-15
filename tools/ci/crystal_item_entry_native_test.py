"""Actual pc_useitem -> native queued NPC bridge -> native choice continuation.

NPC event-name lookup is a single registered fixture event, while queueing,
dequeue, event timer dispatch, item use and NPC continuation execute production
code. Packet/world/registry doubles remain; no real client/SQL durability claim.
"""
import argparse
import json
from pathlib import Path
import re
import yaml
import finalbattle_current_reward_test as current

test=current.test
RUNNER=Path(__file__)
CASES=RUNNER.with_name('crystal_item_entry_native_cases.inc')
NPC='npc/custom/chapter2/Chapter2.txt'
DB='db/import/chapter2_item_db.yml'
IDS=(106441,1001997,1002011,1002014,1001999,1002000,1002001,1002002)
test.PRODUCTION=[*test.PRODUCTION,'src/map/npc.cpp']
test.CROWN_WRAPPERS=tuple(w for w in test.CROWN_WRAPPERS if w!='_Z17npc_event_dequeueP16map_session_datab')+('_Z9npc_eventP16map_session_dataPKci','_Z15clif_useitemackPK16map_session_dataiib','_Z21clif_clearunit_singlej8clr_typeRK16map_session_data')

def validate(root):
    manifest=current.validate(root)
    reader=test.gate.base.Reader(root)
    _,rows=test.gate.base.database_graph(reader)
    items=test.gate.base.scalar_overlay(rows['db/item_db.yml'],'Id')
    crystal=items[106441]
    assert crystal['Type']=='Delayconsume'
    assert crystal['Script'].strip()=='doevent "CH2_PhantomCrystal::OnOpen";'
    for id in IDS[1:]:
        item=items[id]
        assert item['Type'] in ('Etc','Usable','Healing')
        assert not item.get('Flags',{}).get('UniqueId') and not item.get('Flags',{}).get('Autoequip') and not item.get('Stack',{}).get('Inventory')
    manifest['crystal_entry_sources']={p:test.sha((root/p).read_bytes()) for p in (NPC,DB,'src/map/pc.cpp','src/map/npc.cpp')}
    manifest['crystal_entry_tests']={p.name:test.sha(p.read_bytes()) for p in (RUNNER,CASES)}
    manifest['crystal_entry_items']={str(id):items[id] for id in IDS}
    return manifest

def prepare(build,before):
    build.mkdir(parents=True,exist_ok=True)
    source=(test.ROOT/NPC).read_text()
    old_source=(before/NPC).read_text()
    for name in ('CH2_OpenPhantomCrystal','CH2_CanGrantMaterial','CH2_PhantomCrystal'):
        body=test.gate.body(source,name)
        if name!='CH2_PhantomCrystal':
            assert body==test.gate.body(old_source,name), 'Item-entry baseline must retain exact reward/helper body: '+name
        (build/(name+'.script')).write_text(body)
    old=next(row for row in yaml.safe_load((before/DB).read_text())['Body'] if row['Id']==106441)
    assert old['Type']=='Delayconsume' and old['Script'].strip()=='callfunc "CH2_OpenPhantomCrystal";'
    (build/'direct-crystal.script').write_text('{ '+old['Script']+' }')
    manifest=validate(test.ROOT)
    inputs=list(current.inputs())
    assert not {row['Id'] for row in inputs[4]}.intersection(IDS)
    inputs[4]+=[manifest['crystal_entry_items'][str(id)] for id in IDS]
    inputs[6]=manifest
    # Preserve the exact private event-data layout from production source. Only
    # its name->event lookup is replaced; npc_event_sub and timers remain native.
    npc_source=(test.ROOT/'src/map/npc.cpp').read_text()
    layout=re.search(r'struct event_data \{.*?\n\};',npc_source,re.S)
    assert layout
    (build/'shop_cases.inc').write_text('#define SHOP_ITEM_COUNT '+str(len(IDS))+'\n'+layout[0]+'\n'+CASES.read_text())
    # pc_useitem inspects more session state than the inherited reward fixture.
    # C++ value initialization safely initializes scalar fields and containers;
    # never memset the nontrivial map_session_data object or edit shared files.
    driver=(test.ROOT/test.DRIVER).read_text()
    old_init='Player sd(new map_session_data);'
    assert driver.count(old_init)==1, 'Exact inherited recipient constructor expected'
    generated=build/'crystal_entry_finalbattle_driver.cpp'
    generated.write_text(driver.replace(old_init,'Player sd(new map_session_data{});',1))
    test.DRIVER=str(generated.resolve())
    (build/'crystal-entry-fixture.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return tuple(inputs)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-build-dir',type=Path,required=True)
    parser.add_argument('--before',type=Path,required=True)
    parser.add_argument('--prepare-only',action='store_true')
    args=parser.parse_args()
    inputs=prepare(args.native_build_dir,args.before)
    if args.prepare_only:
        print('CRYSTAL_ENTRY_PREPARED actual item/bridge/helper source and native event layout');raise SystemExit(0)
    test.native(args.native_build_dir,inputs,verifier=validate,fixture_only=True)
    output=(args.native_build_dir/'candidate.stdout.txt').read_text()
    assert 'CRYSTAL_ITEM_ENTRY_NATIVE_OK cases=6 original_direct_failure=1 queue_and_timer=native event_lookup=fixture' in output
    print('CRYSTAL_ITEM_ENTRY_VERIFIED direct-use menu loss and queued resumable selection')
