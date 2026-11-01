#!/usr/bin/env python3
"""Independent, resumable live global quality sentinel. Never executes model output."""
import hashlib,json,os,time,random,threading,fcntl,math,collections,heapq,subprocess,sys,re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from agent_dispatch import dispatch

ROOT=Path(__file__).resolve().parent.parent
RUN=ROOT/'runs/train5000-live'; OUT=ROOT/'runs/global-quality-live'; OUT.mkdir(parents=True,exist_ok=True)
for d in ('decisions','natural','batches'): (OUT/d).mkdir(exist_ok=True)
S={'type':'string'}; B={'type':'boolean'}; N={'type':'number','minimum':0,'maximum':1}
def arr(x):return {'type':'array','items':x}
def obj(**x):return {'type':'object','properties':x,'required':list(x),'additionalProperties':False}
ITEM=obj(id=S,duplicate=B,confidence=N,quote_a=S,quote_b=S,reason=S)
PAIR_SCHEMA=obj(results=arr(ITEM)); NAT_ITEM=obj(id=S,severe=B,confidence=N,history=S,quote_a=S,quote_b=S,reason=S)
NAT_SCHEMA=obj(results=arr(NAT_ITEM))
PAIR_INSTRUCTION=('独立判断每对是否同一具体故事换皮：需结合人物具体目标、冲突、关键证据如何改变与实际行动要求，'
 '共同动机、职业场景、同一六分支形式或一般主题不构成复写。每对返回原id、duplicate、confidence、'
 'quote_a和quote_b分别为对应A/B中可逐字匹配的关键原文，reason说决定性相同或差异；允许不确定。')
NAT_INSTRUCTION=('逐族看完整两段历史及六个彼此独立当前场景。只判断严重的历史状态自相矛盾、已完成同一具体事项被无解释重置、'
 '或必须独立的历史块实际互相影响；不要因礼貌收尾、普通措辞、未写背景或小事繁琐而阻断。'
 '返回原id、severe、confidence、history填有证据的历史代号、quote_a/quote_b为该完整历史中的两段逐字原文，'
 'reason解释时序；不确定或仅文风问题severe=false。')
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def digest(x):return hashlib.sha256(canon(x).encode()).hexdigest()
def atomic(path,x):
 tmp=path.with_name(path.name+'.'+str(os.getpid())+'.'+str(threading.get_ident())+'.tmp')
 with tmp.open('w',encoding='utf-8') as f:f.write(json.dumps(x,ensure_ascii=False,indent=2)+'\n');f.flush();os.fsync(f.fileno())
 os.replace(tmp,path)
def read(path,default):
 try:return json.loads(path.read_text(encoding='utf-8'))
 except FileNotFoundError:return default
def event(kind,**details):
 with (OUT/'events.jsonl').open('a',encoding='utf-8') as f:f.write(canon({'time':time.time(),'event':kind,**details})+'\n')
def visible(f):
 return {'profile':f['persona']['natural_profile'],'context':f['common_visible_context'],
  'scenes':[{'observation':b['visible_observation'],'player':b['player_turn']} for b in f['branches']]}
def natural_visible(f):
 v=visible(f);v['histories']=[{'history':'H'+str(i+1),'messages':h['messages']} for i,h in enumerate(f['histories'])];return v
def flat(x):
 if isinstance(x,str):return x
 if isinstance(x,dict):return '\n'.join(flat(v) for v in x.values())
 if isinstance(x,list):return '\n'.join(flat(v) for v in x)
 return ''
def quoted(q,side):return bool(q and q.strip() and q in flat(side))
def response(r,ids):
 if r.get('status')!='success':return None
 try:
  rows=r['result']['results'];return {x['id']:x for x in rows} if len(rows)==len(ids) and set(x['id'] for x in rows)==set(ids) else None
 except (KeyError,TypeError):return None
def pair_key(a,b):
 # Pair identities and actor-visible payload both participate; changed facts invalidate cache.
 return digest(sorted([(a['family_id'],digest(visible(a))),(b['family_id'],digest(visible(b)))]))
