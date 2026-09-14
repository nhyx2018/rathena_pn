"""Current native crystal capacity/retry fixture; not a broad callback-closure proof.

The three reward bodies match the accepted September 7 fixture byte for byte
after newline normalization. Later encounter-state guards lie outside these
bodies. The legacy whole-world safety gate remains unchanged and independent.
"""
import argparse
from pathlib import Path
import finalbattle_reward_capacity_test as test

SHOP_CASES = None
SHOP_PATHS = ("npc/custom/fashion_points/FashionPoints.txt", "npc/battleground/kvm/kvm_item_pay.txt")
PINS = {
    'EP21_FB_CheckPlainBatch': '16735455455bf34828772b656f213d99f577a0771120dfe394910c522e0db0c8',
    'Giant Serpent Crystal#ep21_fb': '4963bd4512a1119f3b14b11a4779dafab42d2c9f2063272f381ac59065f113e3',
    'Giant Serpent Crystal#ep21_fb_hard': '899bbd5c090911f04b516f12be9efabd178e73866ac17de0a426f084b672be68',
}

def validate(root):
    gate=test.gate
    reader=gate.base.Reader(root)
    source=reader.text(test.NPC)
    for name,digest in PINS.items():
        test.require(test.sha(gate.body(source,name).encode())==digest, 'Reviewed reward body changed: '+name)
    daily=gate.body(reader.text(gate.DAILY),'EP21_DailyKey')
    test.require(test.sha(daily.encode())=='d6ca6f73b1c8fb5073f29b86942018f89fab56831a1e858315033d60f92c5bd1','Daily key changed')
    manifest=gate.collect(reader)
    for section in ('outputs','achievements','script_limits'):
        test.require(gate.base.digest(gate.base.canonical(manifest[section]))==gate.PINS[section], 'Reward fixture data changed: '+section)
    if SHOP_CASES:
        manifest['shop_source_hashes']={p:test.sha(reader.text(p).encode()) for p in SHOP_PATHS}
    return manifest

def inputs():
    manifest=validate(test.ROOT)
    source=(test.ROOT/test.NPC).read_text()
    helper=test.gate.body(source,'EP21_FB_CheckPlainBatch')
    start=source.index('// Exact capacity for this file')
    end=source.index('jor_raise1,132,323,4')
    old=source[:start]+source[end:]
    call='callfunc("EP21_FB_CheckPlainBatch",.@reward_item,.@reward_amount,.@reward_count)'
    test.require(old.count(call)==2,'Exactly two capacity checks')
    old=old.replace(call,'checkweight2(.@reward_item,.@reward_amount)')
    reader=test.gate.base.Reader(test.ROOT)
    _,rows=test.gate.base.database_graph(reader)
    items=test.gate.base.scalar_overlay(rows['db/item_db.yml'],'Id')
    achievement_rows=[r for r in manifest['achievements']['ordered_records'] if r.get('Group') in ('Get_Item','Goal_Achieve')]
    test.require(len(achievement_rows)==27,'Achievement fixture scope')
    daily=test.gate.body(reader.text(test.gate.DAILY),'EP21_DailyKey')
    return old.encode(),source.encode(),source.encode(),helper,manifest['outputs']['records']+[items[644]]+([items[1201],items[41090]] if SHOP_CASES else []),achievement_rows,manifest,daily

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-build-dir',type=Path,required=True)
    parser.add_argument('--shop-cases',type=Path)
    args=parser.parse_args()
    SHOP_CASES=args.shop_cases
    if SHOP_CASES:
        args.native_build_dir.mkdir(parents=True,exist_ok=True)
        (args.native_build_dir/'shop_cases.inc').write_bytes(SHOP_CASES.read_bytes())
        for path,name,marker,setup,output in (
          (SHOP_PATHS[0],'Fashion Box Shop#FP','if (select("Buy:Cancel")','setarray .@box[0],41090; .@i=0; .@cost=50;','fashion-commit.script'),
          (SHOP_PATHS[1],'KVM Logistic Officer#a','switch(select("No, I won','.@item_id=1201; .@req_setting=0; setarray .@prices[0],100;','kvm-commit.script')):
            body=test.gate.body((test.ROOT/path).read_text(),name)
            (args.native_build_dir/output).write_text('{ '+setup+' mes "Confirm purchase"; next; '+body[body.index(marker):])
    test.output_negative_controls()
    test.native(args.native_build_dir,inputs(),verifier=validate,fixture_only=True)
