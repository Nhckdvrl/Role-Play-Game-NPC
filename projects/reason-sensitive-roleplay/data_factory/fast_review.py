"""Family-level independent Terra review; no author targets enter either pass."""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
from copy import deepcopy
import hashlib,json,random,time
from pathlib import Path
from agent_dispatch import dispatch
from factory import validate,digest,write_new

S={'type':'string'};B={'type':'boolean'};N={'type':'number','minimum':0,'maximum':1}
def arr(x):return {'type':'array','items':x}
def obj(**x):return {'type':'object','properties':x,'required':list(x),'additionalProperties':False}
LOCAL=obj(nodes=arr(obj(n=S,actions=arr(S),missing=arr(S),checks=arr(S),why=S)),blocking=arr(S))
RATINGS=obj(cs=arr(obj(id=S,d=S,c=B,g=B,s=N,style=N,v=arr(S),quotes=arr(S),f=B,p=B,why=S)),blocking=arr(S),notes=arr(S))

def read(p):return json.loads(Path(p).read_text())
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 text=json.dumps(x,ensure_ascii=False,indent=2)+'\n'
 if p.exists() and p.read_text()!=text:raise FileExistsError(p)
 if not p.exists():p.write_text(text)

def payloads(f):
 scenes=[];nodes=[];mapping={};cands=[];aliases={}
 source_hash=digest(f)
 for b in f['branches']:
  bid=digest([f['family_id'],b['id']])[:12]
  scenes.append({'scene':bid,'observation':b['visible_observation'],'player':b['player_turn'],
    'visible_evidence':[e['text'] for e in b['evidence'] if e['visible']]})
  for h in f['histories']:
   nid=digest([f['family_id'],h['id'],b['id']])[:12]
   nodes.append({'n':nid,'history':h['id'],'scene':bid});mapping[nid]=(h['id'],b['id'])
   for c in b['candidates']:
    if c['history_id']==h['id']:
     alias=digest(['fast-candidate-blind-v2',f['family_id'],source_hash,c['id']])
     if alias in aliases:raise ValueError('candidate alias collision')
     aliases[alias]=c['id'];cands.append({'id':alias,'n':nid,'text':c['text']})
 base={'profile':f['persona']['natural_profile'],'context':f['common_visible_context'],
  'histories':[{'id':h['id'],'messages':h['messages']} for h in f['histories']],
  'scenes':scenes,'nodes':nodes,'action_dictionary':f['decision_inventory']}
 # No intended, allowed_decisions, branch kind, decision_contract or teacher.
 random.Random(digest(f['family_id'])).shuffle(cands)
 candidate={**base,'candidates':cands,'condition_vocabulary':sorted({x for b in f['branches'] for x in b['missing_condition_ids']})}
 return base,candidate,mapping,aliases

def dispatch_ratings(task,run,model,aliases,dispatcher=None):
 dispatcher=dispatcher or dispatch
 # Keep the original request and cache; retry incomplete IDs with a constrained schema.
 result=dispatcher(task,run,model,'low')
 if result['status']!='success':return result
 try:
  ids=[x['id'] for x in result['result']['cs']]
  if len(ids)==48 and set(ids)==set(aliases):return result
 except (KeyError,TypeError):pass
 constrained=deepcopy(task)
 cs=constrained['output_schema']['properties']['cs']
 cs['minItems']=cs['maxItems']=48
 cs['items']['properties']['id']={'type':'string','enum':list(aliases)}
 return dispatcher(constrained,run,model,'low')

