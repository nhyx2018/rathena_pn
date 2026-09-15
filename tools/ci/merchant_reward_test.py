"""Native complete Guild Dealer/Erundek purchase paths; exact stack and resume cases.

This is a bounded fixture, with inherited world, transport, status and persistence
doubles. It does not prove SQL/crash durability or arbitrary callback closure.
"""
from pathlib import Path
import argparse, json, os, re, subprocess
import finalbattle_current_reward_test as current

test = current.test
test.CROWN_WRAPPERS += ('_Z16clif_scriptinputR16map_session_dataj',)
PATHS = ('npc/battleground/bg_common.txt', 'npc/merchants/alchemist.txt')
NAMES = ('Erundek', 'Guild Dealer')
KEYS = ('erundek', 'alchemist')
PLAIN = [*range(7127,7135),7144,*range(12269,12274)]

def bodies(root):
    return [test.gate.body((root/path).read_text(),name) for path,name in zip(PATHS,NAMES)]

def recipe_ids(root):
    bg,alchemy=bodies(root)
    ids={1201,7828,7829,*PLAIN}
    for group in re.findall(r'setarray \.@(Weapons|Items)\[0\],([^;]+);',bg):
        values=[int(n) for n in group[1].split(',')]
        assert len(values)%2==0
        ids.update(values[::2])
    assert len(re.findall(r'callsub S_SellManual,\d+,\d+;',alchemy))==8
    return sorted(ids)

def validate(root):
    manifest=current.validate(root)
    bg,_=bodies(root)
    assert 'if (.@Items[.@i] < 12269 || .@Items[.@i] > 12273 )' in bg
    assert '.@item[0]' not in bg,'Erundek notice must inspect the actual selected item'
    reader=test.gate.base.Reader(root);_,rows=test.gate.base.database_graph(reader)
    items=test.gate.base.scalar_overlay(rows['db/item_db.yml'],'Id')
    ids=recipe_ids(root)
    for id in PLAIN:
        item=items[id]
        assert item['Type'] in ('Etc','Usable','Healing'),(id,'not plain stackable')
        assert not any(item.get('Flags',{}).get(k,False) for k in ('UniqueId','Autoequip')),(id,'derived identity/equip')
        assert not item.get('Stack',{}).get('Inventory',False),(id,'custom stack limit')
        assert item.get('Weight',0)>=0,(id,'weight')
    manifest['merchant_sources']={p:test.sha((root/p).read_bytes()) for p in PATHS}
    manifest['merchant_items']={str(id):items[id] for id in ids}
    manifest['merchant_cases_sha256']=test.sha(Path(__file__).with_name('merchant_reward_cases.inc').read_bytes())
    return manifest

def prepare(build,before):
    build.mkdir(parents=True,exist_ok=True)
    for label,root in [('before',before),('after',test.ROOT)]:
        for key,body in zip(KEYS,bodies(root)):
            (build/f'merchant-{key}-{label}.script').write_text(body)
    ids=recipe_ids(test.ROOT)
    cases=Path(__file__).with_name('merchant_reward_cases.inc').read_text()
    (build/'shop_cases.inc').write_text('#define SHOP_ITEM_COUNT '+str(len(ids))+'\n'+cases)
    inp=list(current.inputs())
    manifest=validate(test.ROOT)
    present={r['Id'] for r in inp[4]}
    assert not present.intersection(ids),'Fixture IDs must not duplicate the 21 base rewards or Gift_Box'
    inp[4]+=[manifest['merchant_items'][str(id)] for id in ids]
    inp[6]=manifest
    (build/'merchant-fixture.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return tuple(inp)

def historical_output(result):
    result.check_returncode()
    text=re.sub(r'\x1b\[[0-9;]*m','',result.stdout+'\n'+result.stderr)
    assert text.count('MERCHANT_NATIVE_OK cases=4 negative=1 expected_grant_failures=3 expected_zeny_errors=1')==1
    for expected in ('buildin_getitem: Failed to add the item to player.',"[Warning]: Script command 'getitem' returned failure."):
        assert text.count(expected)==3,(expected,text)
        text=text.replace(expected,'')
    expected="script_set_reg: failed to set param 'Zeny' to -1."
    assert text.count(expected)==1,(expected,text)
    text=text.replace(expected,'')
    assert text.count('Memory manager: No memory leaks found.')==1
    assert text.count('FINALBATTLE_NATIVE_OK')==1
    assert not re.search(r'\[(?:error|warning)\]|script_set_reg:|buildin_.*(?:failed|fatal)|AddressSanitizer|UndefinedBehaviorSanitizer|runtime error:|TEST FAIL|infinity loop|fatal error|(?:double|invalid) free|Memory manager:(?! No memory leaks found\.)',text,re.I),text

def historical_output_negative_controls():
    expected="script_set_reg: failed to set param 'Zeny' to -1."
    good='MERCHANT_NATIVE_OK cases=4 negative=1 expected_grant_failures=3 expected_zeny_errors=1\nFINALBATTLE_NATIVE_OK\nMemory manager: No memory leaks found.\n'
    good+=('buildin_getitem: Failed to add the item to player.\n'+"[Warning]: Script command 'getitem' returned failure.\n")*3+expected+'\n'
    historical_output(subprocess.CompletedProcess([],0,good,''))
    samples=[good.replace(expected,''),good+expected,good.replace(expected,expected.replace('-1','-2')),
             *(good+'\n'+bad for bad in ('script_set_reg: unrelated failure','[Error]: unrelated','[Warning]: unrelated','runtime error: overflow','AddressSanitizer: failure','buildin_getitem: unexpected failed operation'))]
    for sample in samples:
        try:historical_output(subprocess.CompletedProcess([],0,sample,''))
        except AssertionError:pass
        else:raise AssertionError('Unexpected merchant diagnostic accepted')
    print(f'MERCHANT_OUTPUT_NEGATIVES_OK {len(samples)} altered or unrelated diagnostics rejected')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native-build-dir',type=Path,required=True)
    p.add_argument('--before',type=Path,required=True)
    p.add_argument('--prepare-only',action='store_true')
    a=p.parse_args();historical_output_negative_controls();inputs=prepare(a.native_build_dir,a.before)
    if a.prepare_only:
        print('MERCHANT_FIXTURE_PREPARED full source bodies and actual item contracts validated');raise SystemExit(0)
    test.native(a.native_build_dir,inputs,verifier=validate,fixture_only=True)
    executable=a.native_build_dir.resolve()/'finalbattle_reward_capacity_test'
    result=subprocess.run([str(executable),str(a.native_build_dir.resolve()),'candidate'],cwd=test.ROOT,capture_output=True,text=True,env=dict(os.environ,MERCHANT_NEGATIVE='1'),timeout=120)
    (a.native_build_dir/'merchant-negative.stdout.txt').write_text(result.stdout)
    (a.native_build_dir/'merchant-negative.stderr.txt').write_text(result.stderr)
    historical_output(result)
    print('MERCHANT_NEGATIVE_CONTROLS_OK three lost payments and one aborted manual purchase with unchanged wallet/inventory reproduced in original complete bodies')
