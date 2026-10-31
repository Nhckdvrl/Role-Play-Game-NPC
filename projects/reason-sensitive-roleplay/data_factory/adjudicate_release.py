"""Independent strong semantic adjudication, with author intentions removed.

Single-candidate blind reviews remain immutable first-pass annotations. This
stage resolves their extraction errors; it never edits candidate text or copies
generation targets into observed labels.
"""
import argparse
from copy import deepcopy
from pathlib import Path
import json
import random
import subprocess
import sys
from produce_pilot import S,B,N,array,obj,read,save,task,execute
from factory import actor_messages,digest,validate,write_new,jobs

ANNOT=obj(candidate_id=S,decision_id=S,decision_correct=B,evidence_ok=B,naturalness=N,
          requested_condition_ids=array(S),requested_condition_quotes=array(S),
          feasible_verification=B,premature_commitment=B,rationale=S)
SCHEMA=obj(local_information_sufficient=B,history_coherent=B,blocking_issues=array(S),
           nonblocking_observations=array(S),candidates=array(ANNOT))

def tasks_for(families,blind):
 tasks=[]
 for f in families:
  nodes=[];annotations={}
  for h in f['histories']:
   for b in f['branches']:
    cs=[]
    for c in b['candidates']:
     if c['history_id']==h['id']:
      cs.append({'candidate_id':c['id'],'text':c['text']});annotations[c['id']]=blind[c['id']]['result']
    random.Random(digest([f['family_id'],h['id'],b['id']])).shuffle(cs)
    nodes.append({'history_id':h['id'],'node_id':h['id']+'::'+b['id'],
      'messages':actor_messages(f,h,b),'candidates':cs,
      'condition_ids_for_mapping':b['missing_condition_ids']})
  # Sharing full messages is intentional at global adjudication, but no actor sees siblings.
  payload={'decision_inventory':f['decision_inventory'],'nodes':nodes,'first_pass_blind_annotations':annotations}
  instruction=('你是独立语义仲裁员。你没有作者intended标签、allowed_decisions、教师答案、分支类型或chosen/rejected。'
    '每个node是互不接续的反事实分支，只按该node的messages判断，不得从兄弟节点借用证据。'
    'primary盲审可能误读，不能把它当真值；逐条读候选的实际决定、事实依据和核验。'
    '按decision_inventory映射主决定：附带聊天、方法讨论或交接细节不自动变成另一主决定。'
    '人物已经明确亲自核验且表达意愿的事实按已知处理，不机械追加未知阻碍；只有必要条件没有行动意愿则指出真歧义。'
    '决定和依据分别标，台词不必复述全部已知条件，不能因简短就判不忠实。未知与不存在严格区分。'
    '自然度只评表达自然可读、像此人可能说出，不能因决定错而自动扣文风分，平实可以优秀。'
    '只有候选确实请求/安排核验的未知条件才填requested；不要把背景、已知事实或交接细节补进去。'
    'condition_ids_for_mapping只作语义ID映射，quoted条件必须是候选正文的连续原文；没有提到就空。'
    '核验前不无条件执行才是合格核验；“查明满足后再做”的条件性计划不是提前承诺，先答应后查才是。'
    '未发生核验动作feasible_verification=false，不表示该回复其他决定错误。'
    '每条candidate_id恰好一条annotation，给简短可审计rationale。真实样本歧义/主线事实冲突列blocking_issues；'
    '普通措辞、微小节奏偏好列nonblocking，不为迎合作者消除真实歧义，也不为挑错创造额外事实。'
    'history_coherent同时检查自然交流和上下文状态：须围绕真实目的承接，不能是为凑轮数逐件问物品、反复无动机索取或破坏；'
    '两史最后几轮须分别保持实际合作与不同意的近期姿态，不能一律转回合作收尾。'
    '检查未结的相关承诺/资源/离场；独立已结块间正常话题跳转不是自动失败。')
  schema=deepcopy(SCHEMA);schema['properties']['candidates'].update(minItems=48,maxItems=48)
  tasks.append(task(f['family_id'],'semantic_adjudication',payload,instruction,schema))
 return tasks

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-dir',type=Path,required=True);p.add_argument('--concurrency',type=int,default=4);p.add_argument('--no-local-repair',action='store_true');a=p.parse_args();run=a.run_dir.resolve()
 if (run/'RELOAD_CONTROLLER').exists() or (run.parent.parent/'RELOAD_CONTROLLER').exists():
  print('Controller reload requested at a completed model-call boundary; raw outputs are preserved.',flush=True)
  raise SystemExit(75)
 families=[read(p) for p in sorted((run/'drafts').glob('RCD-*.json'))]
 if not families:raise ValueError('no complete drafts')
 blind=read(run/'indices/blind.json')
 for f in families:
  for h in f['histories']:
   for b in f['branches']:
    payload={'messages':actor_messages(f,h,b)}
    for c in b['candidates']:
     if c['history_id']==h['id']:
      meta=read(Path(blind[c['id']]['path'])/'metadata.json')
      if meta['payload_sha256']!=digest({**payload,'candidate_text':c['text']}):raise ValueError('stale candidate blind review')
 tasks=tasks_for(families,blind)
 index=execute(tasks,run,a.concurrency,'high','adjudication-'+digest(tasks)[:12],'gpt-6-astra')
 alias=run/'indices/adjudication.json'
 if alias.exists():save(run/'indices'/f'adjudication-prior-{digest(read(alias))[:12]}.json',read(alias))
 alias.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 accepted=[];pending=[];reports=[]
 for source in families:
  f=deepcopy(source);fid=f['family_id'];raw=index[fid]['result'];annotations={x['candidate_id']:x for x in raw['candidates']}
  expected={c['id'] for b in f['branches'] for c in b['candidates']}
  if set(annotations)!=expected or len(raw['candidates'])!=len(expected):raise ValueError('incomplete adjudication')
  issues=list(raw['blocking_issues'])
  if not raw['local_information_sufficient']:issues.append('local information insufficient')
  if not raw['history_coherent']:issues.append('history state conflict')
  disagreements=[]
  for b in f['branches']:
   for c in b['candidates']:
    x=annotations[c['id']];old=blind[c['id']]['result'];audit=str(Path(index[fid]['path'])/'result.json')+'#/candidates/'+str(raw['candidates'].index(x))
    c['observed']={'audit_id':audit,'decision_id':x['decision_id'],'decision_correct':x['decision_correct'],
      'evidence_ok':x['evidence_ok'],'naturalness':x['naturalness'],'requested_conditions':x['requested_condition_ids'],
      'feasible_verification':x['feasible_verification'],'premature_commitment':x['premature_commitment']}
    if old['decision_supported']!=x['decision_correct'] or old['evidence_ok']!=x['evidence_ok']:
     disagreements.append({'candidate_id':c['id'],'blind_decision_correct':old['decision_supported'],'adjudicated_decision_correct':x['decision_correct'],
       'blind_evidence_ok':old['evidence_ok'],'adjudicated_evidence_ok':x['evidence_ok'],'reason':x['rationale']})
    if x['decision_id'] not in f['decision_inventory']:issues.append(c['id']+':unknown decision')
    if x['decision_correct']!=c['intended']['decision_correct']:issues.append(c['id']+':actual grid differs from intended')
    if x['decision_correct']!=(x['decision_id'] in b['allowed_decisions']):issues.append(c['id']+':author allowed decision disagreement')
    if x['decision_correct'] and not x['evidence_ok']:issues.append(c['id']+':correct exemplar has ungrounded basis')
    if x['naturalness']<.7:issues.append(c['id']+':low expression naturalness')
    # B6 has an authored closed route vocabulary. Other branches can naturally
    # propose additional checks; their quoted extraction is an open annotation.
    if b['kind']=='insufficient_evidence' and not set(x['requested_condition_ids'])<=set(b['missing_condition_ids']):issues.append(c['id']+':unknown requested condition')
    if x['requested_condition_ids'] and not x['requested_condition_quotes']:issues.append(c['id']+':condition lacks textual evidence')
    if any(not q or q not in c['text'] for q in x['requested_condition_quotes']):issues.append(c['id']+':condition quote not in candidate')
    if b['kind']=='insufficient_evidence' and x['decision_correct']:
     if not any(set(route)<=set(x['requested_condition_ids']) for route in b['verification_routes']) or not x['feasible_verification'] or x['premature_commitment']:
      issues.append(c['id']+':B6 insufficient verification')
  passed=not issues;f['status']='audited' if passed else 'needs_review'
  f['audit']={'local_blind_review':'pass' if raw['local_information_sufficient'] else 'fail','global_review':'pass' if passed else 'fail','human_review':'not_sampled',
   'records':[str(run/'indices/blind.json'),str(Path(index[fid]['path'])/'result.json')]}
  validate(f);save(run/'adjudicated'/f'{fid}.json',f)
  (accepted if passed else pending).append(f)
  reports.append({'family_id':fid,'status':f['status'],'issues':issues,'nonblocking':raw['nonblocking_observations'],
    'first_pass_adjudication_disagreements':disagreements,'adjudication_path':index[fid]['path']})
 write_new(run/'families.jsonl',accepted);write_new(run/'needs_review.jsonl',pending);save(run/'review_decisions.json',reports)
 by_stage={s:[] for s in ('actor','local_blind','candidate_auditor','teacher')}
 for f in accepted:
  for job in jobs(f,True):by_stage[job['stage']].append(job)
 for stage,rows in by_stage.items():write_new(run/'jobs'/f'{stage}.jsonl',rows)
 print(json.dumps({'audited':len(accepted),'needs_review':len(pending)},ensure_ascii=False),flush=True)
 if pending and not a.no_local_repair:
  subprocess.run([sys.executable,str(Path(__file__).with_name('curate_shard.py')),'--run-dir',str(run),
                  '--concurrency',str(min(8,a.concurrency)),'--no-initial-adjudication'],check=True)

if __name__=='__main__':main()
