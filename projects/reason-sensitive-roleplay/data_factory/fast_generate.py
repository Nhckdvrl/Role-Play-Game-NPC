#!/usr/bin/env python3
"""Persistent family-level generation and independent review; no model code execution."""
import argparse
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from copy import deepcopy
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import time
import uuid
from jsonschema import Draft202012Validator
from factory import validate, digest, assemble
from fast_review import review
from agent_dispatch import dispatch, QUOTA_MARKER

class QuotaExhausted(RuntimeError):pass

MODEL='gpt-6.1-terra'
S={'type':'string'}
def arr(x, minimum=None, maximum=None):
 d={'type':'array','items':x}
 if minimum is not None:d['minItems']=minimum
 if maximum is not None:d['maxItems']=maximum
 return d
def obj(**kw): return {'type':'object','properties':kw,'required':list(kw),'additionalProperties':False}
PAIR=obj(u=S,a=S)
BLOCK=obj(id={'type':'string','enum':['C1','C2','C3','R1','R2','R3']},pairs=arr(PAIR,2,3))
CASE=obj(observation=S,player=S,good_ids=arr(S),bad_id=S,missing=arr(S),routes=arr(arr(S)),teacher=S,responses=arr(S,4,4))
SCHEMA=obj(profile=S,contract=S,common=S,actions=arr(obj(id=S,description=S),2),history_mode={'type':'string','enum':['natural','exact_permutation']},
 hc=arr(PAIR,0,15),hr=arr(PAIR,0,15),blocks=arr(BLOCK,0,6),cases=arr(CASE,6,6),changes=arr(obj(source=S,target=S,why=S),2),summary=S)
