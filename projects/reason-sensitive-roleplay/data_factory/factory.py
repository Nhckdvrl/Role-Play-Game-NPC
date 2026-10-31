"""Offline production plumbing: seed queues, exact history assembly, validation, routing.

No provider credentials or fictional Astra/Terra API model IDs. Use a real local
agent dispatcher on exported payloads. Structural validity != semantic approval.
"""
from __future__ import annotations
import argparse
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent
MOTIVES = ['利润/信誉','求知/程序','自尊/交易','独立/协作','忠诚/规则','承诺/效率','创作/配合']
KINDS = ['routine','pressure','invalid_reason','generic_incentive','valid_reason','insufficient_evidence']


def digest(value):
    return sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def unique(values, name):
    if len(set(values)) != len(values):
        raise ValueError(f'duplicate {name}')


def assemble(blocks, order):
    unique([b['id'] for b in blocks], 'block ids')
    by_id = {b['id']: b for b in blocks}
    if Counter(order) != Counter(by_id.keys()):
        raise ValueError('order must use every closed independent block exactly once')
    if any(not b['closed'] or not b['independent'] for b in blocks):
        raise ValueError('blocks must be closed and independent')
    return [deepcopy(m) for block_id in order for m in by_id[block_id]['messages']]


def validate(family):
    schema = json.loads((ROOT/'story_family.schema.json').read_text())
    Draft202012Validator(schema).validate(family)
    histories, branches = family['histories'], family['branches']
    if len(histories) != 2 or len(branches) != 6:
        raise ValueError('v0.2 requires exactly two histories and six branches')
    unique([h['id'] for h in histories], 'histories')
    unique([b['id'] for b in branches], 'branches')
    if set(b['kind'] for b in branches) != set(KINDS):
        raise ValueError('all six branch kinds are required')
    if {h['posture'] for h in histories} != {'cooperative_recent','resistant_recent'}:
        raise ValueError('both history postures are required')
    inv = family['decision_inventory']
    for h in histories:
        if any(m['role'] != ('user' if i%2==0 else 'assistant') for i,m in enumerate(h['messages'])) or len(h['messages'])%2:
            raise ValueError('history must contain completed user/assistant exchanges')
    if family['history_mode'] == 'exact_permutation':
        if len(family['blocks']) < 4:
            raise ValueError('mechanism subset needs >=4 independent blocks')
        for h in histories:
            if h['messages'] != assemble(family['blocks'],h['block_order']):
                raise ValueError('exact block text/order mismatch')
        if histories[0]['block_order'] == histories[1]['block_order']:
            raise ValueError('mechanism pair must have different order')
    ids = []
    nodes = {h['id']+'::'+b['id']: b for h in histories for b in branches}
    for b in branches:
        if not set(b['allowed_decisions']) <= set(inv):
            raise ValueError('unknown allowed decision')
        unique([e['id'] for e in b['evidence']], 'branch evidence')
        if b['kind'] == 'insufficient_evidence':
            if not b['missing_condition_ids'] or not b['verification_routes']:
                raise ValueError('B6 requires missing conditions and verification routes')
            if any(not set(r) <= set(b['missing_condition_ids']) for r in b['verification_routes']):
                raise ValueError('verification route references an unknown missing condition')
        for c in b['candidates']:
            ids.append(c['id'])
            if c['history_id'] not in {h['id'] for h in histories} or c['intended']['decision_id'] not in inv:
                raise ValueError('unknown candidate history/decision')
            if c['observed'] is not None and c['observed']['decision_id'] not in inv:
                raise ValueError('unknown observed decision')
        for h in histories:
            grid = {(c['intended']['decision_correct'],c['intended']['style']) for c in b['candidates'] if c['history_id']==h['id']}
            if grid != {(x,y) for x in (True,False) for y in ('natural_character','plain_natural')}:
                raise ValueError('four-grid coverage missing')
    unique(ids, 'candidate ids')
    seen = set()
    for e in family['edges']:
        if e['source'] not in nodes or e['target'] not in nodes or e['source']==e['target']:
            raise ValueError('invalid edge endpoint')
        key = tuple(sorted((e['source'],e['target'])))
        if key in seen: raise ValueError('duplicate edge')
        seen.add(key)
        for left,right in e['allowed_pairs']:
            if left not in nodes[e['source']]['allowed_decisions'] or right not in nodes[e['target']]['allowed_decisions']:
                raise ValueError('edge pair must be valid at both endpoints')
    if family['status']=='audited':
        if family['audit']['local_blind_review']!='pass' or family['audit']['global_review']!='pass' or not family['audit']['records']:
            raise ValueError('audited family requires linked passed audits')
        if any(c['observed'] is None for b in branches for c in b['candidates']):
            raise ValueError('intended labels cannot substitute independent candidate annotations')
    return {'family_id':family['family_id'],'nodes':len(nodes),'candidate_instances':len(ids),
            'unique_candidate_texts':len({c['text'] for b in branches for c in b['candidates']}),
            'semantic_audited':family['status']=='audited','family_sha256':digest(family)}


