#!/usr/bin/env python3
"""Build an isolated, evidence-linked preview from existing native adjudications."""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

from jsonschema import Draft202012Validator
import fast_review
import factory
import quality

ROOT = Path('runs/train-conflict-adjudication')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def candidate_equal(actual, expected):
    if set(actual) != set(expected):
        return False
    for key in expected:
        if key == 'candidates':
            left, right = actual[key], expected[key]
            if len(left) != len(right) or len({x['id'] for x in left}) != len(left):
                return False
            if {x['id']: x for x in left} != {x['id']: x for x in right}:
                return False
        elif actual[key] != expected[key]:
            return False
    return True


def material_notes(notes):
    # Narrow, conservative indicators of explicit approximate/impossible dictionary mapping.
    patterns = (r'近似', r'(?:词典|字典|动作词典).{0,25}(?:没有|缺少|缺失|无法|不能|未明确|假定)',
                r'(?:不在|缺少|没有).{0,20}(?:动作词典|词典|字典)', r'无法.{0,15}(?:映射|归类|表达)')
    return [n for n in notes if any(re.search(p, n) for p in patterns)]


def reconstruct(family, output, response_path, record_path, mapping, aliases):
    problems = []
    nodes = output['nodes']; ratings = output['cs']
    if len(nodes) != 12 or {x['n'] for x in nodes} != set(mapping):
        return None, ['node_coverage']
    if len(ratings) != 48 or {x['id'] for x in ratings} != set(aliases):
        return None, ['candidate_coverage']
    by_node = {x['n']: x for x in nodes}
    by_alias = {x['id']: (i, x) for i, x in enumerate(ratings)}
    by_candidate = {cid: by_alias[alias] for alias, cid in aliases.items()}
    if output['blocking']:
        problems.append('blocking')
    if material_notes(output['notes']):
        problems.append('dictionary_mapping_notes')
    family = deepcopy(family)
    for branch in family['branches']:
        node_ids = [n for n, pair in mapping.items() if pair[1] == branch['id']]
        if len(node_ids) != 2 or {mapping[n][0] for n in node_ids} != {'hc', 'hr'}:
            problems.append('node_mapping'); continue
        local = [by_node[n]['actions'] for n in node_ids]
        if any(not a or len(a) != len(set(a)) or not set(a) <= set(family['decision_inventory']) for a in local):
            problems.append('invalid_local_actions'); continue
        if set(local[0]) != set(local[1]):
            problems.append('history_actions_disagree'); continue
        branch['allowed_decisions'] = list(local[0])
        for c in branch['candidates']:
            idx, x = by_candidate[c['id']]
            node = next(n for n in node_ids if mapping[n][0] == c['history_id'])
            allowed = set(by_node[node]['actions'])
            if x['d'] not in family['decision_inventory']:
                problems.append('unknown_action')
            if x['c'] != c['intended']['decision_correct']:
                problems.append('intended_correctness_disagree')
            if x['c'] and not x['g']:
                problems.append('positive_unfaithful')
            if x['s'] < .7:
                problems.append('naturalness_below_threshold')
            if x['c'] and x['d'] not in allowed:
                problems.append('positive_not_locally_allowed')
            if not x['c'] and x['d'] in allowed:
                problems.append('negative_locally_allowed')
            if not x['quotes'] or any(not q.strip() or q not in c['text'] for q in x['quotes']):
                problems.append('unfaithful_quote')
            if branch['kind'] == 'insufficient_evidence' and x['c']:
                if (not any(set(route) <= set(x['v']) for route in branch['verification_routes'])
                        or not x['f'] or x['p']):
                    problems.append('b6_verification')
            c['observed'] = {'audit_id': str(response_path) + '#/cs/' + str(idx),
                             'decision_id': x['d'], 'decision_correct': x['c'],
                             'evidence_ok': x['g'], 'naturalness': x['s'],
                             'requested_conditions': x['v'], 'feasible_verification': x['f'],
                             'premature_commitment': x['p']}
    if problems:
        return None, sorted(set(problems))
    allowed = {b['id']: set(b['allowed_decisions']) for b in family['branches']}
    by_branch = {b['id']: b for b in family['branches']}
    edges = []
    for edge in family['edges']:
        left, right = edge['source'].split('::')[1], edge['target'].split('::')[1]
        l, r = allowed[left], allowed[right]
        if edge['kind'] == 'change' and l & r:
            continue
        new = deepcopy(edge)
        new['allowed_pairs'] = ([[d, d] for d in sorted(l & r)] if edge['kind'] == 'preserve'
                                else [[a, b] for a in sorted(l) for b in sorted(r)])
        if new['allowed_pairs']:
            edges.append(new)
    for h in ('hc', 'hr'):
        existing = {tuple(sorted((e['source'].split('::')[1], e['target'].split('::')[1])))
                    for e in edges if e['kind'] == 'change' and e['source'].startswith(h+'::')
                    and e['target'].startswith(h+'::')}
        for i in range(1, 7):
            for j in range(i+1, 7):
                if len(existing) >= 2:
                    break
                a, b = f'B{i}', f'B{j}'
                if (a,b) in existing or allowed[a] & allowed[b]:
                    continue
                aa, bb = by_branch[a], by_branch[b]
                why = ('独立审查的两处可见事实：'+aa['visible_observation']+'；'+bb['visible_observation']
                       +'；两处独立审查动作集合互不相交。')
                edges.append({'source': h+'::'+a, 'target': h+'::'+b, 'kind': 'change',
                              'allowed_pairs': [[x,y] for x in sorted(allowed[a]) for y in sorted(allowed[b])],
                              'justification': why})
                existing.add((a,b))
            if len(existing) >= 2:
                break
        if len(existing) < 2:
            problems.append('insufficient_disjoint_change_edges')
    if problems:
        return None, sorted(set(problems))
    family['edges'] = edges
    family['audit']['records'] = list(family['audit']['records']) + [str(response_path), str(record_path)]
    family['source']['note'] += '；第三次原生独立审核已关联输出与记录；原native提示哈希为声明，不单独证明提示内容。'
    errors, _ = quality.check_family(family)
    if errors:
        return None, ['quality_check_failure'] + errors
    return family, []


