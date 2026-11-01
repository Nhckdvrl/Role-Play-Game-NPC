import contextlib
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import fast_generate as g
from test_fast_build import compact


class SplitTests(unittest.TestCase):
    def setUp(self):
        self.family = json.loads((Path(__file__).parent/'examples'/'pilot_audited.jsonl').read_text().splitlines()[0])

    def test_build_sets_isolated_split_and_source_group(self):
        for split in ('train', 'dev', 'test'):
            fid = f'RCD-{split}-stream-00000010'
            f = g.build(compact(), fid, 10, 'test-run', split=split)
            self.assertEqual(split, f['split'])
            self.assertEqual(fid, f['split_group_id'])

    def test_group_freeze_and_cross_split_similar_story_quarantine(self):
        with tempfile.TemporaryDirectory() as d:
            registry = Path(d)/'registry.jsonl'
            first = deepcopy(self.family); first['split_group_id'] = 'train-group'
            self.assertIsNone(g.registry_append(registry, 'train', 'train-group', first))
            second = deepcopy(first); second['split_group_id'] = 'dev-group'
            self.assertEqual('train-group', g.registry_append(registry, 'dev', 'dev-group', second))
            with self.assertRaisesRegex(ValueError, 'split group already frozen'):
                g.registry_append(registry, 'test', 'train-group')
            records = [json.loads(line) for line in registry.read_text().splitlines()]
            self.assertNotIn(first['persona']['natural_profile'], registry.read_text())
            self.assertTrue(records[0]['features'])

    def test_split_nonce_and_seed_context_do_not_cross_splits(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d); seed = base/'seed.jsonl'; rows = []
            for split in ('train', 'dev', 'test'):
                f = deepcopy(self.family); f['split'] = split
                f['family_id'] = 'seed-'+split; f['split_group_id'] = 'group-'+split
                f['persona']['natural_profile'] = 'ONLY_'+split.upper()+' 独有背景。'
                rows.append(f)
            g.jsonl(seed, rows); captured = {}
            def fake_job(run, idx, payload, split='train'):
                captured[split] = payload
                return {'family_id': f'RCD-{split}-stream-{idx:08d}', 'status': 'needs_review'}
            with patch.object(g, 'run_job', side_effect=fake_job):
                for split in ('train', 'dev', 'test'):
                    run = base/split; run.mkdir()
                    args = SimpleNamespace(split=split, seed_snapshot=[seed], import_snapshot=[], start_index=0,
                                           target=3, concurrency=1, limit_new=1, import_only=False)
                    with contextlib.redirect_stdout(io.StringIO()):
                        g.execute(args, run)
            self.assertEqual({'train:0', 'dev:0', 'test:0'},
                             {payload['split_source_nonce'] for payload in captured.values()})
            for split, payload in captured.items():
                summaries = ''.join(payload['recent_mechanism_summaries'])
                self.assertIn('ONLY_'+split.upper(), summaries)
                for other in {'train', 'dev', 'test'}-{split}:
                    self.assertNotIn('ONLY_'+other.upper(), summaries)

    def test_seed_filter_uses_only_current_split(self):
        with tempfile.TemporaryDirectory() as d:
            run = Path(d); src = run/'seed.jsonl'
            rows = []
            for split in ('train', 'dev', 'test'):
                f = deepcopy(self.family); f['split'] = split; f['family_id'] = 'seed-'+split
                f['split_group_id'] = 'group-'+split; rows.append(f)
            g.jsonl(src, rows); (run/'STOP_AFTER_DRAIN').touch()
            a = SimpleNamespace(split='dev', seed_snapshot=[src], import_snapshot=[], start_index=0,
                                target=3, concurrency=1, limit_new=1, import_only=False)
            with contextlib.redirect_stdout(io.StringIO()):
                g.execute(a, run)
            result = list(g.read_rows(run/'families.jsonl'))
            self.assertEqual(['seed-dev'], [f['family_id'] for f in result])
            state = json.loads((run/'state.json').read_text())
            self.assertEqual('dev', state['split'])
            self.assertEqual(1, state['audited_families'])
            self.assertEqual(0, state['audited_train'])


if __name__ == '__main__':
    unittest.main()
