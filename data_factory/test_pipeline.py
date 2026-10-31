from collections import Counter
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from factory import validate,assemble,jobs,actor_messages,write_new
from make_smoke import fixture
from scoring import EvaluationRequest,EvaluationReport,compose,cache_key

class PipelineTests(unittest.TestCase):
    def test_schema_and_counts(self):
        r=validate(fixture())
        self.assertEqual(r['nodes'],12)
        self.assertEqual(r['candidate_instances'],48)
        self.assertEqual(r['unique_candidate_texts'],24)
        self.assertFalse(r['semantic_audited'])

    def test_exact_block_permutation(self):
        f=fixture(); histories=f['histories']
        bag=lambda h: Counter(json.dumps(m,ensure_ascii=False,sort_keys=True) for m in h['messages'])
        self.assertEqual(bag(histories[0]),bag(histories[1]))
        histories[1]['messages'][0]['content']+='新增事实'
        with self.assertRaises(ValueError): validate(f)

    def test_duplicate_block_order_rejected(self):
        f=fixture()
        with self.assertRaises(ValueError): assemble(f['blocks'],['E0','E0','E1','E2'])

    def test_b6_needs_specific_routes(self):
        f=fixture(); f['branches'][-1]['verification_routes']=[]
        with self.assertRaises(ValueError): validate(f)

    def test_expected_labels_are_not_audit(self):
        f=fixture(); f['status']='audited'
        f['audit'].update(local_blind_review='pass',global_review='pass',records=['fake-example-reference'])
        with self.assertRaises(ValueError): validate(f)

    def test_routing_does_not_leak_oracle(self):
        f=fixture(); f['persona']['decision_contract']=['ORACLE_SENTINEL']
        f['branches'][0]['teacher_scaffold']='TEACHER_SENTINEL'
        f['branches'][0]['evidence'].append({'id':'hidden','text':'HIDDEN_SENTINEL','visible':False})
        all_jobs=list(jobs(f,True))
        for j in all_jobs:
            if j['stage']!='teacher':
                text=json.dumps(j['payload'],ensure_ascii=False)
                for token in ('ORACLE_SENTINEL','TEACHER_SENTINEL','HIDDEN_SENTINEL','allowed_decisions','intended'):
                    self.assertNotIn(token,text)
        self.assertEqual(len([j for j in all_jobs if j['stage']=='candidate_auditor']),48)

    def test_test_split_does_not_export_teachers(self):
        f=fixture(); f['split']='test'
        self.assertNotIn('teacher',{j['stage'] for j in jobs(f,True)})

    def test_write_is_idempotent_not_destructive(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.jsonl'; write_new(p,[{'x':1}]); write_new(p,[{'x':1}])
            with self.assertRaises(FileExistsError): write_new(p,[{'x':2}])

    def test_b6_scoring(self):
        req=EvaluationRequest('x',[],['verify'],'请给我有效通告。','insufficient_evidence',[['notice']],['rule'],[])
        good=EvaluationReport('x','verify',1,1,.8,('notice',),1,False,.9)
        self.assertEqual(compose(req,good).q,1)
        self.assertEqual(compose(req,replace(good,requested_conditions=())).q,0)
        self.assertEqual(compose(req,replace(good,premature_commitment=True)).q,0)
        self.assertEqual(compose(req,replace(good,feasible_verification=0)).q,0)
        with self.assertRaises(ValueError): compose(req,replace(good,status='service_error'))
        self.assertNotEqual(cache_key(req,'v1'),cache_key(req,'v2'))

if __name__=='__main__': unittest.main()
