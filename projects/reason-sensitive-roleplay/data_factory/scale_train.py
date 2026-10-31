#!/usr/bin/env python3
"""Resume bounded train shards; only audited, structurally valid families count."""
import argparse
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import re
from pathlib import Path
import subprocess
import sys

from jsonschema import Draft202012Validator
from agent_dispatch import dispatch
from factory import validate, actor_messages, digest

HERE = Path(__file__).resolve().parent
PILOT = HERE.parent / 'runs/pilot12-20261101'


def read(p, default=None):
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default


def write(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    temp = p.with_suffix(p.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    temp.replace(p)


def rows(p):
    return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s.strip()] if p.exists() else []


def stage_complete(shard, stage, count):
    """Resume an existing stage without rewriting its immutable original prompts."""
    directory=shard/('with_histories' if stage=='histories' else 'drafts')
    paths=sorted(directory.glob('RCD-*.json'))
    if len(paths)!=count:return False
    families=[read(p) for p in paths]
    if stage=='histories':
        return all(len(f['histories'])==2 and all(h['messages'] and len(h['messages'])%2==0 for h in f['histories']) for f in families)
    try:
        for f in families:validate(f)
        if stage=='candidates':return True
        index=read(shard/'indices/blind.json',{}) or {}
        for f in families:
            for h in f['histories']:
                for b in f['branches']:
                    key=f['family_id']+'::'+h['id']+'::'+b['id'];payload={'messages':actor_messages(f,h,b)}
                    meta=read(Path(index[key]['path'])/'metadata.json',{})
                    if index[key]['status']!='success' or meta.get('payload_sha256')!=digest(payload):return False
                    for c in b['candidates']:
                        if c['history_id']!=h['id']:continue
                        meta=read(Path(index[c['id']]['path'])/'metadata.json',{})
                        if index[c['id']]['status']!='success' or meta.get('payload_sha256')!=digest({**payload,'candidate_text':c['text']}):return False
        return True
    except (ValueError,KeyError,TypeError,OSError):return False


def write_rows(p, values):
    temp = p.with_suffix('.tmp')
    temp.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in values),encoding='utf-8')
    temp.replace(p)


MOTIVES = ('利润/信誉','求知/程序','自尊/交易','独立/协作','忠诚/规则','承诺/效率','创作/配合')
REQUESTS = ('信息交易','协作分工','邀约','修正','议价','创作','关系承诺')

def nearby(summary, previous):
    def grams(text):
        chars = ''.join(c for c in text if '\u4e00' <= c <= '\u9fff')
        return {chars[i:i+2] for i in range(len(chars)-1)}
    query = grams(summary)
    def similarity(text):
        other = grams(text); union = query | other
        return len(query & other) / len(union) if union else 0
    ranked = sorted(enumerate(previous), key=lambda x: (-similarity(x[1]), -x[0]))[:30]
    ids = {i for i, _ in ranked} | set(range(max(0, len(previous)-10), len(previous)))
    return [previous[i] for i in sorted(ids)]

def progress(root, accepted, target, shard):
    state=read(root/'state.json',{}) or {}
    body=f'本运行已审查通过 Train 故事族：{accepted}/{target}。状态：{state.get("status","running")}。计划与草稿不计入。'
    if state.get('status')!='running' and state.get('stop_reason'):body+='\n\n停止原因：'+state['stop_reason']
    text='# 数据进度\n\n'+body+'\n'
    (shard/'DATA_PROGRESS.md').write_text(text,encoding='utf-8')
    (root/'DATA_PROGRESS.md').write_text(text,encoding='utf-8')
    project_progress=HERE.parent/'DATA_PROGRESS.md'
    start,end='<!-- TRAIN_LIVE_START -->','<!-- TRAIN_LIVE_END -->'
    current=project_progress.read_text(encoding='utf-8') if project_progress.exists() else '# 数据进度\n'
    section=start+'\n\n'+body+'\n\n'+end
    if start in current and end in current:
        current=current.split(start,1)[0]+section+current.split(end,1)[1]
    else:current+='\n'+section+'\n'
    temporary=project_progress.with_name('.DATA_PROGRESS.train.tmp')
    temporary.write_text(current,encoding='utf-8');temporary.replace(project_progress)


