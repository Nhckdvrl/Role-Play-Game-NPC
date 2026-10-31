"""Regression tests use an artificial interface fixture, not production data."""
from copy import deepcopy
import unittest

from make_smoke import fixture
import quality


def natural_fixture():
    f = fixture()
    f['status'] = 'draft'
    f['history_mode'] = 'natural'
    f['blocks'] = []
    for h in f['histories']:
        h['block_order'] = []
        h['messages'] = [{'role': role, 'content': f'fixture {i} {role}'}
                         for i in range(18) for role in ('user', 'assistant')]
    return f


class QualityTest(unittest.TestCase):
    def test_valid_natural_fixture(self):
        self.assertTrue(quality.analyze([natural_fixture()])['passed'])

    def test_smoke_is_rejected(self):
        self.assertTrue(any('smoke_unreviewed' in e for e in quality.analyze([fixture()])['errors']))

    def test_duplicate_grid_cell(self):
        f = natural_fixture()
        candidate = deepcopy(f['branches'][0]['candidates'][0])
        candidate['id'] = 'extra-unique-candidate'
        f['branches'][0]['candidates'].append(candidate)
        errors = quality.analyze([f])['errors']
        self.assertTrue(any('exactly one candidate' in e for e in errors))

    def test_short_natural_history(self):
        f = natural_fixture()
        f['histories'][0]['messages'] = f['histories'][0]['messages'][:28]
        self.assertTrue(any('15..25' in e for e in quality.analyze([f])['errors']))

    def test_wrong_edge_kind(self):
        f = natural_fixture()
        f['edges'][-1]['kind'] = 'preserve'
        self.assertTrue(any('pair inconsistent' in e for e in quality.analyze([f])['errors']))

    def test_cross_snapshot_group_contamination(self):
        f = natural_fixture()
        other = deepcopy(f)
        other['family_id'] = 'other-family'
        other['split'] = 'test'
        self.assertTrue(any('split_group contamination' in e for e in quality.analyze([f], [other])['errors']))

    def test_block_hash_and_message_multiset(self):
        f = fixture()
        f['status'] = 'draft'
        result = quality.analyze([f])
        self.assertTrue(result['passed'])
        self.assertEqual(len(result['families'][0]['block_message_sha256']), 4)
        f['histories'][0]['messages'][0]['content'] = 'changed'
        errors = quality.analyze([f])['errors']
        self.assertTrue(any('multiset differs' in e for e in errors))
        self.assertTrue(any('hash mismatch' in e for e in errors))

    def test_b6_observed_gate_and_duplicate_audit_id(self):
        f = natural_fixture()
        b = f['branches'][5]
        observation = {'audit_id': 'same', 'decision_id': 'verify', 'decision_correct': True,
                       'evidence_ok': True, 'naturalness': 1.0, 'requested_conditions': [],
                       'feasible_verification': False, 'premature_commitment': True}
        b['candidates'][0]['observed'] = observation
        b['candidates'][1]['observed'] = deepcopy(observation)
        errors = quality.analyze([f])['errors']
        self.assertTrue(any('complete route' in e for e in errors))
        self.assertTrue(any('feasible/premature gate' in e for e in errors))
        self.assertTrue(any('duplicate observed audit_id' in e for e in errors))


if __name__ == '__main__':
    unittest.main()
