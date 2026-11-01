import json
from pathlib import Path
import unittest

import collect_adjudication as collector
import fast_review


class CollectAdjudicationTest(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).parent / 'examples' / 'pilot_audited.jsonl'
        self.family = json.loads(path.read_text().splitlines()[0])
        _, self.payload, self.mapping, self.aliases = fast_review.payloads(self.family)
        by_branch = {b['id']: b for b in self.family['branches']}
        by_candidate = {c['id']: (b, c) for b in self.family['branches'] for c in b['candidates']}
        nodes = [{'n': n, 'actions': list(by_branch[pair[1]]['allowed_decisions']), 'why': '原始独立判断'}
                 for n, pair in self.mapping.items()]
        cs = []
        for alias, cid in self.aliases.items():
            b, c = by_candidate[cid]; good = c['intended']['decision_correct']
            cs.append({'id': alias, 'd': c['intended']['decision_id'], 'c': good, 'g': True,
                       's': .9, 'style': .9, 'v': b['verification_routes'][0] if good and b['verification_routes'] else [],
                       'quotes': [c['text']], 'f': True, 'p': False, 'why': '真实审查结果'})
        self.output = {'nodes': nodes, 'cs': cs, 'blocking': [], 'notes': []}

    def reconstruct(self):
        return collector.reconstruct(self.family, self.output, Path('/evidence/response.json'),
                                     Path('/evidence/response.review_record.json'), self.mapping, self.aliases)

    def test_pass_preserves_actor_inputs_and_uses_third_observations(self):
        final, issues = self.reconstruct()
        self.assertEqual([], issues)
        self.assertEqual(self.family['persona'], final['persona'])
        self.assertEqual(self.family['histories'], final['histories'])
        for old, new in zip(self.family['branches'], final['branches']):
            self.assertEqual(old['visible_observation'], new['visible_observation'])
            self.assertEqual(old['player_turn'], new['player_turn'])
            for a, b in zip(old['candidates'], new['candidates']):
                self.assertEqual((a['text'], a['intended']), (b['text'], b['intended']))
                self.assertTrue(b['observed']['audit_id'].startswith('/evidence/response.json#/cs/'))
        self.assertEqual(self.family['audit']['records'], final['audit']['records'][:-2])

    def test_negative_allowed_by_local_must_remain_pending(self):
        raw = next(x for x in self.output['cs'] if not x['c'])
        cid = self.aliases[raw['id']]
        branch = next(b for b in self.family['branches'] if any(c['id']==cid for c in b['candidates']))
        for n, pair in self.mapping.items():
            if pair[1] == branch['id']:
                next(x for x in self.output['nodes'] if x['n']==n)['actions'].append(raw['d'])
        final, issues = self.reconstruct()
        self.assertIsNone(final)
        self.assertIn('negative_locally_allowed', issues)

    def test_unfaithful_quote_and_b6_cannot_be_repaired_automatically(self):
        raw = next(x for x in self.output['cs'] if x['c'])
        raw['quotes'] = ['不在原文的引文']
        final, issues = self.reconstruct()
        self.assertIsNone(final)
        self.assertIn('unfaithful_quote', issues)
        raw['quotes'] = [next(c['text'] for b in self.family['branches'] for c in b['candidates']
                              if c['id'] == self.aliases[raw['id']])]
        branch = next(b for b in self.family['branches'] if b['kind'] == 'insufficient_evidence')
        cid = next(c['id'] for c in branch['candidates'] if c['intended']['decision_correct'])
        alias = next(a for a, original in self.aliases.items() if original == cid)
        next(x for x in self.output['cs'] if x['id'] == alias)['v'] = []
        final, issues = self.reconstruct()
        self.assertIsNone(final)
        self.assertIn('b6_verification', issues)

    def test_explicit_approximate_dictionary_note_is_pending(self):
        self.output['notes'] = ['当前动作不在词典中，近似标为等待。']
        final, issues = self.reconstruct()
        self.assertIsNone(final)
        self.assertIn('dictionary_mapping_notes', issues)

    def test_candidate_payload_order_may_differ_but_contents_must_match(self):
        altered = dict(self.payload)
        altered['candidates'] = list(reversed(self.payload['candidates']))
        self.assertTrue(collector.candidate_equal(altered, self.payload))
        altered['candidates'] = altered['candidates'][:-1]
        self.assertFalse(collector.candidate_equal(altered, self.payload))


if __name__ == '__main__':
    unittest.main()
