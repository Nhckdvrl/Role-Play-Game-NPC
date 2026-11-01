"""Native adapter checks using a real draft, without inventing review labels."""
import json, shutil, tempfile, unittest
from pathlib import Path
import native_review

ROOT=Path(__file__).resolve().parents[1]
class NativeReviewTests(unittest.TestCase):
 def setUp(self):
  temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
  self.draft=Path(temporary.name)/'draft.json'
  source=ROOT/'data_factory/examples/fast_audited.jsonl'
  self.draft.write_text(json.dumps(json.loads(source.read_text().splitlines()[0]),ensure_ascii=False))
 def test_export_is_blind_and_pins_exact_source(self):
  with tempfile.TemporaryDirectory() as td:
   out=Path(td)/'export';native_review.export(self.draft,out)
   manifest=json.loads((out/'manifest.json').read_text());local=json.loads((out/'LOCAL.json').read_text());ratings=json.loads((out/'RATINGS.json').read_text())
   self.assertEqual(48,len(manifest['aliases']))
   self.assertEqual(12,len(local['payload']['nodes']))
   self.assertEqual(48,len(ratings['payload']['candidates']))
   self.assertNotIn('aliases',ratings['payload'])
   self.assertEqual(native_review.sha(self.draft.read_bytes()),manifest['source_sha256'])
 def test_assemble_refuses_changed_source_before_reading_reviews(self):
  with tempfile.TemporaryDirectory() as td:
   out=Path(td)/'export';native_review.export(self.draft,out)
   changed=Path(td)/'changed.json';changed.write_bytes(self.draft.read_bytes()+b' ')
   with self.assertRaisesRegex(ValueError,'source changed'):
    native_review.assemble(changed,out,Path(td)/'missing-local',Path(td)/'missing-ratings','reviewer-a','reviewer-b')
 def test_assemble_rejects_tampered_export_payload(self):
  with tempfile.TemporaryDirectory() as td:
   out=Path(td)/'export';native_review.export(self.draft,out)
   req=json.loads((out/'LOCAL.json').read_text());req['payload']['profile']='tampered';(out/'LOCAL.json').write_text(json.dumps(req))
   with self.assertRaisesRegex(ValueError,'exported payload differs'):
    native_review.assemble(self.draft,out,Path(td)/'missing-local',Path(td)/'missing-ratings','reviewer-a','reviewer-b')
 def test_assemble_requires_distinct_reviewers(self):
  with tempfile.TemporaryDirectory() as td:
   out=Path(td)/'export';native_review.export(self.draft,out)
   with self.assertRaisesRegex(ValueError,'reviewers must be distinct'):
    native_review.assemble(self.draft,out,Path(td)/'missing-local',Path(td)/'missing-ratings','same-reviewer','same-reviewer')
if __name__=='__main__':unittest.main()
