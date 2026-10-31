"""Revise history prose from an independent review, preserving original artifacts.

Candidate texts are reused as counterfactual candidates and fully reaudited on
the revised context. Their original generation input remains available in raw.
"""
import argparse
from copy import deepcopy
from pathlib import Path
import json
from produce_pilot import HISTORY, STYLE, execute, obj, array, S, read, save, task, check_messages
from factory import assemble, digest, validate

PURPOSES={
 1:'一名访客在工作室查看釉色样片，比较拍摄光线，最后整理自己的参观记录。只围绕这三件相邻小事，不讨论当前作品的出售或署名。',
 3:'一名候船者在渡口看告示板、辨认候船位置和调整自己的等候方式。不要连续请求破坏公共设施，不讨论船只借出或乐器运输安排。',
 4:'访客帮忙整理已完成的小修用具、讨论物品摆放和歇脚位置。拒绝可来自阿岑个人习惯，不再提出修缆代劳或技能交换，不让访客离开现场。',
 6:'玩家带着自己的花束来请教简单的配色和包装，换一次零钱，再讨论价签是否易读。不涉及展位权利和当前交易，也不连续索取免费物品。',
 8:'排程同事同黎岚整理过去的印样与工作台照明，讨论如何标记旧资料。同事始终不是学徒，不讲当前学徒的请求，不以教学条款回应所有小事。',
10:'两位同事整理本期已公开的片头、字幕和节目单，讨论剪辑节奏与设备收纳。不讨论任何私人录音或其授权，不说收工或让玩家离开。'}

