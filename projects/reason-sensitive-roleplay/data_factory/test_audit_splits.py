"""Split guard must never feed holdout-driven exclusions back into Train."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import audit_splits
import watch_global_quality as qa


class SplitQualityTests(unittest.TestCase):
    def test_nearest_pair_retrieval_excludes_within_split_pairs(self):
        def family(fid, split):
            return {'family_id': fid, 'split': split,
                    'persona': {'natural_profile': '相同的人物与具体承诺'},
                    'common_visible_context': '相同的地点与决定条件',
                    'branches': [{'visible_observation': '信件需要收件人确认', 'player_turn': '寄出吗'}]}
        families = [family('a', 'train'), family('b', 'train'), family('c', 'test')]
        pairs = qa.top_pairs(families, cross_split=True)
        self.assertEqual(len(pairs), 2)
        self.assertTrue(all(a['split'] != b['split'] for _, a, b in pairs))

    def test_duplicate_quarantines_holdout_regardless_of_pair_order(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); out = root/'runs/split-quality-live'
            (out/'decisions').mkdir(parents=True)
            for directory in audit_splits.RUNS.values():
                (root/'runs'/directory).mkdir(parents=True)
            (out/'decisions/pair.json').write_text(json.dumps({
                'a': 'test-example', 'b': 'train-example', 'status': 'confirmed_duplicate'}))
            families = [{'family_id': 'train-example', 'split': 'train'},
                        {'family_id': 'test-example', 'split': 'test'}]
            with patch.object(qa, 'ROOT', root), patch.object(qa, 'OUT', out):
                audit_splits.merge_exclusions(families)
            self.assertFalse((root/'runs/train5000-live/exclusions.json').exists())
            excluded = json.loads((root/'runs/test800-live/exclusions.json').read_text())
            self.assertEqual(excluded['test-example']['related_family_id'], 'train-example')

    def test_uncertain_pair_does_not_become_confirmed_error(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); out = root/'runs/split-quality-live'
            (out/'decisions').mkdir(parents=True)
            (out/'decisions/pair.json').write_text(json.dumps({
                'a': 'a', 'b': 'b', 'status': 'pending'}))
            with patch.object(qa, 'ROOT', root), patch.object(qa, 'OUT', out):
                audit_splits.merge_exclusions([{'family_id': 'a', 'split': 'train'},
                                               {'family_id': 'b', 'split': 'test'}])
            self.assertFalse((root/'runs/test800-live/exclusions.json').exists())


if __name__ == '__main__':
    unittest.main()