def pair_batch(items):
 payload=[]; refs={}
 for a,b,key in items:
  alias=digest(['pair',key])[:20];va,vb=visible(a),visible(b);payload.append({'id':alias,'A':va,'B':vb});refs[alias]=(a,b,key,va,vb)
 res=dispatch({'stage':'global_pairs_v1','payload':{'pairs':payload},'instruction':PAIR_INSTRUCTION,'output_schema':PAIR_SCHEMA},OUT,'gpt-6.1-terra','low')
 rows=response(res,refs);saved=[]
 for alias,(a,b,key,va,vb) in refs.items():
  row=rows.get(alias) if rows else None
  record={'pair_key':key,'a':a['family_id'],'b':b['family_id'],'payload_hashes':[digest(va),digest(vb)],'first_raw':res.get('path'),'first':row,'status':'pending'}
  if row and row['duplicate'] and row['confidence']>=.9:
   rr=dispatch({'stage':'global_pairs_confirm_v1','payload':{'pairs':[{'id':alias,'A':va,'B':vb}]},'instruction':PAIR_INSTRUCTION,'output_schema':PAIR_SCHEMA},OUT,'gpt-6-astra','low')
   check=response(rr,[alias]);second=check.get(alias) if check else None;record.update(second_raw=rr.get('path'),second=second)
   if second and second['duplicate'] and second['confidence']>=.9 and quoted(row['quote_a'],va) and quoted(row['quote_b'],vb) and quoted(second['quote_a'],va) and quoted(second['quote_b'],vb):record['status']='confirmed_duplicate'
  elif row and not row['duplicate'] and row['confidence']>=.9:record['status']='distinct'
  atomic(OUT/'decisions'/f'{key}.json',record);saved.append(record)
 return saved
def adjudicate_pending(rec,a,b):
 key=rec['pair_key'];alias=digest(['pair',key])[:20];va,vb=visible(a),visible(b)
 if rec.get('payload_hashes')!=[digest(va),digest(vb)]:return
 def valid(x):return bool(x and x.get('confidence',0)>=(.9 if x.get('duplicate') else .8) and x.get('reason','').strip() and quoted(x.get('quote_a',''),va) and quoted(x.get('quote_b',''),vb))
 votes=[rec.get('first')];extra=rec.get('adjudications',[])
 if rec.get('second_raw') and not extra:extra=[{'raw':rec.get('second_raw'),'result':rec.get('second')}]
 votes.extend(x.get('result') for x in extra)
 while len(extra)<2:
  num=len(extra)+1
  rr=dispatch({'stage':'global_pairs_adjudicate_'+str(num),'payload':{'pairs':[{'id':alias,'A':va,'B':vb}]},'instruction':PAIR_INSTRUCTION,'output_schema':PAIR_SCHEMA},OUT,'gpt-6-astra','low')
  rows=response(rr,[alias]);row=rows.get(alias) if rows else None;extra.append({'raw':rr.get('path'),'result':row});votes.append(row)
  strong=[x for x in votes if valid(x)]
  if sum(x['duplicate'] for x in strong)>=2 or sum(not x['duplicate'] for x in strong)>=2:break
 strong=[x for x in votes if valid(x)];rec['adjudications']=extra
 if sum(x['duplicate'] for x in strong)>=2:rec['status']='confirmed_duplicate'
 elif sum(not x['duplicate'] for x in strong)>=2:rec['status']='distinct_adjudicated'
 else:rec['status']='pending'
 atomic(OUT/'decisions'/f'{key}.json',rec);event('pair_adjudicated',pair_key=key,status=rec['status'],extra_calls=len(extra))
def nat_batch(items):
 payload=[];refs={}
 for f in items:
  v=natural_visible(f);key=digest([f['family_id'],v]);alias=digest(['natural',key])[:20];payload.append({'id':alias,**v});refs[alias]=(f,key,v)
 r=dispatch({'stage':'global_natural_v1','payload':{'families':payload},'instruction':NAT_INSTRUCTION,'output_schema':NAT_SCHEMA},OUT,'gpt-6.1-terra','low');rows=response(r,refs);saved=[]
 for alias,(f,key,v) in refs.items():
  row=rows.get(alias) if rows else None;rec={'family_id':f['family_id'],'key':key,'first_raw':r.get('path'),'first':row,'status':'pending'}
  def good(x):
   if not x or x['history'] not in ('H1','H2'):return False
   h=next(z for z in v['histories'] if z['history']==x['history']);return quoted(x['quote_a'],h) and quoted(x['quote_b'],h) and x['quote_a']!=x['quote_b']
  if row and row['severe'] and row['confidence']>=.9 and good(row):
   rr=dispatch({'stage':'global_natural_confirm_v1','payload':{'families':[{'id':alias,**v}]},'instruction':NAT_INSTRUCTION,'output_schema':NAT_SCHEMA},OUT,'gpt-6-astra','low')
   rows2=response(rr,[alias]);z=rows2.get(alias) if rows2 else None;rec.update(second_raw=rr.get('path'),second=z)
   if z and z['severe'] and z['confidence']>=.9 and good(z):rec['status']='confirmed_severe'
  elif row and not row['severe'] and row['confidence']>=.9:rec['status']='clear'
  atomic(OUT/'natural'/f'{key}.json',rec);saved.append(rec)
 return saved