def actor_messages(family, history, branch):
    visible = [e['text'] for e in branch['evidence'] if e['visible']]
    context = branch['visible_observation'] + ('\n'+'\n'.join(visible) if visible else '')
    return [{'role':'system','content':'你在进行虚构人物对话。依据人物设定、自己的经历和可见信息自然回应，不输出决策标签。\n'+family['persona']['natural_profile']+'\n'+family['common_visible_context']}]+deepcopy(history['messages'])+[
        {'role':'user','content':context+'\n'+branch['player_turn']}]


def jobs(family, include_teacher=False):
    """Envelope metadata is NOT sent to the worker; send payload only."""
    validate(family)
    for h in family['histories']:
        for b in family['branches']:
            prefix = family['family_id']+'::'+h['id']+'::'+b['id']
            messages = actor_messages(family,h,b)
            base = {'messages':messages}
            for stage in ('actor','local_blind'):
                yield {'job_id':prefix+'::'+stage,'stage':stage,'payload':deepcopy(base),'input_hash':digest(base)}
            for c in b['candidates']:
                if c['history_id'] != h['id']: continue
                payload = {'messages':deepcopy(messages),'candidate_text':c['text']}
                yield {'job_id':prefix+'::audit::'+c['id'],'stage':'candidate_auditor','payload':payload,'input_hash':digest(payload)}
            if include_teacher and family['split'] != 'test':
                payload = {'messages':deepcopy(messages),'decision_contract':family['persona']['decision_contract'],
                           'teacher_scaffold':b['teacher_scaffold'],'allowed_decisions':b['allowed_decisions']}
                yield {'job_id':prefix+'::teacher','stage':'teacher','payload':payload,'input_hash':digest(payload)}


def read_jsonl(path):
    with Path(path).open(encoding='utf-8') as f:
        for number,line in enumerate(f,1):
            if not line.strip(): continue
            try: yield json.loads(line)
            except json.JSONDecodeError as exc: raise ValueError(f'{path}:{number}: {exc}') from exc


def write_new(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    text = ''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows)
    if path.exists():
        if path.read_text()==text: return
        raise FileExistsError(f'refusing to overwrite {path}; use a new run/shard')
    with path.open('x',encoding='utf-8') as f: f.write(text)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('init'); p.add_argument('--out',required=True); p.add_argument('--count',type=int,default=12)
    p.add_argument('--split',choices=['pilot','train','dev','test'],default='pilot'); p.add_argument('--offset',type=int,default=0)
    p=sub.add_parser('validate'); p.add_argument('input'); p.add_argument('--report',required=True)
    p=sub.add_parser('export'); p.add_argument('input'); p.add_argument('--out',required=True); p.add_argument('--include-teacher',action='store_true')
    a=parser.parse_args()
    if a.command=='init':
        if a.count<1 or a.offset<0: parser.error('positive count and nonnegative offset required')
        rows=[{'family_id':f'RCD-{a.split}-{i:05d}','split_group_id':f'RCD-{a.split}-{i:05d}',
               'split':a.split,'motive':MOTIVES[i%len(MOTIVES)],'history_mode':'exact_permutation' if i%5==0 else 'natural',
               'status':'planned_not_generated','seed':i,'protocol_version':'0.2'} for i in range(a.offset,a.offset+a.count)]
        write_new(Path(a.out)/'plan.jsonl',rows)
        print(json.dumps({'planned_families':len(rows),'generated_families':0}))
    elif a.command=='validate':
        families=list(read_jsonl(a.input)); unique([f['family_id'] for f in families],'family ids')
        groups={}
        for f in families:
            group=f['split_group_id']; split=f['split']
            if group in groups and groups[group]!=split: raise ValueError('split_group contamination')
            groups[group]=split
        write_new(a.report,[validate(f) for f in families]); print(f'validated {len(families)} families structurally')
    else:
        by_stage={s:[] for s in ('actor','local_blind','candidate_auditor','teacher')}
        families=list(read_jsonl(a.input)); unique([f['family_id'] for f in families],'family ids')
        for f in families:
            for job in jobs(f,a.include_teacher): by_stage[job['stage']].append(job)
        for stage,rows in by_stage.items():
            if rows: write_new(Path(a.out)/(stage+'.jsonl'),rows)
        print(json.dumps({stage:len(rows) for stage,rows in by_stage.items()}))

if __name__=='__main__':
    main()
