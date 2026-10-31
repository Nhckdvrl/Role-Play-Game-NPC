"""Append a short, natural, closed disagreement to weak resistant histories."""
from copy import deepcopy
from pathlib import Path
import argparse
from produce_pilot import HISTORY, STYLE, execute, read, save, task, check_messages
from factory import digest, validate

PURPOSES={
3:'候船者想挪候船椅改变挡风位置，阿渡希望保留通道与原有布局；讨论两种更小的挪法，均未采纳。不能再次涉及破坏物品、借船或运输承诺。',
4:'玩家想把已归位工具重新摆成对称形状拍照，阿岑偏爱现在顺手的摆法。讨论简化摆拍的建议，仍保留原摆放。不谈修缆代劳或技能交换。',
6:'玩家对自己带来的花束提出更花哨的包装建议，佟禾从花色搭配出发不赞成，讨论两种细节仍保持原有包装。不免费取走摊上材料，不谈展示权交易。',
10:'同事想在已经对好的公开片头里加一个转场音效，沈菱觉得破坏当前节奏；同事提出缩短/压低音量等具体改法，沈菱仍不采用，片头保持原样。不谈私人录音、授权或收工。'}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-dir',type=Path,required=True);a=p.parse_args();run=a.run_dir.resolve()
 families=[read(p) for p in sorted((run/'drafts').glob('RCD-*.json'))]
 tasks=[]
 for f in families:
  seed=f['provenance']['seed']
  if seed not in PURPOSES:continue
  h=next(h for h in f['histories'] if h['id']=='hr')
  payload={'persona':f['persona']['natural_profile'],'recent_messages':h['messages'][-12:],
           'scene_purpose':PURPOSES[seed],'exchanges':3}
  schema=deepcopy(HISTORY);schema['properties']['messages'].update(minItems=6,maxItems=6)
  tasks.append(task(f['family_id'],'posture_tail_repair',payload,
      STYLE+'\n为现有对话自然续写3往返6消息，user起assistant终，只写新增部分。'
      '最后三轮围绕一个具体的非主线小分歧，角色都维持拒绝原提议的立场；'
      '玩家每次有新的具体考虑，不复读施压，也不恶意。最后不实施提案，双方仍在场，小事已定。'
      '不新增许可、当前主线证据、承诺、信任或资源变动，不让角色机械背人设。',schema))
 index=execute(tasks,run,4,'medium','recent-posture-repair')
 records=[]
 for f in families:
  seed=f['provenance']['seed'];fid=f['family_id']
  if seed in PURPOSES:
   save(run/'drafts_before_posture_repair'/f'{fid}.json',f)
   h=next(h for h in f['histories'] if h['id']=='hr');old=digest(h['messages']);tail=index[fid]['result']['messages'];check_messages(tail,3)
   h['messages']+=tail;h['control_note']+=' 最近三轮自然分歧经独立重审。'
   f['provenance']['prompt_version']='pilot12-v3-recent-posture'
   # This is a versioned context revision; original candidate texts and all prior audit inputs remain saved.
   target=run/'drafts'/f'{fid}.json';target.write_text(__import__('json').dumps(f,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
   records.append({'family_id':fid,'history_id':'hr','old_messages_sha256':old,'new_messages_sha256':digest(h['messages']),
      'new_exchanges':len(h['messages'])//2,'audit_requirement':'Reaudit all changed actor inputs before global approval.'})
  validate(f)
  packet={k:f[k] for k in ['persona','common_visible_context','history_mode','blocks','histories']};packet['persona']={'natural_profile':f['persona']['natural_profile']}
  save(run/'history_review_payloads_v3'/f'{fid}.json',packet)
 save(run/'recent_posture_revision_records.json',records)

if __name__=='__main__':main()
