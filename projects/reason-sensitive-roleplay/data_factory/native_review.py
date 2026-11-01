"""Blind export and native-agent assembly adapter for fast_review."""
import argparse, hashlib, json, shutil
from datetime import datetime, timezone
from pathlib import Path
from jsonschema import Draft202012Validator
import fast_review
from factory import digest, validate

def read(p): return json.loads(Path(p).read_text())
def write(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(x): return hashlib.sha256(x if isinstance(x,bytes) else x.encode()).hexdigest()
def export(draft,out):
 f=read(draft);validate(f);base,candidate,mapping,aliases=fast_review.payloads(f);h=sha(Path(draft).read_bytes());out=Path(out);out.mkdir(parents=True,exist_ok=True)
 ls=json.loads(json.dumps(fast_review.LOCAL));ls['properties']['nodes'].update(minItems=12,maxItems=12);ls['properties']['nodes']['items']['properties']['n']={'type':'string','enum':list(mapping)};ls['properties']['nodes']['items']['properties']['actions']['items']={'type':'string','enum':list(f['decision_inventory'])}
 rs=json.loads(json.dumps(fast_review.RATINGS));rs['properties']['cs'].update(minItems=48,maxItems=48);rs['properties']['cs']['items']['properties']['id']={'type':'string','enum':list(aliases)};rs['properties']['cs']['items']['properties']['d']={'type':'string','enum':list(f['decision_inventory'])}
 rs['properties']['cs']['items']['properties']['quotes']['minItems']=1
 Draft202012Validator.check_schema(ls);Draft202012Validator.check_schema(rs)
 local_instruction=('盲审局部反应：仅看profile、context、history、scene和action_dictionary，不看候选或作者标签。'
  '每个node是独立反事实，不得借兄弟scene事实。恰好返回12个n；列合理主动作、缺失信息、可做核验及简短理由。')
 ratings_instruction=('盲审每条自然候选，不看作者答案。每node为独立反事实。每个alias恰好一次，共48条；'
  'd为action_dictionary中的实际动作，c为决定支持，g为依据/核验主张忠实，s为自然度，style仅语体支持，'
  'v为实际请求核验的未知条件，quotes为候选中逐字连续原文，f为核验可执行，p为核验前无条件承诺。'
  '重大不可判断问题列blocking，细微偏好列notes；不推断或补写候选没有说的核验。')
 write(out/'LOCAL.json',{'source_sha256':h,'stage':'fast_local_blind','instruction':local_instruction,'payload':base,'schema':ls})
 write(out/'RATINGS.json',{'source_sha256':h,'stage':'fast_candidate_blind_v2','instruction':ratings_instruction,'payload':candidate,'schema':rs})
 write(out/'manifest.json',{'family_id':f['family_id'],'source_path':str(Path(draft).resolve()),'source_sha256':h,'aliases':aliases,'mapping':{n:list(v) for n,v in mapping.items()}})
 return out
def assemble(draft,out,local,ratings,local_agent,ratings_agent,model='gpt-6.1-terra'):
 f=read(draft);validate(f);out=Path(out).resolve();m=read(out/'manifest.json');h=sha(Path(draft).read_bytes())
 if local_agent==ratings_agent:raise ValueError('local and ratings reviewers must be distinct')
 if m['source_sha256']!=h:raise ValueError('source changed; re-export before assembly')
 aliases=m['aliases'];expected={c['id'] for b in f['branches'] for c in b['candidates']}
 if len(aliases)!=48 or set(aliases.values())!=expected:raise ValueError('manifest aliases mismatch')
 expected_base,expected_candidate,_,expected_aliases=fast_review.payloads(f)
 if aliases!=expected_aliases:raise ValueError('manifest aliases differ from current source')
 answers={}
 for stage,path,request_file,agent,n,field in [('fast_local_blind',local,'LOCAL.json',local_agent,12,'nodes'),('fast_candidate_blind_v2',ratings,'RATINGS.json',ratings_agent,48,'cs')]:
  request=read(out/request_file)
  if request.get('source_sha256')!=h:raise ValueError('export payload source mismatch')
  expected_payload=expected_base if field=='nodes' else expected_candidate
  if request.get('payload')!=expected_payload:raise ValueError(stage+': exported payload differs from current source')
  raw=read(path)
  if raw.get('source_sha256')!=h:raise ValueError(stage+': source hash mismatch')
  expected_payload_hash=sha(json.dumps(request['payload'],ensure_ascii=False,sort_keys=True,separators=(',',':')))
  if raw.get('input_payload_hash') is not None and raw['input_payload_hash']!=expected_payload_hash:raise ValueError(stage+': input payload hash mismatch')
  result=raw.get('result',raw);Draft202012Validator(request['schema']).validate(result);items=result[field]
  if len(items)!=n:raise ValueError(stage+': expected exactly '+str(n))
  ids=[x['id'] for x in items] if field=='cs' else [x['n'] for x in items]
  if len(set(ids))!=n:raise ValueError(stage+': duplicate or missing ids')
  if field=='cs' and set(ids)!=set(aliases):raise ValueError('ratings aliases missing or extra')
  answers[stage]=(result,raw,agent,path)
 def backend(task,run,mdl,effort):
  stage=task['stage'];result,raw,agent,path=answers[stage]
  ident={'stage':stage,'payload':task['payload'],'instruction':task['instruction'],'output_schema':task['output_schema'],'model':mdl,'effort':effort}
  key=sha(json.dumps(ident,ensure_ascii=False,sort_keys=True,separators=(',',':')));dest=Path(run)/'raw'/stage/key/'attempt-000';dest.mkdir(parents=True,exist_ok=True)
  write(dest/'result.json',result);shutil.copyfile(path,dest/'native_input.json')
  write(dest/'metadata.json',{'status':'success','transport':'collaboration.spawn_agent','model':mdl,'agent_task_name':agent,'collected_utc':raw.get('collected_utc',datetime.now(timezone.utc).isoformat()),'input_hash':sha(json.dumps(task['payload'],ensure_ascii=False,sort_keys=True,separators=(',',':'))),'output_hash':sha(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(',',':'))),'usage':None})
  return {'status':'success','result':result,'path':str(dest),'transport':'collaboration.spawn_agent'}
 return fast_review.review(f,out,model,dispatcher=backend)
def main():
 p=argparse.ArgumentParser();s=p.add_subparsers(dest='cmd',required=True)
 e=s.add_parser('export');e.add_argument('--draft',required=True);e.add_argument('--out',required=True)
 a=s.add_parser('assemble');a.add_argument('--draft',required=True);a.add_argument('--out',required=True);a.add_argument('--local',required=True);a.add_argument('--ratings',required=True);a.add_argument('--local-agent',required=True);a.add_argument('--ratings-agent',required=True);a.add_argument('--model',default='gpt-6.1-terra')
 x=p.parse_args()
 if x.cmd=='export':export(x.draft,x.out)
 else:print(json.dumps(assemble(x.draft,x.out,x.local,x.ratings,x.local_agent,x.ratings_agent,x.model),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