def design_schema():
    schema = read(HERE/'story_family.schema.json')
    schema.pop('$schema', None)
    props = schema['properties']
    props['blocks']['maxItems'] = 0
    props['histories']['maxItems'] = 2
    props['histories']['items']['properties']['messages']['minItems'] = 0
    props['histories']['items']['properties']['messages']['maxItems'] = 0
    props['branches']['maxItems'] = 6
    props['branches']['items']['properties']['candidates']['minItems'] = 0
    props['branches']['items']['properties']['candidates']['maxItems'] = 0
    text={'type':'string','minLength':1}
    briefs={'type':'object','properties':{'natural':{'type':'object','properties':{'hc':{'type':'string'},'hr':{'type':'string'}},'required':['hc','hr'],'additionalProperties':False},'blocks':{'type':'array','items':{'type':'object','properties':{'id':text,'posture':{'enum':['cooperate','resist']},'event':text,'exchanges':{'type':'integer'}},'required':['id','posture','event','exchanges'],'additionalProperties':False}}},'required':['natural','blocks'],'additionalProperties':False}
    node={'type':'object','properties':{'good':text,'bad':text,'bad_decision_id':text},'required':['good','bad','bad_decision_id'],'additionalProperties':False}
    return {'type':'object','properties':{'family':schema,'normalized_briefs':briefs,'node_decision_briefs':{'type':'object','properties':{f'B{i}':node for i in range(1,7)},'required':[f'B{i}' for i in range(1,7)],'additionalProperties':False},'mechanism_summary':text},'required':['family','normalized_briefs','node_decision_briefs','mechanism_summary'],'additionalProperties':False}


def transport_schema():
    schema = deepcopy(design_schema())
    family = schema['properties']['family']['properties']
    text = {'type': 'string'}
    family['decision_inventory'] = {'type': 'array', 'items': {
        'type': 'object', 'properties': {'id': text, 'description': text},
        'required': ['id', 'description'], 'additionalProperties': False}}
    def convert(node):
        if isinstance(node, list):
            for item in node: convert(item)
        elif isinstance(node, dict):
            if 'const' in node: node['enum'] = [node.pop('const')]
            if 'enum' in node and 'type' not in node:
                values = node['enum']
                types = {type(v) for v in values}
                if types == {str}: node['type'] = 'string'
                elif types == {int}: node['type'] = 'integer'
                elif types == {bool}: node['type'] = 'boolean'
                else: raise ValueError('unsupported enum types')
            for key in ('minProperties', 'maxProperties', 'minItems', 'maxItems', 'minLength', 'maxLength', 'minimum', 'maximum', 'title'):
                node.pop(key, None)
            if node.get('type') == 'object' and node.get('additionalProperties') is not False:
                raise ValueError('dynamic object unsupported by transport')
            for value in node.values(): convert(value)
    convert(schema)
    return schema


def canonical_result(result):
    result = deepcopy(result)
    inventory = result['family']['decision_inventory']
    if isinstance(inventory, list):
        ids = [item['id'] for item in inventory]
        if len(ids) != len(set(ids)): raise ValueError('duplicate decision_inventory ID')
        result['family']['decision_inventory'] = {item['id']: item['description'] for item in inventory}
    return result


def normalize_edges(result):
    result = deepcopy(result)
    changes = []
    for index, edge in enumerate(result['family']['edges']):
        for key in ('source', 'target'):
            old = edge[key]
            if re.fullmatch(r'(hc|hr):B[1-6]', old):
                new = old.replace(':', '::', 1)
                edge[key] = new
                changes.append({'edge_index': index, 'field': key, 'original': old, 'normalized': new})
    return result, changes


def transport_result(result):
    result = deepcopy(result)
    inv = result['family']['decision_inventory']
    if isinstance(inv, dict): result['family']['decision_inventory'] = [{'id': k, 'description': v} for k, v in inv.items()]
    return result


