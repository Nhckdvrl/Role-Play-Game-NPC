import itertools
import math
import unittest
from family_reward import (Score,Edge,weights,score_family,conditional_scores,
                           advantages,recovery_diagnostics)

G=Score('accept',1,1,.8)
R=Score('reject',1,1,.5)
BAD=Score('reject',0,1,1)

class RewardTests(unittest.TestCase):
    def test_wrong_style_cannot_win(self):
        self.assertEqual(score_family({'x':BAD},[]),0)
        self.assertGreater(score_family({'x':G},[]),0)

    def test_degree_weights(self):
        edges=[Edge('a','b','preserve',(('accept','accept'),)),
               Edge('a','c','preserve',(('accept','accept'),)),
               Edge('c','d','preserve',(('accept','accept'),))]
        self.assertEqual(weights(list('abcd'),edges),[.375,.25,.375])
        self.assertAlmostEqual(sum(weights(list('abcd'),edges)),1)

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError): Score('x',float('nan'),1,1)
        with self.assertRaises(ValueError): weights(['a','b'],[Edge('a','a','preserve',(('x','x'),))])
        with self.assertRaises(ValueError): advantages({'a':[G]},[])
        with self.assertRaises(ValueError): score_family({'a':G},[],alpha=.5)

    def test_marginal_matches_enumeration(self):
        edges=[Edge('a','b','change',(('accept','reject'),)),
               Edge('b','c','preserve',(('reject','reject'),))]
        pools={'a':[G,BAD],'b':[R,BAD,G],'c':[R,G]}
        anchors={'a':[G],'b':[R],'c':[R]}
        for mode,alpha in itertools.product(['degree','uniform'],[0,.3]):
            kw={'mode':mode,'alpha':alpha,'anchors':anchors}
            conditional=conditional_scores(pools,edges,**kw)
            for node,values in pools.items():
                others=[n for n in pools if n!=node]
                brute=[]
                for value in values:
                    scores=[]
                    for combo in itertools.product(*(pools[n] for n in others)):
                        outputs=dict(zip(others,combo)); outputs[node]=value
                        scores.append(score_family(outputs,edges,**kw))
                    brute.append(sum(scores)/len(scores))
                for i in range(1,len(values)):
                    self.assertAlmostEqual(conditional[node][i]-conditional[node][0],brute[i]-brute[0],places=12)

    def test_zero_signal_needs_separate_auxiliary(self):
        pools={'a':[BAD,BAD],'b':[BAD,BAD]}
        e=[Edge('a','b','preserve',(('accept','accept'),))]
        before=[id(x) for x in pools['a']]
        self.assertEqual(advantages(pools,e,alpha=.5,anchors={'a':[G],'b':[G]}),{'a':[0,0],'b':[0,0]})
        self.assertTrue(recovery_diagnostics(pools)['a']['all_fail'])
        self.assertEqual(before,[id(x) for x in pools['a']])

    def test_anchor_supports_live_node_with_failed_neighbor(self):
        pools={'a':[G,BAD],'b':[BAD,BAD]}
        e=[Edge('a','b','preserve',(('accept','accept'),))]
        a0=advantages(pools,e,alpha=0)
        a1=advantages(pools,e,alpha=.5,anchors={'a':[G],'b':[G]})
        self.assertGreater(a1['a'][0],a0['a'][0])
        self.assertEqual(a1['b'],[0,0])

    def test_score_function_and_rloo_gradients(self):
        # Exact expectation over TWO independent samples per node, not a
        # stochastic one-run claim. Compare shared-parameter score gradient.
        e=[Edge('a','b','change',(('accept','reject'),))]
        choices={'a':[BAD,G],'b':[BAD,R]}; anchors={'a':[G],'b':[R]}
        def prob(theta): return 1/(1+math.exp(-theta))
        for alpha in (0,.4):
            kw={'alpha':alpha,'anchors':anchors}
            def expected(theta):
                p=prob(theta); total=0
                for i,j in itertools.product((0,1),repeat=2):
                    pr=(p if i else 1-p)*(p if j else 1-p)
                    total+=pr*score_family({'a':choices['a'][i],'b':choices['b'][j]},e,**kw)
                return total
            theta=.2; p=prob(theta); eps=1e-5
            numeric=(expected(theta+eps)-expected(theta-eps))/(2*eps)
            estimated=0
            for ids in itertools.product((0,1),repeat=4):
                pr=math.prod(p if i else 1-p for i in ids)
                pools={'a':[choices['a'][i] for i in ids[:2]],'b':[choices['b'][i] for i in ids[2:]]}
                adv=advantages(pools,e,**kw)
                grad=sum((ids[k]-p)*adv['a' if k<2 else 'b'][k%2]/2 for k in range(4))
                estimated+=pr*grad
            self.assertAlmostEqual(estimated,numeric,places=8)

if __name__=='__main__': unittest.main()