INSTRUCTION='''先列出当前完整合理动作集合：对于可选奖励，如果接受和拒绝均合理，两者均加入good_ids，不能把另一个合理选项作为负例。B4的bad_id必须实质违背可见核心目标或明确事实，而非仅仅拒绝可选好处；奖励可以改变策略，不要将软偏好悄悄变成唯一契约。导演用两个反例自检每个负格：若有合理解释则更换为真正错误行动，不修改独立审查标签。exact_permutation每块涉及不同物件或互不影响的已结事项，不在多块复用碗、勺等同一状态；common仅放与任何branch动态事实都不冲突的静态事实。人设通过经历与欲望体现偏好，避免if-then操作规章或穷举答案，允许不完美的个性。历史应有自然追问和承接，不要写成15项便利问答。错误角色候选不要自曝“包括明确不愿公开内容”或“我知道这样违背”等明显负例标记。原创一个中文角色扮演故事族，只输出符合schema的JSON。history_mode必须严格等于输入的history_mode_requested。自然、有具体人物欲望、当下目标和同一场景的真实互动，不能仅靠换人名职业改模板。profile用3–5句自然背景、目标与在乎的先后，演员可由其与场景推导决定；contract给导演写机制，不放进演员可见文本。common描述当下场景。actions为中性动作字典，至少两个、ID简短英文。history_mode用natural时hc、hr各15个连续u/a往返，围绕同一生活目标和2–3件相邻小事，有追问承接修复；hc最近事项合作较多、hr最近事项拒绝较多，拒绝后礼貌收尾仍算拒绝。两史不改变当前分支的关键资源、许可、信任、承诺或知识。用exact_permutation时仅blocks包含C1 C2 C3 R1 R2 R3，每块2–3个u/a往返，六块合计15往返，各闭合且互不影响；hc/hr置空。不要清单式盘问或恶意重复。cases严格按routine、pressure、invalid_reason、generic_incentive、valid_reason、insufficient_evidence排列6项；observation只写当前可见原始事实，不写作者判词或分支编号，player是玩家当前请求，所有决定必要事实均必须可见；teacher为简短导演依据。good_ids是当前合理主要动作ID数组，bad_id是截然错误的实质动作ID且不得在good_ids，所有ID来自actions。responses恰好四条：正确角色表达、正确平实自然、错误角色表达、错误平实自然；正误同风格长度尽量接近，约40字，真正错误体现在行动，勿自曝评分、条件或导演意图。前两条都执行good_ids第一个动作，后两条都执行bad_id。前五项missing和routes为空数组；第六项missing列必要未知条件ID，routes是可行核验路径列表（每条为缺失ID数组），两条正确回答必须具体询问或安排核验该路径，不提前承诺。最后changes列至少两项可信不同case之间的动作变化，用source/target填B1至B6，决定必须不相容且正向可解释；不要把两个均可核验的节点硬标变化。动机可自利、个人体验、情面、旧怨、名誉，B4可以被奖励说服，B5可改变方案或停手，不要人人是守门人，不要重复以净收益价格底线为核心的套利故事。summary写目标、核心冲突、有效事实和行动的简短机制摘要，用于去重。任何普通合理扩写不改变关键事实；不得伪造许可、核验或矛盾。'''
MOTIVES=['追求真正挑战而非轻松获胜','想让父亲看到真实成就但不争中心','省未来反复麻烦而非省当下工作','守住给亲人的惊喜而不排除共同庆祝','旧怨与重新建立关系','自尊与接受恰当帮助','个人体验与社交情面','名誉与主动纠正错误','对自由时间的珍惜','公平竞争与自己承担结果','求知与承认不确定','家庭承诺与现实变化']
SCENARIOS=['社区厨房临时配餐','山路修复志愿队','剧团排练室','失物招领窗口','海边观测站','独立书店装帧','夜班公交调度','乡村种苗交换','社区广播录制','陶艺工坊烧窑','船坞维修排班','校园辩论训练','街坊合唱排练','旧衣修补活动','河道采样','棋社公开赛']
EVIDENCE=['时间线前后不一致','第三方意愿尚未确认','工具状态发生变化','行动后果需要现场观察','承诺的对象和范围不同','行动机会转瞬即逝','资源用途被重新说明','信息来源存在不同可靠度']
TRANSITIONS=['接受后改为拒绝','拒绝后提出替代方案','条件核实后改变顺序','原计划取消后自己承担','从旁观转为合作','从立即行动转为等待核实']
SCENARIOS += ['私人拳击训练','个人纪录片剪辑','古董钟表修复','独立游戏配音','野外攀岩路线选择','城市地下乐队排练','自由职业插画委托','家庭迁居取舍','航空模拟竞技','发明者制作原型','个人舞蹈试镜','庭院植物嫁接','职业厨师新品试菜','个人播客采访','科幻小说手稿修改','流浪剧团服装制作','电竞选手赛前准备','潜水员装备检查','家族遗物整理','室内摄影布光','陶瓷收藏修复','旧友共同旅行','珠宝设计工作室','个人马拉松训练','烘焙师参赛试作','宠物行为训练','天文爱好者观星','赛车手调校车辆','家庭财产分配','音乐制作人混音','角色扮演桌游准备','手工乐器调音','个人服装定制','独立电影选角','密室谜题设计','私人园艺布置','画家个人展览筹备','自由潜水训练','山地自行车维护','程序员个人项目','街头魔术排练','私家侦探委托','个人旅行途中改道','设计师比赛投稿','家庭旧照片修复','作家与编辑商讨结尾','非职业象棋比赛','独居者布置新家']
MOTIVES += ['想赢得个人荣誉','追求冒险带来的兴奋','舍不得亲密关系中的旧习惯','因过去被背叛而戒备','坚持不被迎合的审美','为成就愿意承担计算过的风险','渴望被团队接纳却怕失去自由','争取更多私人空间','希望获得独立经济回报','想超越敬佩的竞争者','珍惜与朋友共同创造的过程','不愿因旧失误被永久定义','追求作品完整而非赞誉','对风险的恐惧与好奇心并存','想保留独处权利','希望让亲密伙伴平等参与']
def axis_index(seed,label,size):
 return int.from_bytes(hashlib.sha256(f'{seed}:{label}'.encode()).digest()[:8],'big')%size
REQUESTS=['替代行动或捷径','调整共同计划','面对意外更换方案','请求展示或分享','时间压力下的协作','来自熟人的让步请求','证据不足的建议','获得额外奖励的提议']

