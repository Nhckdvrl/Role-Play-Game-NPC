#!/usr/bin/env python3
"""Up to two auditable local repairs followed by independent re-review."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from agent_dispatch import dispatch
from factory import actor_messages

HERE = Path(__file__).resolve().parent


def read(p): return json.loads(p.read_text(encoding='utf-8'))
def digest(x): return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def write(p, x):
    p.parent.mkdir(parents=True,exist_ok=True)
    temp=p.with_suffix(p.suffix+'.tmp');temp.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');temp.replace(p)
def invoke(run, script, *args): subprocess.run([sys.executable,str(HERE/script),'--run-dir',str(run),*args],check=True)


def snapshot(run, directory):
    """Move previous publication aside before immutable new release is assembled."""
    directory.mkdir(parents=True,exist_ok=True)
    for name in ('families.jsonl','needs_review.jsonl','adjudicated','jobs','review_decisions.json'):
        source=run/name; target=directory/name
        if source.exists():
            if target.exists(): raise RuntimeError(f'archive target exists: {target}')
            shutil.move(str(source),str(target))


def repair(run, round_dir):
    pub=round_dir/'publication'; reports=read(pub/'review_decisions.json')
    indices=read(run/'indices'/'adjudication.json')
    prior=round_dir/'drafts_before'; prior.mkdir(parents=True,exist_ok=True)
    paths=sorted((run/'drafts').glob('RCD-*.json'))
    for p in paths:
        target=prior/p.name
        if not target.exists(): shutil.copy2(p,target)
    changes=[]; unresolved=[]
    for report in reports:
        if report['status']!='needs_review': continue
        fid=report['family_id']; path=run/'drafts'/f'{fid}.json'; family=read(path); original=deepcopy(family)
        record=indices[fid]['result']; annotations={a['candidate_id']:a for a in record['candidates']}
        issues=report.get('issues',[])
        if not record.get('history_coherent',True):
            # Only the explicit recent resistant-tail defect is eligible for this repair.
            history_issues=[i for i in issues if any(term in i for term in ('hr','末段','尾段','近期姿态'))]
            if family['history_mode']=='natural' and history_issues:
                history=next((h for h in family['histories'] if h['id']=='hr' and h['posture']=='resistant_recent'),None)
                if history and len(history['messages'])>=6:
                    payload={'persona':family['persona']['natural_profile'],'common_context':family['common_visible_context'],
                             'history':history['messages'],'review_criticism':history_issues}
                    schema={'type':'object','properties':{'messages':{'type':'array','items':{'type':'object','properties':{'role':{'type':'string','enum':['user','assistant']},'content':{'type':'string'}},'required':['role','content'],'additionalProperties':False}},'concerns':{'type':'array','items':{'type':'string'}}},'required':['messages','concerns'],'additionalProperties':False}
                    instruction=('只重写这段历史最后6条消息，严格3个user/assistant往返、user起assistant终；前文不可改。'
                        '围绕一件实际需要的小分歧，角色最后真实不采纳请求或坚持原方案；不能由玩家主动撤回而角色只附和。'
                        '不重开已收拾的物品凑轮，事项闭合，不离场，不改变当前主线许可、物料、时间、听众意愿或关系。'
                        '不得创造对当前决定有影响的事实和承诺；只返回替换的6条消息。')
                    r=dispatch({'stage':'curation_history_tail','payload':payload,'instruction':instruction,'output_schema':schema},run)
                    if r['status']!='success': raise RuntimeError('history repair call failed')
                    tail=r['result']['messages']
                    if len(tail)!=6 or any(m['role']!=('user' if i%2==0 else 'assistant') or not m['content'].strip() for i,m in enumerate(tail)):
                        unresolved.append({'family_id':fid,'reason':'invalid history tail output','path':r['path']})
                    else:
                        old=history['messages'][-6:];history['messages'][-6:]=tail
                        changes.append({'family_id':fid,'field':'hr.messages[-6:]','before':old,'after':tail,'before_hash':digest(old),'after_hash':digest(tail),'source_attempt':r['path'],'concerns':r['result']['concerns']})
                else: unresolved.append({'family_id':fid,'reason':'resistant history unavailable'})
            else: unresolved.append({'family_id':fid,'reason':'history issue not eligible for local tail repair'})
        for branch in family['branches']:
            for candidate in branch['candidates']:
                cid=candidate['id']; annotation=annotations.get(cid)
                if not annotation: continue
                relevant=[i for i in issues if i.startswith(cid+':')]
                evidence_defect=bool(annotation['decision_correct'] and not annotation['evidence_ok'] and any('ungrounded' in i for i in relevant))
                wrong_grid=any('actual grid differs from intended' in i for i in relevant)
                if not (evidence_defect or wrong_grid): continue
                history=next(h for h in family['histories'] if h['id']==candidate['history_id'])
                payload={'messages':actor_messages(family,history,branch),'old_candidate':candidate['text'],
                         'adjudication_rationale':annotation['rationale'],
                         'required_decision':family['decision_inventory'][candidate['intended']['decision_id']],
                         'style':candidate['intended']['style']}
                schema={'type':'object','properties':{'text':{'type':'string'},'concerns':{'type':'array','items':{'type':'string'}}},'required':['text','concerns'],'additionalProperties':False}
                instruction=('只重写这一条自然角色回复，保持指定主决定与表达风格；不得编造地图方位、数字、过去事件或未经核实的事实。'
                             '针对反馈删除无据细节，可自然指向已有的图面或安排；不输出标签或解释。'
                             '正确与错误表达均自然可信，核验应明确条件、提出实际核验而不提前承诺。')
                r=dispatch({'stage':'curation_candidate','payload':payload,'instruction':instruction,'output_schema':schema},run)
                if r['status']!='success': raise RuntimeError('candidate repair call failed')
                text=r['result']['text']
                if not text.strip() or text==candidate['text']:
                    unresolved.append({'family_id':fid,'candidate_id':cid,'reason':'empty or unchanged candidate','path':r['path']});continue
                old=candidate['text'];candidate['text']=text
                changes.append({'family_id':fid,'candidate_id':cid,'field':'candidate.text','before':old,'after':text,'before_hash':digest(old),'after_hash':digest(text),'source_attempt':r['path'],'concerns':r['result']['concerns']})
        if family!=original: write(path,family)
    write(round_dir/'patches.json',{'changes':changes,'unresolved':unresolved})
    return changes


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-dir',type=Path,required=True)
    p.add_argument('--concurrency',type=int,default=6);p.add_argument('--no-initial-adjudication',action='store_true')
    a=p.parse_args();run=a.run_dir.resolve()
    if not 1<=a.concurrency<=8:p.error('concurrency must be between 1 and 8')
    if not a.no_initial_adjudication and not (run/'review_decisions.json').exists():
        invoke(run,'adjudicate_release.py','--concurrency',str(min(4,a.concurrency)),'--no-local-repair')
    for n in (1,2):
        rd=run/'curation'/f'round{n}'; marker=rd/'round_complete.json'
        if marker.exists(): continue
        # Recover an interrupted round from the original archived state and cached calls.
        pub=rd/'publication'
        if not (pub/'review_decisions.json').exists(): snapshot(run,pub)
        if not (pub/'review_decisions.json').exists(): raise RuntimeError('no publication to curate')
        backup=rd/'drafts_before'
        if backup.exists() and not (rd/'patches.json').exists():
            for f in backup.glob('RCD-*.json'): shutil.copy2(f,run/'drafts'/f.name)
        changes=read(rd/'patches.json')['changes'] if (rd/'patches.json').exists() else repair(run,rd)
        if not changes:
            # Restore publication unchanged when no safe local repair exists.
            for item in pub.iterdir():
                if not (run/item.name).exists(): shutil.copytree(item,run/item.name) if item.is_dir() else shutil.copy2(item,run/item.name)
            write(marker,{'status':'no_safe_repairs'});return
        if not (run/'review_decisions.json').exists():
            invoke(run,'produce_pilot.py','--stage','blind','--concurrency',str(a.concurrency))
            invoke(run,'adjudicate_release.py','--concurrency',str(min(4,a.concurrency)),'--no-local-repair')
        quality=subprocess.run([sys.executable,str(HERE/'quality.py'),str(run/'families.jsonl'),'--report',str(rd/'quality.json')])
        if quality.returncode:
            snapshot(run,rd/'quality_failed_publication')
            raise RuntimeError('quality check failed; publication quarantined')
        write(marker,{'status':'complete','changes':len(changes)})
        reports=read(run/'review_decisions.json')
        if all(r['status']=='audited' for r in reports): return
    print('Local repair limit reached; remaining families retain needs_review.',flush=True)


if __name__=='__main__': main()
