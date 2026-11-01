"""Offline regression tests for engineering-failure reconciliation."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import fast_generate as gen
import reconcile_run
from reconcile_fast_allowed import actor_hash


class ImportFailureRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.run = Path(self.temp.name) / 'run'
        self.run.mkdir()
        self.family = json.loads((Path(__file__).parent / 'examples' / 'pilot_audited.jsonl').read_text().splitlines()[0])
        self.job = self.run / 'job'
        self.job.mkdir()
        gen.put(self.job / 'draft.json', self.family)
        gen.put(self.job / 'reviewed.json', self.family)
        self.failure = {'family_id': self.family['family_id'], 'status': 'needs_review',
                        'job': str(self.job), 'error': "ImportError: cannot import name 'reconcile' from 'reconcile_allowed' (test)"}
        gen.put(self.run / 'state.json', {'split': 'train', 'completed': [self.failure]})
        gen.jsonl(self.run / 'families.jsonl', [])
        gen.jsonl(self.run / 'needs_review.jsonl', [self.failure])

    def recover(self):
        result = {'status': 'audited', 'issues': [], 'reviewed_path': str(self.job / 'reviewed.json')}
        with patch.object(reconcile_run.fast_review, 'review', return_value=result) as review, \
             patch.object(reconcile_run.agent_dispatch, 'dispatch', side_effect=AssertionError('model called')):
            reconcile_run.reconcile_run(self.run)
        review.assert_called_once()
        self.assertIs(review.call_args.kwargs['dispatcher'], reconcile_run.cached)
        state = json.loads((self.run / 'state.json').read_text())
        archive = Path(state['metadata_reconciliation_history'][-1]['path'])
        self.assertEqual(self.failure, json.loads((archive / (self.family['family_id'] + '-engineering_failure.json')).read_text()))
        self.assertEqual(0, state['metadata_reconciliation_history'][-1]['model_calls'])
        return state, archive

    def test_saved_review_releases_original_family_and_archives_failure(self):
        state, archive = self.recover()
        released, = gen.read_rows(self.run / 'families.jsonl')
        self.assertEqual('audited', state['completed'][0]['status'])
        self.assertNotIn('error', state['completed'][0])
        self.assertEqual(actor_hash(self.family), actor_hash(released))
        for before, after in zip(self.family['branches'], released['branches']):
            for a, b in zip(before['candidates'], after['candidates']):
                self.assertEqual((a['text'], a['intended'], a['observed']),
                                 (b['text'], b['intended'], b['observed']))
        self.assertEqual([], list(gen.read_rows(self.run / 'needs_review.jsonl')))
        self.assertTrue(json.loads((archive / 'summary.json').read_text())['results'][0]['released'])
        self.assertEqual(1, len(list(gen.read_rows(self.run.parent / 'split_fingerprints.jsonl'))))

    def test_duplicate_is_quarantined_without_success(self):
        existing = deepcopy(self.family)
        existing['family_id'] = 'existing-family'
        existing['split_group_id'] = 'existing-group'
        gen.jsonl(self.run / 'families.jsonl', [existing])
        state, archive = self.recover()
        self.assertEqual([existing], list(gen.read_rows(self.run / 'families.jsonl')))
        self.assertEqual('quarantined', state['completed'][0]['status'])
        self.assertIn('existing-family', state['completed'][0]['error'])
        pending, = gen.read_rows(self.run / 'needs_review.jsonl')
        self.assertEqual('quarantined', pending['status'])
        summary = json.loads((archive / 'summary.json').read_text())
        self.assertEqual('existing-family', summary['results'][0]['withheld_novelty'])
        self.assertNotIn('released', summary['results'][0])
        self.assertEqual(0, state['metadata_reconciliation_history'][-1]['newly_released'])
        self.assertFalse((self.run.parent / 'split_fingerprints.jsonl').exists())


if __name__ == '__main__':
    unittest.main()