EVENT_FIXES={
 (0,'R2'):'玩家想询问一只未在场的旧音箱二手售价。型号与成色都说不清，沈岚解释这样的范围太宽，拒绝本次估价；玩家问怎样描述成色，得到一条简短说明。不留下替人估价的承诺。',
 (0,'C3'):'沈岚手持一张器材清单原稿，玩家手持对应印件，两人核对三个分类的顺序并发现顺序相同；问答应有实际参照，最后确认结束，不接收器材或货款。',
 (2,'R1'):'玩家想只凭海边一句传闻猜当天浪高，研究员拒绝报数并解释缺观测；玩家改问一般看什么记录，得到简短回答。不能新增当前异常的原始数据或复验事实。',
 (2,'R3'):'玩家嫌墙上已经印好的学术海报标题太长，想为了临时口头介绍重新印一张。研究员不同意为这个用途重印，建议讲解时口头用短称，两人把短称讲清后结束。不要添新长期任务。',
 (9,'R1'):'新来的志愿者建议将已经按船位标号的空箱改按颜色摆，方便自己记。领队说明船位标签是队员归还的参照，拒绝重排；双方用一个箱子核对读标签的方法，保持原分类，事项结束。',
 (9,'R3'):'白板边框有一道水印，但板上训练说明仍清楚。玩家提议整板湿擦并重抄，领队拒绝擦掉清楚的说明，只当场擦净边框；结束小事，不改变训练时段或队员安排。',
 (11,'C1'):'两人给昨晚已经录下的一小段旋律起个便于查找的名称，比较两个具体名称后定下一个，事项结束。它与今天的热身不是同一段。',
 (11,'R1'):'玩家想把练习记录里具体的曲式名称改成夸张押韵口号，乐手觉得以后查找会不方便，拒绝改写；玩家确认原名对应哪个节奏后结束，不涉及当前搭档或拟演段落。',
 (11,'R2'):'凳面已擦净，玩家想再喷一点自己的浓香喷雾。乐手不喜欢那个味道，婉拒；玩家收起喷雾，双方把凳子摆稳，物品归位，事项结束。'}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-dir',type=Path,required=True);p.add_argument('--concurrency',type=int,default=8);a=p.parse_args();run=a.run_dir.resolve()
 original=run/'drafts_v1'
 if not original.exists():(run/'drafts').rename(original)
 families=[read(x) for x in sorted(original.glob('RCD-*.json'))]
 if len(families)!=12:raise ValueError('pilot roster must have 12 complete generated drafts')
 reviews={x['family_id']:x for x in read(run/'history_quality_review.json')['families']}
 briefs=read(run/'normalized_briefs.json');tasks=[];positions={}
 style=read(run/'style_guidance.json')['principles']
 for f in families:
  fid=f['family_id'];seed=f['provenance']['seed']
  if f['history_mode']=='exact_permutation':
   for i,b in enumerate(f['blocks']):
    exchanges=(2,4,3,3,2,4)[i]
    event=EVENT_FIXES.get((seed,b['id']),next(x['event'] for x in briefs[fid]['blocks'] if x['id']==b['id']))
    payload={'persona':f['persona']['natural_profile'],'event':event,'posture':b['posture'],'exchanges':exchanges,
             'writing_guidance':style,'source_messages':b['messages'],
             'quality_feedback':[x for x in reviews[fid]['findings'] if b['id'] in x['location']]}
    instruction=(STYLE+'\n请重写这个独立小事件，严格exchanges个往返、user起assistant终。'
       '只写这一块，不能提其他块或当前主线。每次玩家追问要有新的具体意图，不连续重复催促。'
       '拒绝块可以解释理由、澄清或提供别法，最后保留该局部拒绝；合作块完成一次具体帮助。'
       '不要机械复述已归位/事情结束；用自然对话或一处简短动作闭合。'
       '既不留下未结借用品和承诺，也不新增主线资源、许可、证据、信任变化。'
       '事件时间锚定于本块，不以“刚才那段”暗指别块；source只作待改原文，不必须保留句子。')
    key=fid+'::'+b['id'];positions[key]=(exchanges,b['id'])
    schema=deepcopy(HISTORY);schema['properties']['messages'].update(minItems=exchanges*2,maxItems=exchanges*2)
    tasks.append(task(key,'block_quality_rewrite',payload,instruction,schema))
  else:
   for h in f['histories']:
    payload={'persona':f['persona']['natural_profile'],'scene_purpose':PURPOSES[seed],
             'recent_posture':h['posture'],'exchanges':18,'source_messages':h['messages'],
             'writing_guidance':style,'quality_feedback':reviews[fid]['findings']}
    instruction=(STYLE+'\n重写当前这一段历史，严格18往返36条消息、user起assistant终，不生成另一段。'
       '整段围绕scene_purpose的两三个相邻事项自然发展，每个追问有具体目的；不要18个跳转话题。'
       '合作近期史以多次帮忙与最近合作为主；拒绝近期史以有动机的意见分歧、选择不同方案和边界为主，'
       '可以有正常合作，不能为了拒绝把玩家写成不断破坏物品或索取利益的人。'
       '不同意后允许玩家修正需求、确认理解；别每次都重复施压，不刻意复述人物契约。'
       '全部小事在末尾有自然闭合，借用品归还；双方仍在场，后面可以谈别事。'
       '不新增当前主线交易/授权/技能/承诺证据，不让历史提早解决主线，也不增强亲密信任。')
    schema=deepcopy(HISTORY);schema['properties']['messages'].update(minItems=36,maxItems=36)
    key=fid+'::'+h['id'];positions[key]=(18,h['id'])
    tasks.append(task(key,'natural_quality_rewrite',payload,instruction,schema))
 index=execute(tasks,run,a.concurrency,'medium','history-quality-rewrite')
 records=[]
 for source in families:
  f=deepcopy(source);fid=f['family_id'];oldhash=digest(f['histories'])
  if f['history_mode']=='exact_permutation':
   for b in f['blocks']:
    key=fid+'::'+b['id'];messages=index[key]['result']['messages'];check_messages(messages,positions[key][0]);b['messages']=messages
   for h in f['histories']:h['messages']=assemble(f['blocks'],h['block_order'])
  else:
   for h in f['histories']:
    messages=index[fid+'::'+h['id']]['result']['messages'];check_messages(messages,18);h['messages']=messages
  for h in f['histories']:h['control_note']+=' 已根据独立自然度审查重写；待以本上下文盲审全部候选。'
  f['provenance']['prompt_version']='pilot12-v2-naturalness'
  validate(f);save(run/'drafts'/f'{fid}.json',f)
  packet={k:f[k] for k in ['persona','common_visible_context','history_mode','blocks','histories']};packet['persona']={'natural_profile':f['persona']['natural_profile']}
  save(run/'history_review_payloads_v2'/f'{fid}.json',packet)
  records.append({'family_id':fid,'original_history_sha256':oldhash,'revised_history_sha256':digest(f['histories']),
    'candidate_provenance':'Texts retained from original node rendering; all independent audits use revised actor context. No decision-relevant fact changed.',
    'original_draft':str(original/f'{fid}.json'),'rewrite_index':str(run/'indices'/'history-quality-rewrite.json')})
 save(run/'history_revision_records.json',records)
 print('12 revised complete drafts ready for independent candidate audit',flush=True)

if __name__=='__main__':main()