def collect(root=ROOT):
    root = Path(root).resolve(); out = root/'collected'; out.mkdir(exist_ok=True)
    manifests = out/'manifests'; manifests.mkdir(exist_ok=True)
    sources = {}; invalid_sources = {}; source_errors = []
    source_paths = sorted((root/'private').glob('*/source.json'))
    for p in source_paths:
        try:
            source = read(p); raw = source['original_final_family_bytes_utf8'].encode('utf-8')
            f = json.loads(raw); base, cand, mapping, aliases = fast_review.payloads(f)
            private = read(p.parent/'mapping.json')
            require(sha(raw) == source['family_line_sha256'] and factory.digest(f) == source['family_canonical_digest'], 'source family hash mismatch')
            require(f['family_id'] == source['family_id'] and aliases == private['aliases_to_candidate_ids'], 'source alias mapping mismatch')
            require({k:list(v) for k,v in mapping.items()} == private['nodes_to_history_branch'], 'source node mapping mismatch')
            require([r['path'] for r in source['audit_records']] == f['audit']['records'], 'source audit reference mismatch')
            for record in source['audit_records']:
                require(sha(Path(record['path']).read_bytes()) == record['sha256'], 'source audit hash mismatch')
            key = frozenset(aliases)
            if key in sources:
                raise ValueError('duplicate source aliases')
            sources[key] = (p, source, f, base, cand, mapping, aliases)
        except Exception as exc:
            entry={'family_id':p.parent.name,'issues':['invalid_source'],'error':f'{type(exc).__name__}: {exc}','source':str(p)}
            try:
                aliases=read(p.parent/'mapping.json')['aliases_to_candidate_ids']
                invalid_sources[frozenset(aliases)]=entry
            except Exception:
                source_errors.append(entry)
    approved=[];pending=list(source_errors);categories=Counter();seen=set()
    if source_errors:categories['invalid_source']=len(source_errors)
    for index in sorted(root.glob('batch-*/index.json')):
        for item in read(index)['requests']:
            reqpath=Path(item['masked_request_path']);response=Path(item['safe_output_path'])
            record_path=response.with_suffix('.review_record.json')
            fid=None
            try:
                request=read(reqpath)
                payload=request['payload']; key=frozenset(c['id'] for c in payload['candidate']['candidates'])
                if key in invalid_sources:
                    entry=invalid_sources.pop(key);seen.add(entry['family_id']);pending.append(entry);categories['invalid_source']+=1;continue
                source_path, source, original, base, candidate, mapping, aliases=sources[key];fid=original['family_id']
                if fid in seen:
                    approved[:]=[row for row in approved if row['family_id']!=fid]
                    raise ValueError('duplicate family request')
                seen.add(fid)
                result=read(response);record=read(record_path)
                require(payload['local']==base and candidate_equal(payload['candidate'],candidate), 'payload mismatch')
                require(sha(reqpath.read_bytes())==record.get('request_bytes_sha256',record.get('input_bytes_sha256')), 'request hash mismatch')
                require(sha(canonical(payload))==record['canonical_payload_sha256'], 'payload hash mismatch')
                require((record.get('transport')=='native' or record.get('native') is True) and bool(record.get('model')), 'invalid native record')
                Draft202012Validator.check_schema(request['output_schema'])
                Draft202012Validator(request['output_schema']).validate(result)
                final, issues=reconstruct(original,result,response,record_path,mapping,aliases)
                manifest={'family_id':fid,'source_path':str(source_path),'source_sha256':sha(source_path.read_bytes()),
                          'source_family_sha256':source['family_line_sha256'],'mapping_path':str(source_path.parent/'mapping.json'),
                          'mapping_sha256':sha((source_path.parent/'mapping.json').read_bytes()),'request_path':str(reqpath),
                          'request_sha256':sha(reqpath.read_bytes()),'response_path':str(response),
                          'response_sha256':sha(response.read_bytes()),'native_record_path':str(record_path),
                          'native_record_sha256':sha(record_path.read_bytes()),'old_audit_records':source['audit_records'],
                          'original_allowed':{b['id']:b['allowed_decisions'] for b in original['branches']},
                          'original_observed':{c['id']:c['observed'] for b in original['branches'] for c in b['candidates']},
                          'original_edges':original['edges'],'notes':result['notes'],'blocking':result['blocking'],
                          'issues':issues,'native_prompt_hash_limitation':'recorded request hash is a declaration, not proof of native model prompt',
                          'usage':record.get('usage')}
                write(manifests/(fid+'.json'),manifest)
                if issues:
                    for issue in issues:categories[issue.split(':')[0]]+=1
                    pending.append({'family_id':fid,'issues':issues,'manifest':str(manifests/(fid+'.json'))})
                else:approved.append(final)
            except Exception as exc:
                reason='invalid_or_unverifiable_artifact';categories[reason]+=1
                pending.append({'family_id':fid,'request':str(reqpath),'issues':[reason], 'error':f'{type(exc).__name__}: {exc}'})
    for key,(path,source,f,*_) in sources.items():
        if f['family_id'] not in seen:
            categories['missing_completed_request']+=1
            pending.append({'family_id':f['family_id'],'issues':['missing_completed_request'],'source':str(path)})
    for entry in invalid_sources.values():
        pending.append(entry);categories['invalid_source']+=1
    for name,rows in (('approved.jsonl',approved),('pending.jsonl',pending)):
        (out/name).write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for x in rows),encoding='utf-8')
    summary={'utc':datetime.now(timezone.utc).isoformat(),'source_families':len(source_paths),'approved':len(approved),'pending':len(pending),
             'pending_categories_nonexclusive':dict(categories),'preview_only':True,'usage':'native usage not returned; unknown',
             'limitation':'Native request hash is recorded by the collector; it does not prove native prompt content.'}
    write(out/'summary.json',summary);print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=ROOT)
    collect(parser.parse_args().root)
