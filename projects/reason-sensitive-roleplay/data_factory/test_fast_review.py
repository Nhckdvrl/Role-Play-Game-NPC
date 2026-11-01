"""Regression checks for label isolation and independent decision/grounding heads."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import fast_review


class FastReviewTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).parent / 'examples' / 'pilot_audited.jsonl'
        self.family = json.loads(path.read_text().splitlines()[0])
        self.family['status'] = 'draft'
        for branch in self.family['branches']:
            for candidate in branch['candidates']:
                candidate['observed'] = None

    def test_worker_receives_opaque_ids_without_author_labels(self):
        base, candidate, nodes, aliases = fast_review.payloads(self.family)
        forbidden = {'intended', 'observed', 'allowed_decisions', 'decision_contract',
                     'teacher_scaffold', 'kind', 'posture', 'split_group_id'}

        def keys(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    yield key
                    yield from keys(item)
            elif isinstance(value, list):
                for item in value:
                    yield from keys(item)

        self.assertFalse(forbidden & set(keys(candidate)))
        self.assertNotIn('candidates', base)
        self.assertEqual(12, len(nodes))
        self.assertEqual(48, len(aliases))
        original = {c['id'] for b in self.family['branches'] for c in b['candidates']}
        self.assertFalse(original & {c['id'] for c in candidate['candidates']})
        self.assertEqual(original, set(aliases.values()))

    def responses(self, altered_id, grounding):
        base, _, mapping, aliases = fast_review.payloads(self.family)
        by_branch = {b['id']: b for b in self.family['branches']}
        by_candidate = {c['id']: (b, c) for b in self.family['branches']
                        for c in b['candidates']}
        local = {'nodes': [{'n': n, 'actions': by_branch[pair[1]]['allowed_decisions'],
                            'missing': [], 'checks': [], 'why': 'test annotation'}
                           for n, pair in mapping.items()], 'blocking': []}
        ratings = []
        for alias, candidate_id in aliases.items():
            branch, c = by_candidate[candidate_id]
            correct = c['intended']['decision_correct']
            ratings.append({'id': alias, 'd': c['intended']['decision_id'], 'c': correct,
                            'g': grounding if candidate_id == altered_id else True,
                            's': .9, 'style': .9,
                            'v': branch['verification_routes'][0]
                            if branch['verification_routes'] and correct else [],
                            'quotes': [c['text']], 'f': True, 'p': False,
                            'why': 'test annotation'})
        rated = {'cs': ratings, 'blocking': [], 'notes': []}

        def dispatch(task, run, model, effort):
            result = local if task['stage'] == 'fast_local_blind' else rated
            return {'status': 'success', 'result': result,
                    'path': str(run / 'test_raw' / task['stage'])}

        return dispatch

    def test_wrong_decision_can_have_unfaithful_basis_without_rewriting_labels(self):
        candidate = next(c for b in self.family['branches'] for c in b['candidates']
                         if not c['intended']['decision_correct'])
        intended = deepcopy(candidate['intended'])
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(fast_review, 'dispatch', self.responses(candidate['id'], False)):
                result = fast_review.review(self.family, Path(directory), 'test-model')
            self.assertEqual('audited', result['status'])
            family = json.loads(Path(result['reviewed_path']).read_text())
            observed = next(c for b in family['branches'] for c in b['candidates']
                            if c['id'] == candidate['id'])
            self.assertEqual(intended, observed['intended'])
            self.assertFalse(observed['observed']['decision_correct'])
            self.assertFalse(observed['observed']['evidence_ok'])

    def test_positive_with_unfaithful_basis_is_blocked(self):
        candidate = next(c for b in self.family['branches'] for c in b['candidates']
                         if c['intended']['decision_correct'])
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(fast_review, 'dispatch', self.responses(candidate['id'], False)):
                result = fast_review.review(self.family, Path(directory), 'test-model')
            self.assertEqual('needs_review', result['status'])
            self.assertTrue(any(candidate['id'] in issue for issue in result['issues']))


if __name__ == '__main__':
    unittest.main()
