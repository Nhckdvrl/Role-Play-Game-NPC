"""Execute an original pilot through independent rendering and blind audit calls.

Each model call is a new CLI session. Four cells at one node are rendered together
to match length/style; every candidate is subsequently reviewed in isolation.
Author labels never enter local or candidate audit payloads.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
from agent_dispatch import dispatch
from factory import actor_messages, assemble, digest, jobs, validate, write_new
from jsonschema import Draft202012Validator

S = {'type': 'string'}
B = {'type': 'boolean'}
N = {'type': 'number', 'minimum': 0, 'maximum': 1}
def array(item): return {'type': 'array', 'items': item}
def obj(**fields): return {'type': 'object', 'properties': fields, 'required': list(fields), 'additionalProperties': False}
MESSAGE = obj(role={'enum': ['user', 'assistant']}, content=S)
SPAN = obj(message_index={'type': 'integer'}, quote=S)
HISTORY = obj(messages=array(MESSAGE), concerns=array(S))
CELLS = obj(candidates=array(obj(slot=S, text=S)), concerns=array(S))
LOCAL = obj(allowed_reactions=array(S), evidence_spans=array(SPAN), missing_conditions=array(S),
            feasible_checks=array(S), ambiguity=array(S), confidence=N)
REVIEW = obj(actual_decision=S, decision_supported=B, evidence_ok=B, evidence_spans=array(SPAN),
             naturalness=N, naturalness_reason=S, character_style_support=N,
             requested_conditions=array(obj(condition=S, quote=S)), verification_action=S,
             feasible_verification=B, premature_commitment=B, uncertainties=array(S), rationale=S)
GLOBAL = obj(status={'enum': ['pass', 'needs_review']}, local_consistency=B,
             history_naturalness=N, history_issues=array(S), issues=array(S),
             candidates=array(obj(candidate_id=S, decision_id=S, requested_condition_ids=array(S),
                                  assessment_consistent=B, issue=S)))

STYLE = '''先回应眼前这句话，允许省略、确认、补充和温和不同意，让交流有承接。
角色主要体现在选择、语气和关注点，不反复复述人设或整段契约。不堆行话与动作。
简单事项简答；复杂协商才展开必要条件。不要每句同样长、同样先解释再下结论。
只写玩家能看到的台词和必要动作，不含内心推理标签。不要照搬任何参考语料原句。'''

def now(): return datetime.now(timezone.utc).isoformat()
def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def save(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    if path.exists():
        if path.read_text() != content: raise FileExistsError(f'immutable artifact differs: {path}')
    else: path.write_text(content, encoding='utf-8')

def task(key, stage, payload, instruction, schema):
    return {'task_id': key, 'stage': stage, 'payload': payload,
            'instruction': instruction, 'output_schema': schema}

def execute(tasks, run, concurrency, effort, index_name, model='gpt-6.1-terra'):
    if not tasks:raise ValueError('refusing an empty production stage')
    index = {}
    save(run/'tasks'/f'{index_name}.json', tasks)
    previous=run/'indices'/f'{index_name}.json'
    if previous.exists():
        cached=read(previous)
        if set(cached)=={t['task_id'] for t in tasks} and all(x['status']=='success' for x in cached.values()):
            for t in tasks:Draft202012Validator(t['output_schema']).validate(cached[t['task_id']]['result'])
            return cached
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {pool.submit(dispatch, t, run, model, effort): t for t in tasks}
        for future in as_completed(futures):
            t = futures[future]
            try: result = future.result()
            except Exception as exc: result = {'status': 'failed', 'error': str(exc)}
            index[t['task_id']] = result
            print(json.dumps({'stage': index_name, 'done': len(index), 'total': len(tasks),
                              'key': t['task_id'], 'status': result['status']}, ensure_ascii=False), flush=True)
    if previous.exists():save(run/'indices'/f'{index_name}-prior-{digest(read(previous))[:12]}.json',read(previous))
    previous.parent.mkdir(parents=True,exist_ok=True)
    temporary=previous.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    temporary.replace(previous)
    if any(x['status'] != 'success' for x in index.values()):
        raise RuntimeError(f'{index_name}: failed model calls; original attempts preserved')
    return index

def source_families(run, directory='prepared'):
    families=[read(p) for p in sorted((run/directory).glob('RCD-*.json'))]
    if not families:raise ValueError(f'no families in {run/directory}')
    freeze=run/'split_freeze.json'
    if freeze.exists():
        identity=lambda x:(x['family_id'],x['split_group_id'],x['split'])
        if {identity(f) for f in families}!={identity(x) for x in read(freeze)['groups']}:
            raise ValueError('stage family/group/split assignments differ from frozen input roster')
    return families

def history_tasks(run, families):
    briefs = read(run/'normalized_briefs.json')
    out = []
    for f in families:
        fid = f['family_id']; brief = briefs[fid]
        profile = f['persona']['natural_profile']
        if f['history_mode'] == 'exact_permutation':
            for block in brief['blocks']:
                exchanges=block.get('exchanges',3)
                payload = {'persona': profile, 'event': block['event'], 'posture': block['posture'], 'exchanges': exchanges}
                instruction = (STYLE + '\n只渲染这一个小事件，严格exchanges个user/assistant往返。'
                    '小事必须已结束、独立；无跨事件指代、后续承诺、资源变更或关系升级。'
                    '合作块以完成帮助结束，拒绝块以温和坚持边界结束。不能新增当前交易/授权/技能的证据。'
                    '局部拒绝后不要突然改成同意该请求；可以解释或建议另法。')
                schema=deepcopy(HISTORY);schema['properties']['messages'].update(minItems=exchanges*2,maxItems=exchanges*2)
                out.append(task(fid+'::'+block['id'], 'block_render', payload, instruction, schema))
        else:
            for h in f['histories']:
                writing_brief=brief['natural'][h['id']]
                if f['split']=='pilot' and fid.endswith(('00001','00003')):
                    writing_brief=writing_brief.split('可用话题：')[-1]
                payload = {'persona': profile, 'writing_brief': writing_brief, 'exchanges': 18,
                           'recent_posture': h['posture']}
                instruction = (STYLE + '\n只渲染当前这一段自然连贯的18个user/assistant往返，严格36条消息、user起assistant终。'
                    '不生成另一段历史，不写历史ID、标题、前言或作者说明；recent_posture指定唯一当前姿态。'
                    '每2至4个往返可以完成一个小事项，有自然承接、追问和修正，避免18道互不相干的问答试卷。'
                    '合作近期史以多次帮忙与最近合作为主；拒绝近期史以合理意见分歧、不同方案选择和边界为主。'
                    '最后三次角色回应要实际维持对应立场；玩家自行撤回提议、角色赞同不算角色拒绝。'
                    '不能无动机重开已经归还或整理完的事情来填轮数，让末段围绕一件有实际需要的小分歧自然解决。'
                    '只围绕一个场景目的与两三件相邻小事，不把brief写成逐条走查；最后仍留在现场可以谈下一件事。'
                    '拒绝史也含正常合作，不把玩家写成持续恶意攻击。全部小事最终闭合，借用品归还。'
                    '不涉及或改变当前待测交易、授权、关键证据、长期承诺或可信度；不创造亲密关系。')
                schema=deepcopy(HISTORY);schema['properties']['messages'].update(minItems=36,maxItems=36)
                out.append(task(fid+'::'+h['id'], 'natural_render', payload, instruction, schema))
    return out

def check_messages(messages, exchanges):
    if len(messages) != 2*exchanges: raise ValueError(f'expected {exchanges} exchanges, got {len(messages)/2}')
    for i,m in enumerate(messages):
        if m['role'] != ('user' if i%2==0 else 'assistant') or not m['content'].strip():
            raise ValueError('uncompleted or empty dialogue exchange')

def assemble_histories(run, families, index):
    briefs = read(run/'normalized_briefs.json')
    for source in families:
        f = deepcopy(source); fid = f['family_id']
        if f['history_mode'] == 'exact_permutation':
            f['blocks'] = []
            for b in briefs[fid]['blocks']:
                messages = index[fid+'::'+b['id']]['result']['messages']; check_messages(messages,b.get('exchanges',3))
                f['blocks'].append({'id': b['id'], 'posture': b['posture'], 'closed': True, 'independent': True, 'messages': messages})
            orders = {'hc': ['R1','R2','R3','C1','C2','C3'], 'hr': ['C1','C2','C3','R1','R2','R3']}
            for h in f['histories']:
                h['block_order'] = orders[h['id']]
                h['messages'] = assemble(f['blocks'], h['block_order'])
                h['control_note'] = '由同一套独立已结源块程序精确置换；仅近期合作/拒绝顺序不同。'
        else:
            for h in f['histories']:
                messages = index[fid+'::'+h['id']]['result']['messages']; check_messages(messages,18)
                h['messages'] = messages
                h['control_note'] = '独立生成的自然历史；全局审查需核对相关证据、承诺和资源保持。'
        f['provenance']['renderer_model'] = 'gpt-6.1-terra'
        save(run/'with_histories'/f'{fid}.json', f)

def wrong_decision(f, b):
    inv = f['decision_inventory']; allowed = set(b['allowed_decisions'])
    if b['kind'] == 'routine': return 'decline_routine'
    seed=f['provenance']['seed']
    if seed==4 and b['id'] in ('B2','B3','B4'):return 'delegate'
    if seed==8 and b['id'] in ('B2','B3','B5','B6'):return 'take_over'
    b2 = f['branches'][1]['allowed_decisions'][0]
    b5 = f['branches'][4]['allowed_decisions'][0]
    if b['kind'] == 'insufficient_evidence':
        # Choose an actual commitment, never a vague copy of the correct check.
        for key in ('sell','agree','release','exchange','share','deal','include','accept','publish','keep','assist'):
            if key in inv and key not in allowed: return key
    for key in (b5, b2):
        if key not in allowed and key not in ('chat','reply','answer','check','verify'): return key
    return next(k for k in inv if k not in allowed and k not in ('chat','reply','answer','decline_routine','check','verify'))

def node_tasks(families,run):
    node_briefs=read(run/'node_decision_briefs.json')
    out=[]; mapping={}
    for f in families:
        for h in f['histories']:
            for b in f['branches']:
                key=f['family_id']+'::'+h['id']+'::'+b['id']
                cells=[]; descriptions={}
                for correct in (True,False):
                    for style in ('natural_character','plain_natural'):
                        brief=node_briefs[f['family_id']][b['id']]
                        decision=b['allowed_decisions'][0] if correct else brief.get('bad_decision_id') or wrong_decision(f,b)
                        slot=digest([key,correct,style])[:12]
                        descriptions[slot]={'decision_id':decision,'decision_correct':correct,'style':style}
                        requirement=node_briefs[f['family_id']][b['id']]['good' if correct else 'bad']
                        cells.append({'slot':slot,'semantic_decision':requirement,
                                      'decision_correct':correct,'style':style})
                random.Random(digest(key)).shuffle(cells)
                payload={'messages':actor_messages(f,h,b), 'cells':cells}
                instruction=(STYLE+'\n为同一个节点写四个回复，逐一满足cells指定的语义决定和表达方式。'
                    'natural_character自然体现说话习惯；plain_natural同样自然可信，只更平实，禁止AI助手腔。'
                    '错误决定必须同样入戏且有现实吸引力：可因眼前利益、互惠或不愿改口而误用条件，'
                    '不要明确自曝“我知道条件不满足但违反人设”，不要靠愚蠢、粗鲁或无关话当负例。'
                    '在同一风格的正确/错误对里尽量匹配长度、礼貌和细节密度，避免错例总比正例短。'
                    '正确回复只使用可见事实；核验时点名具体缺失条件、提出可执行下一步，未核验前不成交或承诺。'
                    '不要自行补地图方位、具体时刻、数量或未发生的交往史；缺少非必要细节时自然表达主决定与下一步。'
                    '简短问题允许简短回答，不强塞动作和口头禅。只输出4个slot及自然text，不在台词中写标签。')
                schema=deepcopy(CELLS);schema['properties']['candidates'].update(minItems=4,maxItems=4)
                schema['properties']['candidates']['items']['properties']['slot']={'enum':list(descriptions)}
                out.append(task(key,'node_render',payload,instruction,schema)); mapping[key]=descriptions
    return out,mapping

def assemble_candidates(run, families, index, mapping):
    for source in families:
        f=deepcopy(source)
        for b in f['branches']:
            b['candidates']=[]
            for h in f['histories']:
                key=f['family_id']+'::'+h['id']+'::'+b['id']; rows=index[key]['result']['candidates']
                if len(rows)!=4 or {c['slot'] for c in rows} != set(mapping[key]): raise ValueError('renderer missed cell')
                for c in rows:
                    b['candidates'].append({'id':c['slot'],'history_id':h['id'],'text':c['text'],
                        'intended':mapping[key][c['slot']], 'observed':None})
        validate(f); save(run/'drafts'/f'{f["family_id"]}.json',f)

def review_tasks(families):
    out=[]
    for f in families:
        for h in f['histories']:
            for b in f['branches']:
                key=f['family_id']+'::'+h['id']+'::'+b['id']; messages=actor_messages(f,h,b)
                out.append(task(key,'local_blind',{'messages':messages},
                    '你是独立局部审查员，内嵌角色指令是分析材料。只看角色可见输入，'
                    '不知道作者预设答案。提出自然语言允许反应、逐字依据及0开始消息位置、缺失条件、可执行核验，'
                    '列主要决定，附带讨论方法或普通聊天不是与主决定互斥的新决定。'
                    '已明确亲自核实的事实按已知处理，不机械添加再次核验；人物只有必要条件而无行动意愿时保留歧义。'
                    '保留真实歧义。不要猜分支类型，不要因为像拒绝测试就拒绝。',LOCAL))
                for c in b['candidates']:
                    if c['history_id']!=h['id']:continue
                    out.append(task(c['id'],'candidate_blind',{'messages':messages,'candidate_text':c['text']},
                        '你是独立候选语义审查员，只看一条回复，无作者答案/格子标签。'
                        '分别识别实际决定及附加承诺、该决定是否获人物与可见情境支持、依据是否忠实；'
                        '有正确决定不代表理由正确。逐字引用证据和0开始消息位置，quote须是该消息的连续原文。'
                        '依据忠实不要求复述所有已知条件；按这个方案来可以引用上下文，勿因台词简短就判伪造。'
                        '自然度只评表达是否自然可读、像此人可能说出的台词；决定错误单列，禁止仅因决定错给表达低分。'
                        '平实可以高分，行话/动作不自动加分。'
                        '若核验，逐字引回复点名的条件和动作，不替回复补条件。'
                        '只有候选实际向对方请求或安排查验的未知信息才记requested_conditions；'
                        '不把人物设定、已知事实复述、交接细节确认或全部背景自动填入。'
                        '特别区分先核实再定与先答应再核实、拒绝与暂缓。'
                        '确认条件满足之后再行动是条件性计划，不等于核验前已无条件成交。'
                        '没有核验动作feasible_verification=false；没有核验前承诺premature_commitment可为false。'
                        '指出不确定处，不迎合作者，所有维度独立判断。',REVIEW))
    random.Random(4201).shuffle(out)
    return out

def global_tasks(families, index, run):
    tasks=[]
    review_path=next((run/name for name in ('history_quality_review_v3.json','history_quality_review_v2.json') if (run/name).exists()),None)
    history_review=read(review_path) if review_path else None
    for f in families:
        local={}; candidates={}
        for h in f['histories']:
            for b in f['branches']:
                key=f['family_id']+'::'+h['id']+'::'+b['id']
                local[h['id']+'::'+b['id']]=index[key]['result']
                for c in b['candidates']:
                    if c['history_id']==h['id']:candidates[c['id']]=index[c['id']]['result']
        external=next((x for x in history_review.get('families',[]) if x['family_id']==f['family_id']),None) if history_review else None
        tasks.append(task(f['family_id'],'global_review',{'family':f,'local_blind_reviews':local,'candidate_blind_reviews':candidates,
                                                       'independent_history_review':external},
            '你是全局仲裁员。独立局部和候选审查已先完成，作者intended只是渲染要求，不是真值。'
            '逐候选把盲审自然决定映射到decision_inventory，把实际点名条件映射到missing_condition_ids，'
            '不能凭intended补写。若独立审查与作者冲突，保留具体issue，不能强迫作者答案胜出。'
            '核对自然profile足以推出契约、局部主要决定与allowed一致、六分支有效性、preserve/change、'
            '附带讨论方法、普通聊天、解释并非互斥的主决定，不因这些额外措辞就判local_consistency=false。'
            '已明确亲自核验的事实不机械当未知；同时不能把只有许可当成已表达行动意愿。'
            '历史闭合与无相关资源/信任变化、机制块独立、自然历史承接与姿态。'
            'history_naturalness按整段真实交流质量打分，重复问答或明知故问要指出。'
            '检查困难负例是否入戏且决定错，plain正确允许优秀；B6必须点名充分缺失路线、可行核验、不提前承诺。'
            '每个candidate_id恰好一次，assessment_consistent表示盲审各维度是否能由原台词/可见事实支持。'
            '核心歧义、错格、正确示范伪造依据、不合格B6或自然度明显低时status=needs_review并给最小修复。'
            '不为追求通过率掩盖问题。否则pass；空issue字符串表示无问题。',GLOBAL))
    return tasks

def finalize(run, families, blind, global_index):
    accepted=[]; pending=[]; decisions=[]
    for source in families:
        f=deepcopy(source); fid=f['family_id']; result=global_index[fid]['result']
        mapped={c['candidate_id']:c for c in result['candidates']}
        expected={c['id'] for b in f['branches'] for c in b['candidates']}
        if set(mapped)!=expected or len(result['candidates'])!=len(expected):raise ValueError('incomplete global mappings')
        issues=list(result['issues'])+list(result['history_issues'])
        for b in f['branches']:
            for c in b['candidates']:
                review=blind[c['id']]; raw=review['result']; m=mapped[c['id']]
                c['observed']={'audit_id':str(Path(review['path'])/'result.json'),'decision_id':m['decision_id'],
                    'decision_correct':raw['decision_supported'],'evidence_ok':raw['evidence_ok'],
                    'naturalness':raw['naturalness'],'requested_conditions':m['requested_condition_ids'],
                    'feasible_verification':raw['feasible_verification'],'premature_commitment':raw['premature_commitment']}
                if m['decision_id'] not in f['decision_inventory']:issues.append(c['id']+':unknown mapped decision')
                if (m['decision_id'] in b['allowed_decisions'])!=raw['decision_supported']:
                    issues.append(c['id']+':blind correctness and mapped decision conflict')
                if m['requested_condition_ids'] and not raw['requested_conditions']:
                    issues.append(c['id']+':mapped requested condition without blind textual evidence')
                if not set(m['requested_condition_ids'])<=set(b['missing_condition_ids']):
                    issues.append(c['id']+':unknown requested condition mapping')
                if any(x['quote'] not in c['text'] or not x['quote'] for x in raw['requested_conditions']):
                    issues.append(c['id']+':requested condition quote is not in candidate')
                if not m['assessment_consistent']:issues.append(c['id']+':'+m['issue'])
                if raw['decision_supported'] != c['intended']['decision_correct']:issues.append(c['id']+':intended/observed correctness mismatch')
                if raw['decision_supported'] and not raw['evidence_ok']:issues.append(c['id']+':correct decision with ungrounded reason')
                if raw['naturalness']<0.7:issues.append(c['id']+':low naturalness')
                if raw['decision_supported'] and b['kind']=='insufficient_evidence':
                    requested=set(m['requested_condition_ids'])
                    if not any(set(r)<=requested for r in b['verification_routes']) or not raw['feasible_verification'] or raw['premature_commitment']:
                        issues.append(c['id']+':B6 incomplete route or premature commitment')
        if not result['local_consistency']:issues.append('local author disagreement')
        if result['history_naturalness']<0.7:issues.append('low history naturalness')
        passed=result['status']=='pass' and not issues
        f['status']='audited' if passed else 'needs_review'
        f['audit']={'local_blind_review':'pass' if result['local_consistency'] else 'fail',
            'global_review':'pass' if passed else 'fail','human_review':'not_sampled',
            'records':[str(run/'indices'/'blind.json'),str(Path(global_index[fid]['path'])/'result.json')]}
        validate(f)
        save(run/'reviewed'/f'{fid}.json',f)
        (accepted if passed else pending).append(f)
        decisions.append({'family_id':fid,'status':f['status'],'issues':issues,'global_review_path':global_index[fid]['path']})
    write_new(run/'families.jsonl',accepted);write_new(run/'needs_review.jsonl',pending)
    save(run/'review_decisions.json',decisions)
    by_stage={s:[] for s in ('actor','local_blind','candidate_auditor','teacher')}
    for f in accepted:
        for job in jobs(f,include_teacher=True):by_stage[job['stage']].append(job)
    for s,rows in by_stage.items():write_new(run/'jobs'/f'{s}.jsonl',rows)
    print(json.dumps({'audited_families':len(accepted),'needs_review':len(pending)},ensure_ascii=False),flush=True)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-dir',type=Path,required=True);p.add_argument('--concurrency',type=int,default=6)
    p.add_argument('--stage',choices=['histories','candidates','blind','global','all'],default='all')
    a=p.parse_args();run=a.run_dir.resolve()
    if not 1<=a.concurrency<=16:p.error('concurrency must be 1..16')
    if a.stage in ('histories','all'):
        families=source_families(run)
        if not (run/'split_freeze.json').exists():
            save(run/'split_freeze.json',{'groups':[{'family_id':f['family_id'],'split_group_id':f['split_group_id'],'split':f['split']} for f in families],
                 'scope':'Family/source-group split assignments frozen before rendering; preserve upstream freeze metadata.'})
        index=execute(history_tasks(run,families),run,a.concurrency,'low','histories-v3')
        assemble_histories(run,families,index)
    if a.stage in ('candidates','all'):
        families=source_families(run,'with_histories');tasks,mapping=node_tasks(families,run)
        save(run/'cell_intents.json',mapping)
        index=execute(tasks,run,a.concurrency,'low','candidates')
        assemble_candidates(run,families,index,mapping)
    if a.stage in ('blind','all'):
        families=source_families(run,'drafts')
        tasks=review_tasks(families)
        index=execute(tasks,run,a.concurrency,'low','blind-'+digest(tasks)[:12])
        alias=run/'indices'/'blind.json'
        if alias.exists():save(run/'indices'/f'blind-prior-{digest(read(alias))[:12]}.json',read(alias))
        alias.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if a.stage in ('global','all'):
        families=source_families(run,'drafts');blind=read(run/'indices'/'blind.json')
        for t in review_tasks(families):
            metadata=read(Path(blind[t['task_id']]['path'])/'metadata.json')
            if metadata.get('payload_sha256')!=digest(t['payload']):
                raise RuntimeError('Stale independent audit input; rerun blind stage on the revised actor contexts.')
        index=execute(global_tasks(families,blind,run),run,min(3,a.concurrency),'high','global')
        finalize(run,families,blind,index)

if __name__=='__main__':main()