def check(result, fid, group):
    Draft202012Validator(transport_schema()).validate(transport_result(result))
    f=result['family']; Draft202012Validator(design_schema()).validate(result)
    if (f['family_id'],f['split_group_id'],f['split'],f['status']) != (fid,group,'train','draft'): raise ValueError('identity or split mismatch')
    if f['provenance']['designer_model']!='gpt-6-astra': raise ValueError('wrong designer provenance')
    if {h['id'] for h in f['histories']} != {'hc','hr'}: raise ValueError('history IDs must be hc/hr')
    if {h['id']:h['posture'] for h in f['histories']} != {'hc':'cooperative_recent','hr':'resistant_recent'}: raise ValueError('history posture mismatch')
    if {b['id'] for b in f['branches']} != {f'B{i}' for i in range(1,7)}: raise ValueError('branch IDs')
    if {b['kind'] for b in f['branches']} != {'routine','pressure','invalid_reason','generic_incentive','valid_reason','insufficient_evidence'}: raise ValueError('branch kinds')
    inv=f['decision_inventory']; nodes={h['id']+'::'+b['id']:b for h in f['histories'] for b in f['branches']}
    for b in f['branches']:
        if not set(b['allowed_decisions']) <= inv.keys(): raise ValueError('unknown allowed decision')
        bad=result['node_decision_briefs'][b['id']]['bad_decision_id']
        if bad not in inv or bad in b['allowed_decisions']: raise ValueError('bad decision invalid')
        if b['kind']=='insufficient_evidence' and (not b['missing_condition_ids'] or not b['verification_routes'] or any(not set(r)<=set(b['missing_condition_ids']) for r in b['verification_routes'])): raise ValueError('invalid B6 route')
    for e in f['edges']:
        if e['source'] not in nodes or e['target'] not in nodes or e['source']==e['target']: raise ValueError('invalid edge')
        if any(a not in nodes[e['source']]['allowed_decisions'] or b not in nodes[e['target']]['allowed_decisions'] for a,b in e['allowed_pairs']): raise ValueError('invalid edge pair')
    for b in f['branches']:
        if not any(e['kind']=='preserve' and {e['source'],e['target']}=={'hc::'+b['id'],'hr::'+b['id']} for e in f['edges']): raise ValueError('missing preserve')
    for h in ('hc','hr'):
        if sum(e['kind']=='change' and e['source'].startswith(h+'::') and e['target'].startswith(h+'::') for e in f['edges'])<2: raise ValueError('missing change edges')
    blocks=result['normalized_briefs']['blocks']
    if f['history_mode']=='exact_permutation':
        if {b['id'] for b in blocks}!={'C1','C2','C3','R1','R2','R3'}: raise ValueError('missing block briefs')
        byid={b['id']:b for b in blocks}
        for bid,n in zip(['R1','R2','R3','C1','C2','C3'],[2,4,3,3,2,4]):
            if byid[bid]['exchanges']!=n or byid[bid]['posture'] != ('resist' if bid[0]=='R' else 'cooperate'): raise ValueError('incorrect block plan')
    elif blocks: raise ValueError('natural history should not have blocks')
    elif not all(result['normalized_briefs']['natural'][h].strip() for h in ('hc','hr')): raise ValueError('natural history briefs missing')


