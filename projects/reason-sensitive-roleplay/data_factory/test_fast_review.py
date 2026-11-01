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

    def responses(self, altered_id, grounding, local_additions=None):
        local_additions = local_additions or {}
        base, _, mapping, aliases = fast_review.payloads(self.family)
        by_branch = {b['id']: b for b in self.family['branches']}
        by_candidate = {c['id']: (b, c) for b in self.family['branches']
                        for c in b['candidates']}
        local = {'nodes': [{'n': n, 'actions': (list(by_branch[pair[1]]['allowed_decisions']) +
                                        list(local_additions.get(pair, []))),
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

    def test_negative_allowed_by_local_reviewer_is_blocked(self):
        branch = self.family['branches'][0]
        candidate = next(c for c in branch['candidates'] if not c['intended']['decision_correct'])
        additions = {(candidate['history_id'], branch['id']): [candidate['intended']['decision_id']]}
        with tempfile.TemporaryDirectory() as directory:
            result = fast_review.review(self.family, Path(directory), 'test-model',
                                        dispatcher=self.responses(None, True, additions))
            self.assertEqual('needs_review', result['status'])
            self.assertTrue(any(candidate['id'] in issue and 'independent reviewers disagree on negative' in issue
                                for issue in result['issues']))
            reviewed = json.loads(Path(result['reviewed_path']).read_text())
            actual = next(c for b in reviewed['branches'] for c in b['candidates'] if c['id'] == candidate['id'])
            self.assertEqual(candidate['intended'], actual['intended'])
            self.assertFalse(actual['observed']['decision_correct'])

    def test_unrendered_local_option_requires_reconciliation(self):
        branch = self.family['branches'][0]
        used = {c['intended']['decision_id'] for c in branch['candidates']}
        extra = next(x for x in self.family['decision_inventory'] if x not in used)
        additions = {(self.family['histories'][0]['id'], branch['id']): [extra]}
        with tempfile.TemporaryDirectory() as directory:
            result = fast_review.review(self.family, Path(directory), 'test-model',
                                        dispatcher=self.responses(None, True, additions))
            self.assertEqual('needs_review', result['status'])
            self.assertTrue(any(branch['id'] in issue and 'needs_allowed_reconciliation' in issue and extra in issue
                                for issue in result['issues']))
            reviewed = json.loads(Path(result['reviewed_path']).read_text())
            actual = next(b for b in reviewed['branches'] if b['id'] == branch['id'])
            self.assertEqual(branch['allowed_decisions'], actual['allowed_decisions'])
            self.assertEqual(self.family['edges'], reviewed['edges'])

    def test_positive_with_unfaithful_basis_is_blocked(self):
        candidate = next(c for b in self.family['branches'] for c in b['candidates']
                         if c['intended']['decision_correct'])
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(fast_review, 'dispatch', self.responses(candidate['id'], False)):
                result = fast_review.review(self.family, Path(directory), 'test-model')
            self.assertEqual('needs_review', result['status'])
            self.assertTrue(any(candidate['id'] in issue for issue in result['issues']))

    def test_agreed_unrendered_option_repairs_metadata_without_changing_labels(self):
        from reconcile_fast_allowed import actor_hash
        branch = self.family['branches'][0]
        used = {c['intended']['decision_id'] for c in branch['candidates']}
        extra = next(x for x in self.family['decision_inventory'] if x not in used)
        additions = {(h['id'], branch['id']): [extra] for h in self.family['histories']}
        actor_before = actor_hash(self.family)
        with tempfile.TemporaryDirectory() as directory:
            result = fast_review.review(self.family, Path(directory), 'test-model',
                                        dispatcher=self.responses(None, True, additions))
            self.assertEqual('audited', result['status'])
            reviewed = json.loads(Path(result['reviewed_path']).read_text())
            self.assertEqual(actor_before, actor_hash(reviewed))
            self.assertIn(extra, reviewed['branches'][0]['allowed_decisions'])
            for original, actual in zip(self.family['branches'], reviewed['branches']):
                for old, new in zip(original['candidates'], actual['candidates']):
                    self.assertEqual(old['text'], new['text'])
                    self.assertEqual(old['intended'], new['intended'])
                    self.assertEqual(old['intended']['decision_correct'], new['observed']['decision_correct'])
            proof = json.loads(Path(reviewed['audit']['records'][-1]).read_text())
            self.assertTrue(proof['candidate_text_intended_observed_unchanged'])


if __name__ == '__main__':
    unittest.main()
