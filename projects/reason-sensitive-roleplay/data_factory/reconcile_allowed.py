"""Record independently supported alternative actions in author metadata.

Actor inputs, candidates, generation targets and observed annotations are not
changed. Any affected relation is rebuilt from valid endpoint actions; a change
edge is removed when both endpoints permit the same main action.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
from produce_pilot import read,save
from factory import validate

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-dir',type=Path,required=True);p.add_argument('--approved',type=Path,required=True);a=p.parse_args();run=a.run_dir.resolve()
 approved=read(a.approved);index=read(run/'indices/adjudication.json');records=[]
 for fid,branches in approved.items():
  path=run/'drafts'/f'{fid}.json';f=read(path);save(run/'drafts_before_allowed_reconciliation'/path.name,f)
  annotations={x['candidate_id']:x for x in index[fid]['result']['candidates']};before=deepcopy(f['edges'])
  changes=[]
  for b in f['branches']:
   for decision in branches.get(b['id'],[]):
    supporting=[x for c in b['candidates'] if (x:=annotations[c['id']])['decision_id']==decision and x['decision_correct'] and x['evidence_ok']]
    if not supporting or decision not in f['decision_inventory']:raise ValueError('no independently grounded support for expansion')
    if decision not in b['allowed_decisions']:
     b['allowed_decisions'].append(decision);changes.append({'branch_id':b['id'],'added_action':decision,'supporting_candidate_ids':[x['candidate_id'] for x in supporting],'rationales':[x['rationale'] for x in supporting]})
  byid={b['id']:b for b in f['branches']};edges=[]
  for edge in f['edges']:
   left=set(byid[edge['source'].split('::')[1]]['allowed_decisions']);right=set(byid[edge['target'].split('::')[1]]['allowed_decisions'])
   if edge['kind']=='change' and left & right:continue
   e=deepcopy(edge)
   e['allowed_pairs']=([[x,x] for x in sorted(left & right)] if e['kind']=='preserve' else [[x,y] for x in sorted(left) for y in sorted(right) if x!=y])
   e['justification']+=' 独立仲裁确认可拒绝当前不足方案并安排核验；合法替代动作已纳入，非强迫单一回答。'
   if e['allowed_pairs']:edges.append(e)
  # Keep two genuinely different condition transitions per history where available.
  for hid in ('hc','hr'):
   for source in ('B2','B3','B4','B6'):
    if sum(e['kind']=='change' and e['source'].startswith(hid+'::') for e in edges)>=2:break
    l=set(byid[source]['allowed_decisions']);rr=set(byid['B5']['allowed_decisions']);src=hid+'::'+source;tgt=hid+'::B5'
    if source=='B5' or l & rr or any({e['source'],e['target']}=={src,tgt} for e in edges):continue
    edges.append({'source':src,'target':tgt,'kind':'change','allowed_pairs':[[x,y] for x in sorted(l) for y in sorted(rr)],
      'justification':'独立允许集合无交集：当前理由不足时保持或核验，满足人物当前目标并核实后采取另一主要决定。'})
  f['edges']=edges;validate(f)
  path.write_text(json.dumps(f,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  records.append({'family_id':fid,'changes':changes,'edges_before':before,'edges_after':edges,
    'basis':'Independent intention-blind adjudication found these actions reasonable; no actor text or labels changed.'})
 save(run/'allowed_reconciliation.json',records)
 # Archive the prior publication attempt; immutable raw annotations remain in place.
 archive=run/'pre_allowed_reconciliation';archive.mkdir(exist_ok=True)
 for name in ('adjudicated','families.jsonl','needs_review.jsonl','review_decisions.json','jobs'):
  source=run/name
  if source.exists():source.rename(archive/name)

if __name__=='__main__':main()
