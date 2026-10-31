"""Regression checks for source-group isolation during resumable production."""
import json
from pathlib import Path
import tempfile
import unittest
from make_smoke import fixture
from produce_pilot import source_families

class ProductionIsolationTests(unittest.TestCase):
    def make_run(self, root):
        root=Path(root);(root/'prepared').mkdir()
        family=fixture();family['status']='draft'
        (root/'prepared/RCD-example.json').write_text(json.dumps(family))
        row={k:family[k] for k in ('family_id','split_group_id','split')}
        (root/'split_freeze.json').write_text(json.dumps({'groups':[row],'scope':'Caller-specific metadata must survive resume.'}))
        return root,family

    def test_group_cannot_change_with_same_family_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,family=self.make_run(tmp);family['split_group_id']='another-source'
            (root/'prepared/RCD-example.json').write_text(json.dumps(family))
            with self.assertRaises(ValueError):source_families(root)

    def test_existing_freeze_annotation_does_not_block_or_mutate_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,family=self.make_run(tmp);before=(root/'split_freeze.json').read_bytes()
            self.assertEqual(source_families(root)[0]['family_id'],family['family_id'])
            self.assertEqual((root/'split_freeze.json').read_bytes(),before)

if __name__=='__main__':unittest.main()