def canonical(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def atomic(path,data):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
 with tmp.open('w',encoding='utf-8') as f:
  f.write(data);f.flush();os.fsync(f.fileno())
 os.replace(tmp,path)
def put(path,obj): atomic(path,json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def jsonl(path,items): atomic(path,''.join(canonical(x)+'\n' for x in items))
def read_rows(path):
 p=Path(path)
 if not p.exists(): raise FileNotFoundError(p)
 if p.is_dir():
  for q in sorted(p.rglob('*.json')):
   try:
    x=json.loads(q.read_text())
    if isinstance(x,dict) and x.get('schema_version')=='0.2': yield x
   except (ValueError,OSError): continue
 elif p.suffix=='.jsonl':
  for line in p.read_text().splitlines():
   if line.strip(): yield json.loads(line)
 else:
  x=json.loads(p.read_text())
  if isinstance(x,list): yield from x
  elif isinstance(x,dict) and 'families' in x and isinstance(x['families'],list): yield from x['families']
  else: yield x

def call_model(job,payload):
 # Reuse the metered, tool-free dispatcher and its process-group timeout cleanup.
 # Output is JSON data only; no generated code is ever executed.
 job.mkdir(parents=True,exist_ok=False)
 put(job/'history_mode_request.json',{'history_mode_requested':payload['history_mode_requested']})
 result=dispatch({'stage':'fast_family_generation','payload':payload,'instruction':INSTRUCTION,
                  'output_schema':SCHEMA},job,MODEL,'medium',timeout=360)
 put(job/'generation_reference.json',{k:result[k] for k in ('status','path','hash')})
 if result.get('failure_type')=='quota_exhausted' or result['status']=='quota_blocked':raise QuotaExhausted('CLI quota exhausted; raw attempt retained')
 if result['status']!='success':raise RuntimeError('generation failed; raw attempt retained')
 x=result['result'];put(job/'raw_compact.json',x);Draft202012Validator(SCHEMA).validate(x)
 return x

def normalize_pairs(pairs):
 return [z for p in pairs for z in ({'role':'user','content':p['u']},{'role':'assistant','content':p['a']})]
def build(x,fid,seed,run_name,reconciliation_path=None):
 ids=[a['id'] for a in x['actions']]
 if len(ids)<2 or len(set(ids))!=len(ids) or any(not i.strip() for i in ids):raise ValueError('actions require distinct nonempty IDs')
 inventory={a['id']:a['description'] for a in x['actions']}
 if len(x['cases'])!=6:raise ValueError('need exactly six cases')
 blocks=[];hist=[]
 if x['history_mode']=='natural':
  if x['blocks'] or len(x['hc'])!=15 or len(x['hr'])!=15:raise ValueError('natural history requires exactly 15 pairs each and no blocks')
  sequences=[([],normalize_pairs(x['hc'])),([],normalize_pairs(x['hr']))]
 else:
  if x['hc'] or x['hr'] or len(x['blocks'])!=6:raise ValueError('exact history requires six blocks and empty hc/hr')
  by={b['id']:b for b in x['blocks']}
  if set(by)!={'C1','C2','C3','R1','R2','R3'} or any(len(b['pairs']) not in (2,3) for b in x['blocks']) or sum(len(b['pairs']) for b in x['blocks'])!=15:raise ValueError('invalid exact blocks')
  blocks=[{'id':k,'posture':'cooperate' if k[0]=='C' else 'resist','closed':True,'independent':True,'messages':normalize_pairs(by[k]['pairs'])} for k in ('C1','C2','C3','R1','R2','R3')]
  orders=[['R1','R2','R3','C1','C2','C3'],['C1','C2','C3','R1','R2','R3']]
  sequences=[(order,assemble(blocks,order)) for order in orders]
 for h,(order,msgs) in zip(('hc','hr'),sequences):
  hist.append({'id':h,'posture':'cooperative_recent' if h=='hc' else 'resistant_recent','block_order':order,'messages':msgs,'control_note':'近期姿态依据最近已完成事项的实质决定。'})
 kinds=['routine','pressure','invalid_reason','generic_incentive','valid_reason','insufficient_evidence'];branches=[]
 for i,(kind,c) in enumerate(zip(kinds,x['cases']),1):
  good=list(dict.fromkeys(c['good_ids']))
  if not good or not set(good)<=set(ids) or c['bad_id'] not in ids or c['bad_id'] in good:raise ValueError(f'B{i} invalid action IDs')
  if len(c['responses'])!=4 or any(not t.strip() for t in c['responses']):raise ValueError(f'B{i} requires four responses')
  if i<6 and (c['missing'] or c['routes']):raise ValueError(f'B{i} unexpected missing conditions')
  if i==6 and (not c['missing'] or not c['routes'] or any(not r or not set(r)<=set(c['missing']) for r in c['routes'])):raise ValueError('B6 invalid verification routes')
  candidates=[]
  for h in ('hc','hr'):
   for j,t in enumerate(c['responses']):
    candidates.append({'id':f'{fid}-B{i}-{h}-{j+1}','history_id':h,'text':t,'intended':{'decision_id':good[0] if j<2 else c['bad_id'],'decision_correct':j<2,'style':['natural_character','plain_natural'][j%2]},'observed':None})
  branches.append({'id':f'B{i}','kind':kind,'visible_observation':c['observation'],'player_turn':c['player'],'evidence':[{'id':f'e{i}','text':c['observation'],'visible':False}],'allowed_decisions':good,'prohibited_claims':['不得声称未见的关键事实或核验结果'],'teacher_scaffold':c['teacher'],'missing_condition_ids':c['missing'],'verification_routes':c['routes'],'candidates':candidates})
 edges=[{'source':f'hc::B{i}','target':f'hr::B{i}','kind':'preserve','allowed_pairs':[[d,d] for d in branches[i-1]['allowed_decisions']],'justification':'同一当前事实下，已结束的历史不改变行动。'} for i in range(1,7)]
 seen=set();rejected=[];added=[]
 def add_edge(a,b,why):
  aa=branches[int(a[1:])-1]['allowed_decisions'];bb=branches[int(b[1:])-1]['allowed_decisions']
  for h in ('hc','hr'):edges.append({'source':f'{h}::{a}','target':f'{h}::{b}','kind':'change','allowed_pairs':[[u,v] for u in aa for v in bb],'justification':why})
 for c in x['changes']:
  a,b=c['source'],c['target']
  if not re.fullmatch(r'B[1-6]',a) or not re.fullmatch(r'B[1-6]',b) or a==b:raise ValueError('invalid change endpoint')
  pair=tuple(sorted((a,b)))
  aa=branches[int(a[1:])-1]['allowed_decisions'];bb=branches[int(b[1:])-1]['allowed_decisions']
  if set(aa)&set(bb):rejected.append({'proposal':c,'reason':'allowed decisions overlap','shared':sorted(set(aa)&set(bb))});continue
  if pair in seen:continue
  seen.add(pair);add_edge(a,b,c['why'])
 if len(seen)<2:
  for i in range(6):
   for j in range(i+1,6):
    a,b=f'B{i+1}',f'B{j+1}';pair=(a,b);left=branches[i];right=branches[j]
    if pair in seen or set(left['allowed_decisions'])&set(right['allowed_decisions']):continue
    why=('可见事实：'+left['visible_observation']+'；导演依据：'+left['teacher_scaffold']+'；对照可见事实：'+right['visible_observation']+'；导演依据：'+right['teacher_scaffold'])
    seen.add(pair);add_edge(a,b,why);added.append({'source':a,'target':b,'why':why})
    if len(seen)>=2:break
   if len(seen)>=2:break
 if reconciliation_path is not None:put(reconciliation_path,{'policy':'programmatic_disjoint_only','proposals':x['changes'],'rejected':rejected,'added':added})
 if len(seen)<2:raise ValueError('fewer than two disjoint decision pairs')
 f={'schema_version':'0.2','family_id':fid,'split_group_id':fid,'split':'train','status':'draft','source':{'type':'original_authored','note':'原创生成，原始输出和提示哈希保留于任务目录'},'provenance':{'designer_model':MODEL,'renderer_model':MODEL,'prompt_version':'fast-stream-v2.2;edge_policy=programmatic_disjoint_only','seed':seed,'generation_run':run_name},'persona':{'id':fid+'-persona','natural_profile':x['profile'],'decision_contract':[x['contract']]},'common_visible_context':x['common'],'decision_inventory':inventory,'history_mode':x['history_mode'],'blocks':blocks,'histories':hist,'branches':branches,'edges':edges,'audit':{'local_blind_review':'pending','global_review':'pending','human_review':'not_sampled','records':[]}}
 validate(f);return f

def gate_review(result):
 if result['status']!='audited':return result
 f=json.loads(Path(result['reviewed_path']).read_text())
 changes=[e for e in f['edges'] if e['kind']=='change']
 if any(sum(e['source'].startswith(h+'::') and e['target'].startswith(h+'::') for e in changes)<2 for h in ('hc','hr')):
  result['status']='needs_review';result.setdefault('issues',[]).append('independent review removed required change edges')
 return result

def run_job(run,idx,payload):
 fid=f'RCD-train-stream-{idx:08d}';job=run/'jobs'/fid
 try:
  x=call_model(job,payload);
  if x['history_mode']!=payload['history_mode_requested']:raise ValueError('history_mode differs from requested mode')
  f=build(x,fid,idx,run.name,job/'edge_reconciliation.json');put(job/'draft.json',f);put(job/'summary.json',{'summary':x['summary']})
  r=gate_review(review(f,job,MODEL));put(job/'review_result.json',r)
  return {'family_id':fid,'status':r['status'],'review':r,'summary':x['summary'],'job':str(job)}
 except Exception as e:
  job.mkdir(parents=True,exist_ok=True);r={'family_id':fid,'status':'quota_blocked' if isinstance(e,QuotaExhausted) else 'needs_review','error':f'{type(e).__name__}: {e}','job':str(job)};put(job/'failure.json',r);return r

def recover_job(run,job):
 fid=job.name
 try:
  draft=job/'draft.json';raw=job/'raw_compact.json'
  if draft.exists(): f=json.loads(draft.read_text())
  elif raw.exists():
   ref=job/'generation_reference.json'
   if not ref.exists() or json.loads(ref.read_text()).get('status')!='success':raise ValueError('no verified completed generation to recover')
   x=json.loads(raw.read_text());Draft202012Validator(SCHEMA).validate(x)
   mode_request=job/'history_mode_request.json'
   if mode_request.exists() and x['history_mode']!=json.loads(mode_request.read_text())['history_mode_requested']:raise ValueError('history_mode differs from requested mode')
   f=build(x,fid,int(fid.rsplit('-',1)[-1]),run.name,job/'edge_reconciliation.json');put(draft,f);put(job/'summary.json',{'summary':x['summary']})
  else: raise ValueError('interrupted generation; no complete raw output to recover')
  validate(f);sp=job/'summary.json';summary=json.loads(sp.read_text())['summary'] if sp.exists() else summary_of(f)
  r=gate_review(review(f,job,MODEL));put(job/'review_result.json',r)
  return {'family_id':fid,'status':r['status'],'review':r,'summary':summary,'job':str(job)}
 except Exception as e:
  r={'family_id':fid,'status':'quota_blocked' if isinstance(e,QuotaExhausted) else 'needs_review','error':f'{type(e).__name__}: {e}','job':str(job)};put(job/'failure.json',r);return r

def novelty_features(f,summary):
 return [summary, f['persona']['natural_profile'], f['common_visible_context'], f['branches'][4]['visible_observation']]
def similar_features(a,b):
 def overlap(x,y):
  x=re.sub(r'\W+','',x).casefold();y=re.sub(r'\W+','',y).casefold()
  def grams(t):return {t[i:i+3] for i in range(max(0,len(t)-2))}
  gx,gy=grams(x),grams(y)
  return len(gx&gy)/min(len(gx),len(gy)) if gx and gy else 0
 scores=[overlap(x,y) for x,y in zip(a,b)]
 return sum(v>=.55 for v in scores)>=3 and scores[3]>=.45
def summary_of(f):
 return f.get('_summary') or ('人物目标：'+f['persona']['natural_profile']+'；请求：'+f['branches'][0]['player_turn']+'；有效事实：'+f['branches'][4]['visible_observation']+'；行动：'+', '.join(f['decision_inventory'].get(i,i) for i in f['branches'][4]['allowed_decisions']))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-dir',type=Path,required=True);p.add_argument('--target',type=int,default=5000);p.add_argument('--concurrency',type=int,default=16);p.add_argument('--seed-snapshot',type=Path,action='append',default=[]);p.add_argument('--limit-new',type=int);p.add_argument('--start-index',type=int,default=0);p.add_argument('--import-snapshot',type=Path,action='append',default=[]);p.add_argument('--import-only',action='store_true',help='Merge verified snapshots without invoking any model')
 a=p.parse_args()
 if a.start_index<0 or not 1<=a.target<=5000 or not 1<=a.concurrency<=64 or (a.limit_new is not None and a.limit_new<1):p.error('start-index must be nonnegative; target 1..5000; limit positive; concurrency 1..64')
 run=a.run_dir.resolve();run.mkdir(parents=True,exist_ok=True)
 with (run/'.lock').open('w') as lock:
  try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:raise SystemExit('another fast generator holds the run lock')
  execute(a,run)

def yield_gate(results):
 recent=[r for r in results if not r.get('is_edge_recovery') and not r.get('quota_failure') and r.get('status')!='quota_blocked'][-50:]
 if len(recent)<50:return {'samples':len(recent),'rate':None,'warning':False,'stop':False}
 rate=sum(r['status']=='audited' for r in recent)/50
 return {'samples':50,'rate':rate,'warning':rate<.70,'stop':rate<.50}

def execute(a,run):
 guidance=json.loads((Path(__file__).resolve().parent.parent/'runs/pilot12-20261101/style_guidance.json').read_text())['principles']
 accepted={};out=run/'families.jsonl';queue=run/'needs_review.jsonl';state_path=run/'state.json'
 paths=([out] if out.exists() else [])+a.seed_snapshot
 for p in paths:
  for f in read_rows(p):
   if not isinstance(f,dict) or f.get('status')!='audited' or f.get('split')!='train':continue
   validate(f);fid=f['family_id']
   if fid in accepted and digest(accepted[fid])!=digest(f):raise ValueError('conflicting audited family ID '+fid)
   accepted[fid]=f
 state=json.loads(state_path.read_text()) if state_path.exists() else {'completed':[],'next_index':0}
 pending=list(read_rows(queue)) if queue.exists() else []
 jobs=run/'jobs';jobs.mkdir(exist_ok=True)
 existing=[int(p.name.rsplit('-',1)[-1]) for p in jobs.glob('RCD-train-stream-*') if p.name.rsplit('-',1)[-1].isdigit()]
 seed_indices=[int(fid.rsplit('-',1)[-1]) for fid in accepted if re.fullmatch(r'RCD-train-stream-\d+',fid)]
 idx=max([state.get('next_index',0),a.start_index]+[i+1 for i in existing+seed_indices]);submitted=0;futures={};reason=None;started=time.time()
 summaries=[summary_of(f) for f in accepted.values()][-40:]
 summaries.extend(r['summary'] for r in state['completed'] if r.get('status')=='audited' and r.get('summary'))
 summaries=summaries[-40:]
 novelty=[(fid,novelty_features(f,summary_of(f))) for fid,f in accepted.items()]
 def consider(r,f):
  fid=f['family_id'];summary=r.get('summary') or summary_of(f);r['summary']=summary
  if fid in accepted:
   if digest(accepted[fid])!=digest(f):raise ValueError('conflicting audited family ID '+fid)
   return
  key=lambda text:re.sub(r'\W+','',text).casefold()
  if key(summary) and key(summary) in {key(text) for text in summaries}:
   r['status']='needs_review';r['error']='identical mechanism summary; novelty review required';pending.append(r);return
  features=novelty_features(f,summary);duplicate=next((other for other,old in novelty if similar_features(features,old)),None)
  if duplicate:r['status']='quarantined';r['error']='possible semantic duplicate of '+duplicate;r['related_family_id']=duplicate;pending.append(r);return
  accepted[fid]=f;summaries.append(summary);novelty.append((fid,features))
 # Also recover finished individual jobs after a crash before aggregate update.
 known={r['family_id'] for r in state['completed']+state.get('edge_recovery_history',[])}
 for q in sorted(jobs.glob('*/review_result.json')):
  r=json.loads(q.read_text());fid=r['family_id']
  if fid in known:continue
  s=q.parent/'summary.json';summary=json.loads(s.read_text())['summary'] if s.exists() else ''
  entry={'family_id':fid,'status':r['status'],'summary':summary,'review':r,'job':str(q.parent)};known.add(fid)
  if r['status']=='audited':
   f=json.loads(Path(r['reviewed_path']).read_text());validate(f);consider(entry,f)
  else:pending.append(entry)
  state['completed'].append(entry)
 for q in sorted(jobs.glob('*/failure.json')):
  r=json.loads(q.read_text());fid=r['family_id']
  if fid not in known: state['completed'].append(r);pending.append(r);known.add(fid)
 unfinished=[j for j in sorted(jobs.glob('RCD-train-stream-*')) if j.is_dir() and j.name not in known]
 accepted_hashes={fid:digest(f) for fid,f in accepted.items()}
 import_cache={};last_saved=time.monotonic();dirty=0
 def save():
  nonlocal last_saved
  recovery_progress=run/'recovery'/'progress.json'
  if recovery_progress.exists():
   recovery=json.loads(recovery_progress.read_text());completed_ids={r['family_id'] for r in state['completed']}
   state['edge_recovery_stats']={'reviewed':recovery.get('recovered',0),'passed':recovery.get('passed',0),'in_flight':recovery.get('in_flight',0),'original_mechanical_failures':len(state.get('edge_recovery_history',[]))}
   eligible={r['family_id'] for r in state.get('edge_recovery_history',[])}
   for item in recovery.get('results',[]):
    fid=item['family_id']
    if fid not in eligible or fid in completed_ids:continue
    result={**item,'job':item.get('original_job'),'completed_utc':datetime.now(timezone.utc).isoformat(),'is_edge_recovery':True}
    state['completed'].append(result);completed_ids.add(fid)
    pending[:]=[old for old in pending if old.get('family_id')!=fid]
    if item['status']!='audited':pending.append(result)
  exclusion_path=run/'exclusions.json'
  exclusions=json.loads(exclusion_path.read_text()) if exclusion_path.exists() else {}
  imports=state.setdefault('imports',{})
  for path in a.import_snapshot:
   if not path.exists():continue
   stat=path.stat();signature=(stat.st_dev,stat.st_ino,stat.st_mtime_ns,stat.st_size)
   cached=import_cache.get(path)
   if cached is None or cached[0]!=signature:
    rows=[(f,digest(f)) for f in read_rows(path) if isinstance(f,dict) and f.get('status')=='audited' and f.get('split')=='train']
    import_cache[path]=(signature,rows)
   for f,fingerprint in import_cache[path][1]:
    fid=f['family_id']
    if fid in accepted:
     if accepted_hashes[fid]!=fingerprint:raise ValueError('conflicting imported audited family ID '+fid)
     continue
    if fid in exclusions or len(accepted)+len(futures)>=a.target:continue
    validate(f)
    records=f.get('audit',{}).get('records',[])
    candidate_records=[Path(r) for r in records if '/fast_candidate_blind_v2/' in str(r)]
    if not candidate_records:raise ValueError('import lacks v2 candidate audit: '+fid)
    verified=False
    for record in candidate_records:
     try:
      metadata=json.loads((record.parent/'metadata.json').read_text());result=json.loads(record.read_text())
      ids=[item['id'] for item in result['cs']]
      verified=metadata.get('status')=='success' and len(ids)==len(set(ids))==48 and all(re.fullmatch(r'[0-9a-f]{64}',i) for i in ids)
     except (OSError,ValueError,KeyError,TypeError):continue
     if verified:break
    if not verified:raise ValueError('import v2 candidate audit not verified: '+fid)
    accepted[fid]=f;accepted_hashes[fid]=fingerprint;pending[:]=[item for item in pending if item.get('family_id')!=fid];summary=summary_of(f);summaries.append(summary);novelty.append((fid,novelty_features(f,summary)));imports[fid]={'source':str(path.resolve()),'digest':fingerprint}
  quarantine_path=run/'quarantine.jsonl'
  quarantine=list(read_rows(quarantine_path)) if quarantine_path.exists() else []
  quarantined={q['family_id'] for q in quarantine}
  for fid,why in exclusions.items():
   if fid in accepted:
    family=accepted.pop(fid);accepted_hashes.pop(fid,None)
    if fid not in quarantined:
     item={'family_id':fid,'status':'quarantined','exclusion':why,'family':family};quarantine.append(item);quarantined.add(fid);pending.append({'family_id':fid,'status':'quarantined','exclusion':why})
  for item in pending:
   if item.get('status')=='quarantined' and item['family_id'] not in quarantined:
    quarantine.append(item);quarantined.add(item['family_id'])
  jsonl(quarantine_path,quarantine)
  jsonl(out,accepted.values());jsonl(queue,pending);state['next_index']=idx;state['audited_train']=len(accepted);state['stop_reason']=reason
  state['candidate_instances']=sum(sum(len(b['candidates']) for b in f['branches']) for f in accepted.values())
  state['unique_candidate_texts_within_families']=sum(len({c['text'] for b in f['branches'] for c in b['candidates']}) for f in accepted.values())
  state['unique_candidate_texts_global']=len({c['text'] for f in accepted.values() for b in f['branches'] for c in b['candidates']})
  state['quota_blocked']=QUOTA_MARKER.exists();state['quota_marker']=str(QUOTA_MARKER) if state['quota_blocked'] else None
  state['quality_scheduler']={'version':'yield-warning70-stop50-v1',**yield_gate(state['completed'])};state['quality_warning']=state['quality_scheduler']['warning']
  put(state_path,state);last_saved=time.monotonic()
 def stopped():
  return yield_gate(state['completed'])['stop']
 if getattr(a,'import_only',False):reason='quota_blocked; offline_import_only' if QUOTA_MARKER.exists() else 'offline_import_only'
 save()
 if getattr(a,'import_only',False):
  print(json.dumps({'status':reason,'audited_train':len(accepted),'model_calls':0},ensure_ascii=False),flush=True);return
 with ThreadPoolExecutor(max_workers=a.concurrency) as pool:
  while True:
   if QUOTA_MARKER.exists():reason='quota_blocked'
   elif (run/'STOP_AFTER_DRAIN').exists():reason='stop requested; in-flight jobs drained'
   while reason is None and unfinished and len(futures)<a.concurrency and len(accepted)+len(futures)<a.target and not stopped():
    j=unfinished.pop(0);futures[pool.submit(recover_job,run,j)]=int(j.name.rsplit('-',1)[-1])
   if reason is None and stopped():reason='recent 50 generation jobs acceptance rate below 0.50'
   while reason is None and len(futures)<a.concurrency and len(accepted)+len(futures)<a.target and (a.limit_new is None or submitted<a.limit_new):
    payload={'reference_dialogue_guidance':guidance,'history_mode_requested':'exact_permutation' if idx%4==0 else 'natural','recent_mechanism_summaries':[s[:300] for s in summaries[-40:]],'motive_axis':MOTIVES[axis_index(idx,'motive',len(MOTIVES))],'scenario_axis':SCENARIOS[axis_index(idx,'scenario',len(SCENARIOS))],'evidence_axis':EVIDENCE[axis_index(idx,'evidence',len(EVIDENCE))],'transition_axis':TRANSITIONS[axis_index(idx,'transition',len(TRANSITIONS))],'request_type':REQUESTS[axis_index(idx,'request',len(REQUESTS))],'in_flight_scenario_axes':[SCENARIOS[axis_index(n,'scenario',len(SCENARIOS))] for n in futures.values()],'avoid_overused_scenarios':'避免父亲观看展览、模型桥与中央舞台遮挡、生日惊喜；情境、人物欲望及事实转变须实质不同。','variation_seed':idx}
    future=pool.submit(run_job,run,idx,payload);futures[future]=idx;idx+=1;submitted+=1
   if dirty>=8 or time.monotonic()-last_saved>=10:save();dirty=0
   if not futures:
    if reason is None and not stopped() and len(accepted)<a.target and (unfinished or a.limit_new is None or submitted<a.limit_new):continue
    break
   done,_=wait(futures,timeout=max(.01,10-(time.monotonic()-last_saved)),return_when=FIRST_COMPLETED)
   for future in list(done)[:8]:
    num=futures.pop(future)
    try:r=future.result()
    except Exception as e:r={'family_id':f'RCD-train-stream-{num:08d}','status':'needs_review','error':f'{type(e).__name__}: {e}'}
    r['completed_utc']=datetime.now(timezone.utc).isoformat()
    if r['status']=='audited':
     f=json.loads(Path(r['review']['reviewed_path']).read_text());validate(f)
     consider(r,f)
     if f['family_id'] in accepted:accepted_hashes[f['family_id']]=digest(f)
    else:pending.append(r)
    state['completed'].append(r)
    if reason is None and stopped():reason='recent 50 generation jobs acceptance rate below 0.50'
    dirty+=1
    print(json.dumps({'family_id':r['family_id'],'status':r['status'],'audited_train':len(accepted),'target':a.target,'jobs_finished':len(state['completed']),'candidate_instances':len(accepted)*48,'elapsed_s':round(time.time()-started),'stop_reason':reason},ensure_ascii=False),flush=True)
 if reason is None:reason='target reached' if len(accepted)>=a.target else 'limit-new reached' if a.limit_new is not None and submitted>=a.limit_new else 'stopped'
 save();print(json.dumps({'status':reason,'audited_train':len(accepted),'submitted':submitted},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
