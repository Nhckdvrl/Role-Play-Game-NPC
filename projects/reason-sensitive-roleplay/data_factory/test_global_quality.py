"""Safety regressions for the global quality sentinel; no real process or production I/O."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import watch_global_quality as watch

class RefillTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();root=Path(self.tmp.name);self.run=root/'run';self.out=root/'out';self.proc=root/'proc'
  for p in (self.run,self.out,self.proc):p.mkdir()
  self.patches=[patch.object(watch,'ROOT',root),patch.object(watch,'RUN',self.run),patch.object(watch,'OUT',self.out),patch.object(watch,'Path',side_effect=lambda x:self.proc if x=='/proc' else Path(x)),patch.object(watch.os,'kill',side_effect=ProcessLookupError),patch.object(watch.subprocess,'Popen')]
  for p in self.patches:p.start();self.addCleanup(p.stop)
  self.pop=watch.subprocess.Popen;self.pop.return_value.pid=12345
  (self.run/'production.pid').write_text('99999999');self.argv=['/usr/bin/python3','-u','data_factory/fast_generate.py','--run-dir','runs/train5000-live','--target','5000','--concurrency','8']
  self.write('launch.json',{'argv':self.argv});self.write('exclusions.json',{'1':{'reason':'test'}});self.fs=[{'family_id':str(i)} for i in range(5000)]
  self.addCleanup(self.tmp.cleanup)
 def write(self,name,obj):(self.run/name).write_text(json.dumps(obj))
 def test_maintenance_and_non_target_never_restart(self):
  self.write('state.json',{'stop_reason':'target reached'});(self.run/'STOP_AFTER_DRAIN').write_text('maintenance');watch.refill_if_required(self.fs);self.pop.assert_not_called()
  (self.run/'STOP_AFTER_DRAIN').unlink();self.write('state.json',{'stop_reason':'yield warning'});watch.refill_if_required(self.fs);self.pop.assert_not_called();self.assertTrue((self.out/'NEEDS_ATTENTION').exists())
 def test_target_and_exclusion_restart_validated_argv_and_pid(self):
  self.write('state.json',{'stop_reason':'target reached'});watch.refill_if_required(self.fs)
  self.pop.assert_called_once();self.assertEqual(self.pop.call_args.args[0],self.argv);self.assertEqual((self.run/'production.pid').read_text().strip(),'12345');self.assertTrue((self.run/'launch_history.jsonl').exists())
 def test_explicit_user_budget_never_restarts_old_target(self):
  self.write('state.json',{'stop_reason':'target reached'})
  path=watch.ROOT/'runs/USER_BUDGET_STOP.json';path.parent.mkdir();path.write_text('{}')
  watch.refill_if_required(self.fs);self.pop.assert_not_called()
 def test_bad_target_or_command_rejected(self):
  self.write('state.json',{'stop_reason':'target reached'})
  for argv in (self.argv[:6]+['20000']+self.argv[7:],['/usr/bin/python3','-u','other.py']+self.argv[3:]):
   with self.subTest(argv=argv):
    self.write('launch.json',{'argv':argv})
    with self.assertRaises(ValueError):watch.refill_if_required(self.fs)
  self.pop.assert_not_called()

class EvidenceTest(unittest.TestCase):
 def test_two_reviews_and_verbatim_evidence(self):
  def family(fid,word):return {'family_id':fid,'persona':{'natural_profile':word},'common_visible_context':'场景','branches':[{'visible_observation':'观察','player_turn':'问'}]}
  a,b=family('a','甲事实'),family('b','乙事实');va,vb=watch.visible(a),watch.visible(b);key=watch.pair_key(a,b)
  with tempfile.TemporaryDirectory() as td,patch.object(watch,'OUT',Path(td)):
   (Path(td)/'decisions').mkdir()
   for quoted,want in ((True,'confirmed_duplicate'),(False,'pending')):
    rec={'pair_key':key,'a':'a','b':'b','payload_hashes':[watch.digest(va),watch.digest(vb)],'first':None,'status':'pending'}
    def call(task,*args,**kwargs):return {'status':'success','path':'fake','result':{'results':[{'id':task['payload']['pairs'][0]['id'],'duplicate':True,'confidence':.95,'quote_a':'甲事实' if quoted else '捏造','quote_b':'乙事实','reason':'相同'}]}}
    with patch.object(watch,'dispatch',side_effect=call) as mocked:watch.adjudicate_pending(rec,a,b);self.assertEqual(mocked.call_count,2);self.assertEqual(rec['status'],want)
if __name__=='__main__':unittest.main()