def sanitize_actor_fields(result, shard):
    """Render each branch in isolation; retain source evidence as invisible ledger."""
    family = deepcopy(result['family'])
    fid = family['family_id']
    schema = {'type':'object','properties':{'visible_observation':{'type':'string'},
              'concerns':{'type':'array','items':{'type':'string'}}},
              'required':['visible_observation','concerns'],'additionalProperties':False}
    instruction = ('只重写当前情境的角色可见旁白。保留原旁白及可见证据中的全部必要具体事实，必要时将可见证据事实合入旁白；'
                   '不得新增事实或把玩家声称变成已核验事实。保留未知与缺失，不能自行核实。'
                   '删去作者推理、充分条件是否满足的结论、无效理由评判、研究编号、分支类型、答案和内部条件ID；'
                   '不写角色回复，不引用其他分支。简洁自然，不确定是否能保留的事实写入concerns。')
    def one(branch):
        visible = [e['text'] for e in branch['evidence'] if e['visible']]
        payload = {'persona':family['persona']['natural_profile'],'common_context':family['common_visible_context'],
                   'visible_observation':branch['visible_observation'],'player_turn':branch['player_turn'],
                   'visible_evidence':visible}
        call = dispatch({'stage':'actor_sanitize','payload':payload,'instruction':instruction,'output_schema':schema},
                        shard,model='gpt-6.1-terra',effort='low')
        if call['status'] != 'success': raise RuntimeError('actor sanitization call failed: '+branch['id'])
        raw = json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
        return branch['id'], call, hashlib.sha256(raw).hexdigest()
    results={}
    with ThreadPoolExecutor(max_workers=6) as pool:
        pending=[pool.submit(one,b) for b in family['branches']]
        for future in as_completed(pending):
            bid, call, payload_hash = future.result(); results[bid]=(call,payload_hash)
    changes=[]
    # High-precision checks: do not infer safety from an empty list; independent review remains required.
    research = re.compile(r'(?i)(?:\b(?:B[1-6]|H_coop_end|H_resist_end|C_[A-Za-z0-9_]+)\b|分支(?:编号|类型|[一二三四五六1-6])|作者答案|充分条件(?:已|均|全部)|唯一缺失条件)')
    findings=[]
    for b in family['branches']:
        call, digest = results[b['id']]; old=b['visible_observation']; new=call['result']['visible_observation']
        if not new.strip(): raise ValueError('empty sanitized observation: '+b['id'])
        b['visible_observation']=new
        for e in b['evidence']: e['visible']=False
        changes.append({'branch_id':b['id'],'source_payload_sha256':digest,
                        'original_observation_sha256':hashlib.sha256(old.encode()).hexdigest(),
                        'sanitized_observation_sha256':hashlib.sha256(new.encode()).hexdigest(),
                        'source_attempt':call['path'],'concerns':call['result']['concerns']})
        for field,text in (('visible_observation',new),('player_turn',b['player_turn'])):
            for match in research.finditer(text): findings.append({'branch_id':b['id'],'field':field,'match':match.group(0)})
    for field,text in (('natural_profile',family['persona']['natural_profile']),('common_visible_context',family['common_visible_context'])):
        for match in research.finditer(text): findings.append({'field':field,'match':match.group(0)})
    write(shard/'sanitization'/f'{fid}.json',{'changes':changes,'research_marker_findings':findings,
          'note':'Mechanical marker scan only; no semantic review has been performed.'})
    if findings: raise ValueError('research markers found in actor fields: '+fid)
    return family


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root-dir',type=Path,required=True);p.add_argument('--target',type=int,default=5000)
    p.add_argument('--shard-size',type=int,default=10);p.add_argument('--concurrency',type=int,default=8)
    p.add_argument('--design-only',action='store_true');a=p.parse_args()
    if not 1<=a.target<=5000 or not 1<=a.shard_size<=a.target or not 1<=a.concurrency<=8: p.error('invalid target, shard size or concurrency')
    root=a.root_dir.resolve();root.mkdir(parents=True,exist_ok=True)
    state=read(root/'state.json',{'next_offset':0,'shards':[],'coverage':[],'status':'running'})
    style=read(PILOT/'style_guidance.json',{}).get('principles',[])
    instruction=('覆盖多样互动，不都写安全守门人；金钱有时可接受，有效理由可停止或撤回。设计标签为计划，不是观察到的覆盖。'
        '设计原创中文角色条件决策族。自然人设表达当前意愿、充分条件、无其他阻碍；未知时写可执行核验。'
        'visible_observation和player_turn均独立可读，禁止提到其他分支编号、分支类型或作者答案，不引用其他分支。'
        '旁白事实与玩家声称分开；B1为公开日常交流，不能将合理保密当错误；错误决定必须具体且无未知前提。'
        '六分支、跨史6 preserve及每史至少2 change；允许有效理由使人停止或改方案。'
        'edges的source和target必须用双冒号连接历史和分支，如hc::B1、hr::B1，不能使用单冒号。'
        'B6的verification_routes每条是missing_condition_ids的非空子集，填写缺失条件ID而不是核验动作ID；核验动作写teacher_scaffold。'
        'history_mode严格遵循输入history_mode_requirement。自然史各18轮围绕一个真实目的与2-3个相邻小事，最近3轮对应姿态，所有事项闭合且不改变主线资源关系。'
        'natural模式时normalized_briefs.blocks必须为空数组，natural.hc/hr仅写简要事件计划，不写示例对话、角色台词或逐轮内容。'
        'exact_permutation模式时natural.hc/hr留空，blocks仅提供事件简述，不写对话。'
        '精确块按R1,R2,R3,C1,C2,C3分别2,4,3,3,2,4轮，六块独立闭合、话题多样。'
        'histories为hc/hr且messages空，blocks与candidates空；所有标准字段齐备；designer_model必须精确为gpt-6-astra，renderer_model=pending，'
        'prompt_version=scale-v1，generation_run使用输入generation_run，seed使用输入seed；审查pending、human_review=not_sampled。'
        'decision_inventory按数组输出，每项为id和description，id不能重复。为每分支给good、bad和已有inventory中不允许的bad_decision_id。机制摘要只描述抽象目标、条件及冲突，不含人名职业。')
    review_schema={'type':'object','properties':{'novel':{'type':'boolean'},'uncertain':{'type':'boolean'},'reason':{'type':'string'}},'required':['novel','uncertain','reason'],'additionalProperties':False}
    while True:
        accepted=rows(root/'families.jsonl'); unique={f['family_id']:f for f in accepted if f.get('status')=='audited' and f.get('split')=='train'}
        if len(unique)>=a.target: state['status']='target_met';write(root/'state.json',state);progress(root,len(unique),a.target,root);return
        if state.get('status') in ('needs_calibration','needs_review'): progress(root,len(unique),a.target,root);print(state['status'],flush=True);return
        incomplete=next((s for s in state['shards'] if s['status'] in ('designing','designed','producing')),None)
        if incomplete is None:
            offset=state['next_offset'];count=min(a.shard_size,a.target-len(unique))
            incomplete={'offset':offset,'count':count,'status':'designing'};state['shards'].append(incomplete);state['next_offset']+=count;write(root/'state.json',state)
        shard=root/'shards'/f"shard-{incomplete['offset']:08d}";shard.mkdir(parents=True,exist_ok=True)
        prepared=shard/'prepared';prepared.mkdir(exist_ok=True)
        freeze={'groups':[{'family_id':f'RCD-train-{i:08d}','split_group_id':f'train-original-{i:08d}','split':'train'} for i in range(incomplete['offset'],incomplete['offset']+incomplete['count'])], 'scope':'Train groups frozen before design and rendering'}
        if not (shard/'split_freeze.json').exists(): write(shard/'split_freeze.json',freeze)
        for i in range(incomplete['offset'],incomplete['offset']+incomplete['count']):
            fid=f'RCD-train-{i:08d}';group=f'train-original-{i:08d}'
            plan=shard/'designs'/f'{fid}.json'
            if not plan.exists():
                payload={'family_id':fid,'split_group_id':group,'split':'train','seed':i,'generation_run':shard.name,
                         'history_mode_requirement':'exact_permutation' if i%5==0 else 'natural',
                         'style_principles':style,'existing_abstract_mechanisms':state['coverage'][-80:],
                         'motive_axis':MOTIVES[i % 7], 'request_type':REQUESTS[(i * 3 + 2) % 7],
                         'stream':'design_hard' if i % 10 < 3 else 'coverage'}
                task={'stage':'design','payload':payload,'instruction':instruction,'output_schema':transport_schema()}
                r=dispatch(task,shard,model='gpt-6-astra',effort='high')
                if r['status']!='success': raise RuntimeError('design call failed; raw attempts preserved')
                result, changes=normalize_edges(canonical_result(r['result']));check(result,fid,group)
                write(shard/'normalizations'/f'{fid}.json',{'source_attempt':r['path'],'changes':changes})
                write(plan,result)
            result=read(plan);check(result,fid,group)
            if not (prepared/f'{fid}.json').exists():
                task={'stage':'novelty_review','payload':{'candidate_abstract_mechanism':result['mechanism_summary'], 'persona':result['family']['persona']['natural_profile'], 'visible_branches':[{'visible_observation':b['visible_observation'],'player_turn':b['player_turn']} for b in result['family']['branches']], 'existing_abstract_mechanisms':nearby(result['mechanism_summary'],[x for x in state['coverage'] if x != result['mechanism_summary']])},'instruction':'独立审查是否是新的决定机制，而不是换职业或名字；不确定则uncertain=true。剥离所有族共有的六分支框架，比较目标排序、核心冲突、证据形式及有效条件后的行动的具体组合。novel=false必须指出前一族具体的逐项一对一同构；不能因都有条件、压力无效或未知核验便判重复。结合人物、可见分支与已有摘要，不虚称心理真值。','output_schema':review_schema}
                r=dispatch(task,shard,model='gpt-6.1-terra',effort='low')
                if r['status']!='success': raise RuntimeError('novelty call failed; raw attempts preserved')
                if not r['result']['novel'] or r['result']['uncertain']:
                    state['status']='needs_review';state['stop_reason']='novelty reviewer rejected or was uncertain: '+r['result']['reason'];incomplete['status']='needs_review';write(root/'state.json',state);progress(root,len(unique),a.target,shard);print('novelty needs review:',fid,flush=True);return
                if result['mechanism_summary'] not in state['coverage']: state['coverage'].append(result['mechanism_summary'])
                write(root/'state.json',state)
                write(prepared/f'{fid}.json',sanitize_actor_fields(result,shard))
        designs=[read(shard/'designs'/f'RCD-train-{i:08d}.json') for i in range(incomplete['offset'],incomplete['offset']+incomplete['count'])]
        write(shard/'normalized_briefs.json',{d['family']['family_id']:d['normalized_briefs'] for d in designs})
        write(shard/'node_decision_briefs.json',{d['family']['family_id']:d['node_decision_briefs'] for d in designs})
        incomplete['status']='designed';write(root/'state.json',state)
        if a.design_only: return
        incomplete['status']='producing';write(root/'state.json',state)
        for stage in ('histories','candidates','blind'):
            if stage_complete(shard,stage,incomplete['count']):
                print('Resuming completed stage:',shard.name,stage,flush=True);continue
            subprocess.run([sys.executable,str(HERE/'produce_pilot.py'),'--run-dir',str(shard),'--stage',stage,'--concurrency',str(a.concurrency)],check=True)
        if not (shard/'families.jsonl').exists(): subprocess.run([sys.executable,str(HERE/'adjudicate_release.py'),'--run-dir',str(shard),'--concurrency',str(min(4,a.concurrency))],check=True)
        for f in rows(shard/'families.jsonl'):
            validate(f)
            if f['status']=='audited' and f['split']=='train': unique[f['family_id']]=f
        write_rows(root/'families.jsonl',list(unique.values()))
        pending={f['family_id']:f for f in rows(root/'needs_review.jsonl')+rows(shard/'needs_review.jsonl')};write_rows(root/'needs_review.jsonl',list(pending.values()))
        subprocess.run([sys.executable,str(HERE/'report_run.py'),'--run-dir',str(shard)],check=True)
        progress(root,len(unique),a.target,shard)
        incomplete['status']='complete';incomplete['accepted']=len(rows(shard/'families.jsonl'));incomplete['reviewed']=incomplete['accepted']+len(rows(shard/'needs_review.jsonl'))
        completed=[s for s in state['shards'] if s['status']=='complete']
        if len(completed)>=2 and sum(s['accepted'] for s in completed[:2])/max(1,sum(s['reviewed'] for s in completed[:2]))<0.8:
            state['status']='needs_calibration';state['stop_reason']='first two shards audited acceptance below 0.8'
        write(root/'state.json',state)
        progress(root,len(unique),a.target,shard)


if __name__=='__main__':
    try: main()
    except Exception as exc:
        parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--root-dir',type=Path);parser.add_argument('--target',type=int,default=5000)
        known,_=parser.parse_known_args()
        if known.root_dir:
            path=known.root_dir.resolve()/'state.json'
            state=read(path,{}) or {}; state['status']='modelservice_or_pipeline_stopped';state['stop_reason']=str(exc);write(path,state)
            progress(known.root_dir.resolve(),len(rows(known.root_dir.resolve()/'families.jsonl')),known.target,known.root_dir.resolve())
        raise
