"""Use a fresh strong author to repair concrete disagreements before re-audit.

The author may edit prose and current visible facts, never observed labels or
audit verdicts. Original drafts, raw calls and all critical reviews are retained.
"""
import argparse
from copy import deepcopy
from pathlib import Path
import json
from produce_pilot import S, array, obj, execute, read, save, task, STYLE
from factory import validate,digest

SCHEMA=obj(patches=array(obj(path=S,old_text=S,new_text=S,reason=S)),unresolved_issues=array(S),repair_summary=S)

def at(root,pointer):
 parts=pointer.strip('/').split('/');parent=root
 for p in parts[:-1]:parent=parent[int(p)] if isinstance(parent,list) else parent[p]
 last=int(parts[-1]) if isinstance(parent,list) else parts[-1]
 return parent,last

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-dir',type=Path,required=True);p.add_argument('--out-run',type=Path,required=True);p.add_argument('--concurrency',type=int,default=4);a=p.parse_args();run=a.run_dir.resolve();out=a.out_run.resolve()
 families=[read(p) for p in sorted((run/'drafts').glob('RCD-*.json'))];blind=read(run/'indices/blind.json');global_index=read(run/'indices/global.json')
 tasks=[]
 for f in families:
  fid=f['family_id'];locals={};cs={}
  for h in f['histories']:
   for b in f['branches']:
    key=fid+'::'+h['id']+'::'+b['id'];locals[h['id']+'::'+b['id']]=blind[key]['result']
    for c in b['candidates']:
     if c['history_id']==h['id']:cs[c['id']]=blind[c['id']]['result']
  payload={'family':f,'local_blind_reviews':locals,'candidate_blind_reviews':cs,'global_critique':global_index[fid]['result']}
  instruction=(STYLE+'\n你是新的故事修订作者，实际模型为Astra。对已经生成且已独立审查的故事族做最小必要的语义修复。'
   '这不是替作者辩护，也不是改审查标签。只能输出字符串字段的JSON pointer替换：path/old_text/new_text/reason。'
   '不得改ID、split、history、blocks、edges、candidates[].intended、observed、audit或状态。'
   '可改persona.natural_profile、decision_contract各项、common_visible_context、branch的观察/玩家话/evidence.text/teacher_scaffold、候选text、inventory的动作描述。'
   '所有决定性信息须自然可见，visible=false证据仍不可作为角色依据。不能把作者结论塞进观察。'
   '修复要点：必要条件不能偷当充分条件；用人物此刻的明确意图、已有意愿和无其他阻碍的事实支持该具体行动，'
   '而不是加一串研究规则或强迫所有人物永远配合。自然写明核验是人物在缺信息时会做的下一步。'
   'B1控制要无真实隐私/创作自主冲突，人物主动在做公开交流或已经自愿答应处理当前小事；负例必须实际拒绝/误导，'
   '不能把回答了问题但审美不同的台词当错。必要时改成公开事实询问，保持原动作ID语义能对应。'
   'B5应自然明确人物已表达愿意采取当前方案且有效条件已满足，排除只是获得许可但并不想行动的问题；'
   '角色已亲自核验过的事实不强制再核验，附带讨论方法不应自动成为另一主决定。'
   'B6四个正确格实际只有每史两条：点名充分缺失路线，提出可做核验，核验前不答应执行；'
   '“确认到账后再成交”是条件性计划，不是现在已成交；但先答应再查是提前承诺。'
   '严格区分未知与不存在，删掉正确示范中未经支持的事实。不要仅因未复述所有已知背景而判依据错误。'
   '四格错误决定要自然可信，不能通过宣称新增许可/核验结果使原来的错行动变成合理。尽量匹配长度与表达。'
   '全局批评可能过度：不要为同一人物想象无限额外理由；但所有实际歧义必须修文本。'
   '重点核对当前family所有候选逐条原意，不盲抄批评；真实审查提取误读可在summary说明，不用篡改正确台词迎合误读。'
   '只补必要事实，不重写无关背景；保留中文自然对话。无法用允许的字符串修复则写unresolved_issues，不假装已解决。'
   '每个patch old_text必须逐字等于原字段全文；path用/branches/0/candidates/0/text等真实路径。')
  tasks.append(task(fid,'semantic_repair_author',payload,instruction,SCHEMA))
 index=execute(tasks,run,a.concurrency,'high','semantic-repair-author','gpt-6-astra')
 reports=[];out.mkdir(parents=True,exist_ok=True)
 for source in families:
  f=deepcopy(source);fid=f['family_id'];r=index[fid]['result'];seen=set()
  for patch in r['patches']:
   path=patch['path']
   if path.startswith('/family/'):path=path[len('/family'):]
   if path in seen:raise ValueError('duplicate repair pointer')
   seen.add(path)
   if any(x in path.split('/') for x in ('intended','observed','audit','histories','blocks','edges','id','family_id','split','split_group_id','status')):raise ValueError('forbidden repair field '+path)
   holder,key=at(f,path)
   if holder[key]!=patch['old_text'] or not isinstance(holder[key],str):raise ValueError('repair source mismatch '+path)
   if not patch['new_text'].strip():raise ValueError('empty repair')
   holder[key]=patch['new_text']
  f['provenance']['prompt_version']='pilot12-v4-semantic-repair';f['provenance']['designer_model']='gpt-6-astra (repair); original gpt-6.1-terra'
  validate(f);save(out/'drafts'/f'{fid}.json',f)
  reports.append({'family_id':fid,'patch_count':len(r['patches']),'unresolved':r['unresolved_issues'],'summary':r['repair_summary'],'original_family_sha256':digest(source),'repaired_family_sha256':digest(f),'raw_author_output':str(Path(index[fid]['path'])/'result.json')})
 save(out/'semantic_repair_records.json',reports)
 for name in ('split_freeze.json','history_quality_review_v3.json','run_config.json'):
  if (run/name).exists():save(out/name,read(run/name))
 save(out/'source_run.json',{'source_run':str(run),'raw_calls_remain_in':str(run/'raw'),'new_raw_calls_saved_in':str(out/'raw'),'reuse_policy':'New independent blind calls for every revised actor input; original labels never copied.'})

if __name__=='__main__':main()
