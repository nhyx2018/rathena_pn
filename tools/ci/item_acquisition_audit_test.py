"""Exercise source tracing with a small imported database and active NPC fixture."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('audit',Path(__file__).parents[1]/'audit_item_acquisition.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)

class AcquisitionTest(unittest.TestCase):
    def test_imported_rewards_called_barter_and_absent_catalog(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            fixtures={
                'db/item_db.yml':'Body: [{Id: 1, AegisName: Box}, {Id: 2, AegisName: Prize}]\nFooter: {Imports: [{Path: db/extra.yml}]}',
                'db/extra.yml':'Body: [{Id: 3, AegisName: Barter}, {Id: 4, AegisName: Trophy}]',
                'db/item_group_db.yml':'Body: [{Group: TEST, SubGroups: [{SubGroup: 1, List: [{Index: 0, Item: Prize, Rate: 100}]}]}]',
                'db/achievement_db.yml':'Body: [{Id: 1, Rewards: {Item: Trophy}}]',
                'npc/re/scripts_main.conf':'npc: npc/test.txt',
                'npc/test.txt':'getitem 1,1; getgroupitem IG_TEST; callshop "Remote Shop",1; // getitem 999,1;\n',
                'npc/barters.yml':'Footer: {Imports: [{Path: npc/custom/barters.yml}]}',
                'npc/custom/barters.yml':'Body: [{Name: Remote Shop, Items: [{Item: Barter}]}]',
                'metadata.tsv':'1\tBox\n2\tPrize\n3\tBarter\n4\tTrophy\n',
                'triage.json':json.dumps({'catalog_missing_references':[{'item_id':i} for i in (1,2,3,4,999)]})}
            for name,text in fixtures.items():
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
            report=root/'report.json'
            with patch.object(audit,'REPO',root),patch.object(sys,'argv',['audit','--metadata',str(root/'metadata.tsv'),
                 '--triage',str(root/'triage.json'),'--report',str(report)]):
                audit.main()
            rows={row['item_id']:row for row in json.loads(report.read_text())['items']}
            self.assertEqual({i for i,row in rows.items() if row['source_path_found']},{1,2,3,4})
            self.assertFalse(rows[999]['in_server_database'])
            self.assertEqual(rows[2]['path'][-1]['kind'],'item group output')
            self.assertEqual(rows[3]['path'][0]['kind'],'configured barter output')

if __name__=='__main__':unittest.main()
