import copy
import json
import tempfile
import unittest
from pathlib import Path

from fast_generate import build


def compact():
    pairs = [{'u': '今天先准备材料。', 'a': '好，我来整理。'} for _ in range(15)]
    cases = []
    for i, good in enumerate((['a', 'b'], ['a'], ['c'], ['b'], ['c'], ['a'])):
        bad = next(x for x in ('a', 'b', 'c') if x not in good)
        cases.append({'observation': f'当前事实 {i}', 'player': '现在怎么办？', 'good_ids': good,
                      'bad_id': bad, 'missing': ['condition'] if i == 5 else [],
                      'routes': [['condition']] if i == 5 else [], 'teacher': f'依据 {i}',
                      'responses': ['可以这样做。', '我会这样做。', '我做另一件事。', '我选择另一项。']})
    return {'profile': '我在意自己的承诺。', 'contract': '依据事实选择。', 'common': '我们在工作室。',
            'actions': [{'id': x, 'description': '行动 ' + x} for x in ('a', 'b', 'c')],
            'history_mode': 'natural', 'hc': copy.deepcopy(pairs), 'hr': copy.deepcopy(pairs),
            'blocks': [], 'cases': cases,
            'changes': [{'source': 'B1', 'target': 'B2', 'why': '作者的提议。'}], 'summary': '一项选择。'}


class EdgeReconciliationTests(unittest.TestCase):
    def test_overlapping_proposal_is_recorded_and_only_disjoint_edges_added(self):
        x = compact()
        with tempfile.TemporaryDirectory() as directory:
            record = Path(directory) / 'edge_reconciliation.json'
            f = build(x, 'RCD-train-stream-00002000', 2000, 'test', record)
            info = json.loads(record.read_text())
        self.assertEqual(info['proposals'], x['changes'])
        self.assertEqual(info['rejected'][0]['proposal'], x['changes'][0])
        self.assertGreaterEqual(len(info['added']), 2)
        by_id = {b['id']: set(b['allowed_decisions']) for b in f['branches']}
        for e in f['edges']:
            if e['kind'] == 'change':
                left, right = e['source'].split('::')[1], e['target'].split('::')[1]
                self.assertTrue(by_id[left].isdisjoint(by_id[right]))

    def test_no_disjoint_pairs_are_not_invented(self):
        x = compact()
        for case in x['cases']:
            case['good_ids'] = ['a']
            case['bad_id'] = 'b'
        with tempfile.TemporaryDirectory() as directory:
            record = Path(directory) / 'edge_reconciliation.json'
            with self.assertRaisesRegex(ValueError, 'fewer than two disjoint'):
                build(x, 'RCD-train-stream-00002000', 2000, 'test', record)
            self.assertEqual(json.loads(record.read_text())['added'], [])

class YieldGateTests(unittest.TestCase):
    def test_warn_below_70_but_stop_only_below_50(self):
        from fast_generate import yield_gate
        results = lambda passed: ([{'status': 'audited'}] * passed +
                                  [{'status': 'needs_review'}] * (50 - passed))
        self.assertEqual((yield_gate(results(31))['warning'], yield_gate(results(31))['stop']), (True, False))
        self.assertEqual((yield_gate(results(24))['warning'], yield_gate(results(24))['stop']), (True, True))
        self.assertFalse(yield_gate(results(35))['warning'])
        self.assertEqual(yield_gate(results(31) + [{'status':'needs_review','is_edge_recovery':True}] * 60)['rate'], .62)
        self.assertEqual(yield_gate(results(31) + [{'status':'quota_blocked'}] * 60)['rate'], .62)
        self.assertEqual(yield_gate(results(31) + [{'status':'needs_review','quota_failure':True}] * 60)['rate'], .62)

    def test_import_only_never_starts_model_workers(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        import fast_generate
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            args = SimpleNamespace(seed_snapshot=[], import_snapshot=[], start_index=0,
                                   target=5000, concurrency=64, limit_new=None, import_only=True)
            with patch.object(fast_generate, 'ThreadPoolExecutor') as workers:
                fast_generate.execute(args, run)
            workers.assert_not_called()
            state = json.loads((run/'state.json').read_text())
            self.assertEqual(state['audited_train'], 0)
            self.assertIn('offline_import_only', state['stop_reason'])


if __name__ == '__main__':
    unittest.main()