def exclusions(finalize_unresolved=False):
 # Other writers may not use our lock: optimistic reread before replace and verify after.
 additions={}
 for q in (OUT/'decisions').glob('*.json'):
  x=read(q,{})
  if x.get('status')=='confirmed_duplicate':additions[x['b']]={'reason':'two independent blind reviews confirm concrete story duplication','related_family_id':x['a'],'source':str(q.relative_to(ROOT))}
 for q in (OUT/'natural').glob('*.json'):
  x=read(q,{})
  if x.get('status')=='confirmed_severe':additions[x['family_id']]={'reason':'two independent blind reviews confirm severe history state contradiction','source':str(q.relative_to(ROOT))}
 if finalize_unresolved:
  try:
   active={f['family_id'] for f in snapshot()}-set(read(RUN/'exclusions.json',{}))-set(additions)
   for q in sorted((OUT/'decisions').glob('*.json')):
    x=read(q,{})
    if x.get('status')=='pending' and x.get('a') in active and x.get('b') in active:
     additions[x['b']]={'reason':'unresolved global novelty, not confirmed duplicate; conservative final quarantine','related_family_id':x['a'],'source':str(q.relative_to(ROOT))};active.discard(x['b'])
  except Exception as e:event('final_quarantine_error',error=repr(e))
 path=RUN/'exclusions.json'
 with (OUT/'exclusions.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  for _ in range(5):
   old=read(path,{});new=dict(old)
   for k,v in additions.items():new.setdefault(k,v)
   if old==new:return
   if read(path,{})!=old:continue
   atomic(path,new)
   if all(k in read(path,{}) for k in new):event('exclusions_merged',added=sorted(set(new)-set(old)));return
  event('exclusions_merge_conflict',pending=list(additions))
def top_pairs(fs):
 # Sparse trigram TF-IDF with postings, keeping only the global top 30 in memory.
 docs=[];df=collections.Counter()
 for f in fs:
  text=re.sub(r'[^\u4e00-\u9fffA-Za-z0-9]','',flat(visible(f)));doc=collections.Counter(text[i:i+3] for i in range(len(text)-2));docs.append(doc);df.update(doc.keys())
 inv=collections.defaultdict(list);norms=[];heap=[];n=len(fs)
 for i,doc in enumerate(docs):
  vec={t:(1+math.log(c))*(1+math.log((1+n)/(1+df[t]))) for t,c in doc.items()};norm=math.sqrt(sum(w*w for w in vec.values())) or 1;norms.append(norm);scores=collections.defaultdict(float)
  for t,w in vec.items():
   for j,q in inv[t]:scores[j]+=w*q
  for j,val in scores.items():
   score=val/(norm*norms[j]);item=(score,j,i)
   if len(heap)<30:heapq.heappush(heap,item)
   elif item>heap[0]:heapq.heapreplace(heap,item)
  for t,w in vec.items():inv[t].append((i,w))
 return [(score,fs[a],fs[b]) for score,a,b in sorted(heap,reverse=True)]
def run_batch(fs,final=False):
 started=time.time();pairs=top_pairs(fs);sample=random.Random(digest([f['family_id'] for f in fs])).sample(fs,min(8,len(fs)));tasks=[];allkeys=[];natkeys=[]
 for score,a,b in pairs:
  key=pair_key(a,b);allkeys.append(key)
  existing=read(OUT/'decisions'/f'{key}.json',{})
  if not existing:tasks.append((a,b,key))
 unseen=[]
 for f in sample:
  key=digest([f['family_id'],natural_visible(f)]);natkeys.append(key)
  if not (OUT/'natural'/f'{key}.json').exists():unseen.append(f)
 batchid=digest({'ids':[f['family_id'] for f in fs],'final':final})[:20];event('batch_started',id=batchid,count=len(fs),new_pairs=len(tasks),new_histories=len(unseen),final=final)
 with ThreadPoolExecutor(max_workers=4) as pool:
  jobs=[pool.submit(pair_batch,tasks[i:i+5]) for i in range(0,len(tasks),5)]+[pool.submit(nat_batch,unseen[i:i+4]) for i in range(0,len(unseen),4)]
  for job in as_completed(jobs):
   try:job.result()
   except Exception as e:event('worker_error',error=repr(e))
   exclusions()
  # Preserve failed calls explicitly as pending instead of losing their review unit.
  for a,b,key in tasks:
   q=OUT/'decisions'/f'{key}.json'
   if not q.exists():atomic(q,{'pair_key':key,'a':a['family_id'],'b':b['family_id'],'payload_hashes':[digest(visible(a)),digest(visible(b))],'first':None,'status':'pending','error':'primary worker failed'})
  for f in unseen:
   key=digest([f['family_id'],natural_visible(f)]);q=OUT/'natural'/f'{key}.json'
   if not q.exists():atomic(q,{'family_id':f['family_id'],'key':key,'first':None,'status':'pending','error':'primary worker failed'})
  # Revisit all unresolved pairs still in this snapshot, including earlier checkpoints.
  byid={f['family_id']:f for f in fs};pending_jobs=[]
  for q in (OUT/'decisions').glob('*.json'):
   x=read(q,{})
   if x.get('status')=='pending' and x.get('a') in byid and x.get('b') in byid :
    pending_jobs.append(pool.submit(adjudicate_pending,x,byid[x['a']],byid[x['b']]))
  for job in as_completed(pending_jobs):
   try:job.result()
   except Exception as e:event('adjudication_error',error=repr(e))
   exclusions()
 exclusions();pstatus=[read(OUT/'decisions'/f'{x}.json',{'status':'missing'})['status'] for x in allkeys];nstatus=[read(OUT/'natural'/f'{x}.json',{'status':'missing'})['status'] for x in natkeys]
 pending=sum(x in ('pending','missing') for x in pstatus+nstatus)
 result={'id':batchid,'count':len(fs),'final':final,'snapshot_hash':digest([(f['family_id'],digest(visible(f))) for f in fs]),'pair_keys':allkeys,'natural_keys':natkeys,'pair_status':pstatus,'natural_status':nstatus,'pending':pending,'seconds':round(time.time()-started)}
 atomic(OUT/'batches'/f'{batchid}.json',result);atomic(OUT/'latest.json',result);event('batch_finished',**result);return result
def snapshot():
 with (RUN/'families.jsonl').open(encoding='utf-8') as f:return [x for line in f if line.strip() and (x:=json.loads(line)).get('status')=='audited']
def refill_if_required(fs):
 # Explicitly authorized exception: never bypass maintenance or non-target stops.
 if (RUN/'STOP_AFTER_DRAIN').exists():return
 state=read(RUN/'state.json',{});reason=state.get('stop_reason')
 try:
  pid=int((RUN/'production.pid').read_text().strip());os.kill(pid,0);return
 except ProcessLookupError:pass
 except (OSError,ValueError):return
 if reason!='target reached':
  if reason:atomic(OUT/'NEEDS_ATTENTION',{'reason':'generator stopped for a non-target reason; no automatic restart','stop_reason':reason})
  return
 for proc in Path('/proc').iterdir():
  if not proc.name.isdigit():continue
  try:
   args=(proc/'cmdline').read_bytes().split(b'\0')
   if any(a.endswith(b'/fast_generate.py') or a==b'data_factory/fast_generate.py' for a in args) and any(a in (b'runs/train5000-live',str(RUN).encode()) for a in args):return
  except OSError:continue
 excluded=read(RUN/'exclusions.json',{});intersection=[f['family_id'] for f in fs if f['family_id'] in excluded];remaining=len(fs)-len(intersection)
 if remaining>=5000:return
 if not intersection:
  atomic(OUT/'NEEDS_ATTENTION',{'reason':'target stopped below 5000 without published/excluded intersection; no automatic restart','remaining':remaining});return
 launch=read(RUN/'launch.json',{});argv=launch.get('argv',[])
 # Only this project's executable and enumerated flags, with exactly the intended target/run.
 if len(argv)<3 or argv[:3]!=['/usr/bin/python3','-u','data_factory/fast_generate.py']:raise ValueError('unsafe launch prefix')
 allowed={'--run-dir','--target','--concurrency','--start-index','--seed-snapshot','--import-snapshot','--limit-new'};options={};i=3
 while i<len(argv):
  k=argv[i]
  if k not in allowed or i+1>=len(argv):raise ValueError('unsafe launch argument')
  options.setdefault(k,[]).append(argv[i+1]);i+=2
 if options.get('--run-dir')!=['runs/train5000-live'] or options.get('--target')!=['5000'] or len(options.get('--concurrency',[]))!=1 or not 1<=int(options['--concurrency'][0])<=64 or '--limit-new' in options:raise ValueError('launch options failed validation')
 if (ROOT/'data_factory/fast_generate.py').resolve()!=(ROOT/'data_factory/fast_generate.py').absolute():raise ValueError('unexpected generator path')
 if (RUN/'STOP_AFTER_DRAIN').exists() or read(RUN/'state.json',{}).get('stop_reason')!='target reached':return
 out=(OUT/'refill.log').open('a',encoding='utf-8');proc=subprocess.Popen(argv,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT,start_new_session=True);out.close()
 tmp=RUN/('production.pid.'+str(os.getpid())+'.tmp');tmp.write_text(str(proc.pid)+'\n');os.replace(tmp,RUN/'production.pid')
 with (RUN/'launch_history.jsonl').open('a',encoding='utf-8') as f:f.write(canon({'time':time.time(),'pid':proc.pid,'argv':argv,'reason':'target reached but confirmed exclusions reduce published eligible count below 5000','excluded_published':intersection})+'\n')
 event('refill_started',pid=proc.pid,excluded_published=intersection)
def final_fingerprint(fs):
 # Avoid rescanning a 5k corpus every 45 seconds when manual review is pending.
 entries=[]
 for directory in ('decisions','natural'):
  for q in (OUT/directory).glob('*.json'):
   try:entries.append((directory,q.name,q.stat().st_mtime_ns))
   except FileNotFoundError:pass
 return digest({'ids':[f['family_id'] for f in fs],'exclusions':read(RUN/'exclusions.json',{}),'records':sorted(entries)})
def main():
 state=read(OUT/'watch_state.json',{'last_count':0});event('watch_started',state=state)
 while True:
  try:
   if (ROOT/'runs/CLI_QUOTA_EXHAUSTED.json').exists():
    atomic(OUT/'quota_paused.json',{'status':'quota_blocked','utc_epoch':time.time(),'raw_preserved':True});time.sleep(45);continue
   exclusions();fs=snapshot();refill_if_required(fs);n=len(fs);final=n>=5000
   if n and (not state.get('initialized') or n>=state.get('last_count',0)+250 or (final and state.get('final_attempt')!=final_fingerprint(fs))):
    result=run_batch(fs,final);state.update(initialized=True,last_count=n)
    if final:
     exclusions(finalize_unresolved=True)
     after=snapshot();refill_if_required(after);excluded=read(RUN/'exclusions.json',{});remaining=[f for f in after if f['family_id'] not in excluded]
     active={f['family_id'] for f in remaining}; unresolved=[]
     for q in (OUT/'decisions').glob('*.json'):
      x=read(q,{})
      if x.get('status')=='pending' and x.get('a') in active and x.get('b') in active:unresolved.append(str(q))
     for q in (OUT/'natural').glob('*.json'):
      x=read(q,{})
      if x.get('status')=='pending' and x.get('family_id') in active:unresolved.append(str(q))
     if len(remaining)>=5000 and not result['pending'] and not unresolved and digest([f['family_id'] for f in after])==digest([f['family_id'] for f in fs]):
      state['final_hash']=digest([f['family_id'] for f in fs]);atomic(OUT/'COMPLETE',{'status':'reviewed','batch':result['id'],'count':len(remaining),'pending':0});event('complete',count=len(remaining));atomic(OUT/'watch_state.json',state);return
     event('final_not_complete',remaining=len(remaining),pending=result['pending'],unresolved_prior=len(unresolved));state['final_attempt']=final_fingerprint(after)
    atomic(OUT/'watch_state.json',state)
  except Exception as e:event('watch_error',error=repr(e))
  time.sleep(45)
if __name__=='__main__':main()
