"""Native grant/resume checks; explicit world and persistence doubles, no crash durability claim."""
from pathlib import Path
import argparse, json, os, subprocess, re
import finalbattle_current_reward_test as current

test=current.test
PATHS=['npc/custom/instances/FallOfGlastHeim.txt','npc/custom/instances/LakeOfFire.txt','npc/custom/chapter2/Chapter2.txt','db/import/chapter2_item_db.yml']
EXTRA=[15388,25739,6607,1001414,1001415,1001440,1001441,1001442,1001443,106441,1001997,1002011,1002014,1001999,1002000,1002001,1002002]
def verify(root):
 m=current.validate(root);m['resume_sources']={p:test.sha((root/p).read_bytes()) for p in PATHS};return m

def segment(path,name,kind):
 body=test.gate.body(path.read_text(),name)
 if kind=='fall':
  return '{ .@item=15388; setarray .@cost[0],25739,5,6607,10; mes "Confirm"; next; '+body[body.index('if (select("Exchange.:Cancel.")'):body.index('OnInit:')]+'}'
 if kind=='lake':return body[:body.index("\tif (isbegin_quest('boss_quest)")]+ '\nclose; }'
 return body

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--native-build-dir',type=Path,required=True);p.add_argument('--before',type=Path,required=True);p.add_argument('--cases',type=Path,required=True);a=p.parse_args();b=a.native_build_dir;b.mkdir(parents=True,exist_ok=True)
 for key,rel,name in [('fall',PATHS[0],'OSC1052#fogh'),('lake',PATHS[1],'Lake Exit#pn_lake'),('crystal',PATHS[2],'CH2_OpenPhantomCrystal')]:
  for tag,root in [('before',a.before),('after',test.ROOT)]:
   (b/(key+'-'+tag+'.script')).write_text(segment(root/rel,name,key))
 for rel,name in [(PATHS[1],'F_PNLake_CanGrant'),(PATHS[2],'CH2_CanGrantMaterial')]:
  (b/(name+'.script')).write_text(test.gate.body((test.ROOT/rel).read_text(),name))
 inp=list(current.inputs());reader=test.gate.base.Reader(test.ROOT);_,rows=test.gate.base.database_graph(reader);items=test.gate.base.scalar_overlay(rows['db/item_db.yml'],'Id');inp[4]+= [items[i] for i in EXTRA];inp[6]=verify(test.ROOT)
 assert items[106441]['Type']=='Delayconsume'
 for i in [1001414,1001415,1001440,1001441,1001442,1001443,1001997,1002011,1002014,1001999,1002000,1002001,1002002]:
  assert items[i]['Type'] in ('Etc','Usable','Delayconsume') and not items[i].get('Flags',{}).get('UniqueId') and not items[i].get('Flags',{}).get('BindOnEquip') and not items[i].get('Stack'),i
 (b/'shop_cases.inc').write_text('#define SHOP_ITEM_COUNT '+str(len(EXTRA))+'\n'+a.cases.read_text())
 test.native(b,tuple(inp),verifier=verify,fixture_only=True)


 env=dict(os.environ,REWARD_NEGATIVE='1')
 result=subprocess.run([str(b.resolve()/'finalbattle_reward_capacity_test'),str(b.resolve()),'candidate'],cwd=test.ROOT,capture_output=True,text=True,env=env,timeout=120)
 (b/'negative.stdout.txt').write_text(result.stdout);(b/'negative.stderr.txt').write_text(result.stderr)
 result.check_returncode()
 assert 'REWARD_RESUME_NATIVE_OK cases=101 negative=1' in result.stdout
 assert result.stdout.count("[Warning]: Script command 'getitem' returned failure.")==8
 assert result.stderr.count('buildin_getitem: Failed to add the item to player.')==8
 assert not re.search('AddressSanitizer|runtime error:|TEST FAIL|\\[Error\\]',result.stdout+result.stderr)
 print('NEGATIVE_CONTROLS_OK original failures reproduced separately; exact eight grant failures')