def review(f,run,model,dispatcher=None):
 dispatcher=dispatcher or dispatch
 validate(f);base,candidate,mapping,aliases=payloads(f);fid=f['family_id']
 source=run/'source_snapshots'/fid/(digest(f)+'.json');save(source,f)
 local_schema=deepcopy(LOCAL)
 local_schema['properties']['nodes']['items']['properties']['actions']['items']={'type':'string','enum':list(f['decision_inventory'])}
 rating_schema=deepcopy(RATINGS)
 rating_schema['properties']['cs']['items']['properties']['d']={'type':'string','enum':list(f['decision_inventory'])}
 local=dispatcher({'stage':'fast_local_blind','payload':base,'instruction':
  '独立局部信息审查，没有候选和作者答案。每个node是独立反事实：profile+context+指定history+指定scene，'
  '不得借兄弟scene的事实。为每node列当前合理主要action_dictionary动作、缺什么及可做核验，用简短why。'
  '已明确的当前意愿与事实按已知处理，不臆想额外阻碍；真有多种合理主反应可以并列。'
  '检查历史自然连贯、当前相关资源/承诺/知识不被改变。近期合作/拒绝按最近事项的实质选择，'
  '角色拒绝原请求后对方接受、角色礼貌确认，并不变成新的合作事项；不要强求最后每句话都说不。'
  '明显凑轮、同一消息混演双方、主线状态矛盾才blocking；普通措辞偏好不阻断。'
  'nodes必须恰好返回输入的12个n，保留真实不确定性。','output_schema':local_schema},run,model,'low')
 rated=dispatch_ratings({'stage':'fast_candidate_blind_v2','payload':candidate,'instruction':
  '独立审查每条自然候选，未知生成目标，不看作者答案。每node是独立反事实，不能从兄弟scene借信息。'
  '逐条返回：id原样,d实际主要动作ID,c该决定是否由当前人物与事实支持,g决定依据/核验主张是否忠实，'
  's表达自然度0..1,style仅语体/职业措辞/语气像此人的支持度，不因决定错自动扣风格，平实也可优秀；'
  'v仅候选实际请求/安排查验的未知条件ID（condition_vocabulary仅词典），quotes必须至少一条，逐条为候选对应非空连续原文，覆盖决定与重要事实主张，'
  'f核验能否执行,p是否在核验前无条件承诺需该条件才能作的动作，why用一句短理由。'
  '核实条件成立后再做是条件性计划，不是提前承诺。已知事实复述/交接细节不自动变成缺失条件请求。'
  '事实真实但理由无效与伪造事实分开，不能因决定错就g=false。角色明确要隐瞒时，策略性言语不等于其内在依据失真。'
  '不影响决定条件、未伪造许可/核验且不冲突的普通场景描写不应导致整族返工；明确数字/状态矛盾要标g=false。'
  '不要推断恰好多少条正确；不能用评价任务替候选补上没说的核验。每id恰好一次，所有48条，'
  '重大场景矛盾或真实不可判断列blocking，细微偏好列notes。','output_schema':rating_schema},run,model,aliases,dispatcher)
 if local['status']!='success' or rated['status']!='success':
  quota=any(x.get('failure_type')=='quota_exhausted' or x['status']=='quota_blocked' for x in (local,rated))
  return {'family_id':fid,'status':'quota_blocked' if quota else 'service_failure','gate_version':'v2.1-independent-grounding','source':str(source)}
 ls=local['result'];rs=rated['result'];actors={x['n']:set(x['actions']) for x in ls['nodes']};observed={aliases[x['id']]:x for x in rs['cs'] if x['id'] in aliases}
 expected={c['id'] for b in f['branches'] for c in b['candidates']};issues=list(ls['blocking'])+list(rs['blocking'])
 if set(actors)!=set(mapping) or len(ls['nodes'])!=12:issues.append('incomplete local reactions')
 if set(observed)!=expected or len(rs['cs'])!=48 or set(x['id'] for x in rs['cs'])!=set(aliases):issues.append('incomplete candidate ratings')
 if issues and (set(observed)!=expected or set(actors)!=set(mapping) or len(rs['cs'])!=48 or set(x['id'] for x in rs['cs'])!=set(aliases)):
  return {'family_id':fid,'status':'needs_review','gate_version':'v2.1-independent-grounding','issues':issues,'source':str(source)}
 family=deepcopy(f);expansions=[]
 for b in family['branches']:
  for c in b['candidates']:
   x=observed[c['id']];nid=next(n for n,pair in mapping.items() if pair==(c['history_id'],b['id']))
   if x['d'] not in family['decision_inventory']:issues.append(c['id']+':unknown action')
   if x['c']!=c['intended']['decision_correct']:issues.append(c['id']+':rendered correctness differs from request')
   if x['c'] and not x['g']:issues.append(c['id']+':positive has unfaithful basis')
   if x['s']<.7:issues.append(c['id']+':expression not natural')
   if x['c'] and x['d'] not in actors[nid]:issues.append(c['id']+':independent reviewers disagree')
   if x['c'] and x['d'] not in b['allowed_decisions'] and x['d'] in actors[nid]:
    b['allowed_decisions'].append(x['d']);expansions.append({'branch':b['id'],'action':x['d'],'candidate':c['id'],'reason':x['why']})
   if not x['c'] and x['d'] in b['allowed_decisions']:issues.append(c['id']+':author action set disagrees with independent rating')
   if not x['quotes'] or any(not q.strip() or q not in c['text'] for q in x['quotes']):issues.append(c['id']+':unfaithful quote')
   if b['kind']=='insufficient_evidence' and x['c']:
    if not any(set(route)<=set(x['v']) for route in b['verification_routes']) or not x['f'] or x['p']:issues.append(c['id']+':B6 insufficient verification')
   c['observed']={'audit_id':str(Path(rated['path'])/'result.json')+'#/cs/'+str(rs['cs'].index(x)),
    'decision_id':x['d'],'decision_correct':x['c'],'evidence_ok':x['g'],'naturalness':x['s'],
    'requested_conditions':x['v'],'feasible_verification':x['f'],'premature_commitment':x['p']}
 # Permit independently grounded alternative reactions; never change their labels.
 if expansions:
  by={b['id']:set(b['allowed_decisions']) for b in family['branches']};edges=[]
  for edge in family['edges']:
   l=by[edge['source'].split('::')[1]];r=by[edge['target'].split('::')[1]]
   if edge['kind']=='change' and l&r:continue
   e=deepcopy(edge);e['allowed_pairs']=([[d,d] for d in sorted(l&r)] if e['kind']=='preserve' else [[a,b] for a in sorted(l) for b in sorted(r)])
   if e['allowed_pairs']:edges.append(e)
  family['edges']=edges
 passed=not issues;family['status']='audited' if passed else 'needs_review'
 family['audit']={'local_blind_review':'pass' if not ls['blocking'] else 'fail','global_review':'pass' if passed else 'fail',
  'human_review':'not_sampled','records':[str(Path(local['path'])/'result.json'),str(Path(rated['path'])/'result.json')]}
 validate(family);save(run/'reviewed_v2_1'/f'{fid}.json',family)
 negative=[x for x in rs['cs'] if not x['c']]
 hard=sum(x['g'] and x['style']>=.7 for x in negative)
 return {'family_id':fid,'status':family['status'],'gate_version':'v2.1-independent-grounding','negative_counts':{'total':len(negative),'hard':hard,'easy':sum(not x['g'] for x in negative),'grounded_style_below_threshold':sum(x['g'] and x['style']<.7 for x in negative)},'issues':issues,'expansions':expansions,
   'source':str(source),'reviewed_path':str(run/'reviewed_v2_1'/f'{fid}.json'),
   'local_raw':local['path'],'candidate_raw':rated['path'],'notes':rs['notes']}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-dir',type=Path,required=True);p.add_argument('--concurrency',type=int,default=16)
 a=p.parse_args();run=a.run_dir.resolve();paths=sorted((run/'drafts').glob('*/*.json'));families=[]
 for path in paths:
  x=read(path)
  if isinstance(x,dict) and x.get('schema_version')=='0.2' and x.get('family_id'):families.append(x)
 if not families:raise ValueError('no real complete draft families')
 results=[];started=time.time()
 with ThreadPoolExecutor(max_workers=a.concurrency) as pool:
  futures={pool.submit(review,f,run,'gpt-6.1-terra'):f['family_id'] for f in families}
  for future in as_completed(futures):
   fid=futures[future]
   try:r=future.result()
   except Exception as exc:r={'family_id':fid,'status':'error','error':str(exc)}
   results.append(r);save(run/'review_results'/f'{fid}.json',r)
   print(json.dumps({'done':len(results),'total':len(families),'family_id':fid,'status':r['status'],'elapsed_s':round(time.time()-started)},ensure_ascii=False),flush=True)
 accepted=[read(x['reviewed_path']) for x in results if x['status']=='audited'];pending=[x for x in results if x['status']!='audited']
 write_new(run/'fast_audited.jsonl',accepted);save(run/'fast_review_summary.json',{'generated':len(families),'audited':len(accepted),'needs_review':len(pending),'elapsed_seconds':time.time()-started,'review_protocol':'family-level independent local/candidate passes; generation intentions hidden','results':results})

if __name__=='__main__':main()
