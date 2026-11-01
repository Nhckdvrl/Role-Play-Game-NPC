#!/usr/bin/env python3
"""Freeze and validate the currently released research snapshot; never touches sources."""
import copy, datetime, gzip, hashlib, json, os, subprocess, sys
from collections import Counter, defaultdict
from pathlib import Path
import factory, quality

P = Path(__file__).resolve().parent.parent
RUNS = (P/'runs').resolve()
OUT = RUNS/'hf-staging/current'
sha = lambda b: hashlib.sha256(b).hexdigest()
canon = lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()

def write(path, data):
    path = OUT/path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)

def jwrite(path, value):
    write(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True).encode()+b'\n')

def gz(path, records):
    raw = b''.join(canon(x)+b'\n' for x in records)
    write(path, gzip.compress(raw, mtime=0))

def frozen(path):
    b = path.read_bytes()
    return b, [json.loads(x) for x in b.splitlines() if x.strip()]

def norm(f):
    f = copy.deepcopy(f)
    f['audit']['records'] = ['<audit-reference>' for _ in f['audit']['records']]
    for b in f['branches']:
        for c in b['candidates']:
            if c.get('observed') and c['observed'].get('audit_id'):
                c['observed']['audit_id'] = '<audit-reference>'
    return sha(canon(f))

def pointer(obj, fragment):
    if not fragment: return
    if not fragment.startswith('/'): raise ValueError('invalid JSON pointer: '+fragment)
    for token in fragment[1:].split('/'):
        token = token.replace('~1','/').replace('~0','~')
        obj = obj[int(token)] if isinstance(obj,list) else obj[token]

cache, mapping = {}, {}
def reference(ref):
    path, sep, fragment = ref.partition('#')
    p = Path(path)
    if not p.is_absolute(): p = P/p
    p = p.resolve(strict=True)
    if not p.is_relative_to(RUNS) or p.suffix != '.json': raise ValueError('unsafe audit path: '+ref)
    if p not in cache:
        b = p.read_bytes(); obj = json.loads(b)
        digest = sha(b); identity = sha(str(p.relative_to(P)).encode())
        artifact = identity+'-'+digest
        write('audits/objects/'+artifact+'.json', b)
        cache[p] = (artifact, obj)
    digest, obj = cache[p]
    pointer(obj, fragment)
    new = 'audits/objects/'+digest+'.json'+('#'+fragment if sep else '')
    mapping[ref] = new
    return new

def export(f):
    out = copy.deepcopy(f)
    out['audit']['records'] = [reference(r) for r in out['audit']['records']]
    for b in out['branches']:
        for c in b['candidates']:
            if c.get('observed') and c['observed'].get('audit_id'):
                c['observed']['audit_id'] = reference(c['observed']['audit_id'])
    if norm(f) != norm(out): raise ValueError('semantic hash mismatch')
    return out

def main():
    if OUT.exists():
        import shutil
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    sources = {'train':'runs/train5000-live/families.jsonl','validation':'runs/dev500-live/families.jsonl','test':'runs/test800-live/families.jsonl','pilot':'runs/pilot12-20261101-semantic-v4/families.jsonl'}
    inputs, source_hashes = {}, {}
    for k,p in sources.items():
        b, inputs[k] = frozen(P/p); source_hashes[p] = sha(b)
        directory = (P/p).parent
        exclusion_path = directory/'exclusions.json'
        if exclusion_path.exists():
            eb = exclusion_path.read_bytes(); excluded = json.loads(eb)
            source_hashes[str(exclusion_path.relative_to(P))] = sha(eb)
            # A controller may not yet have saved an asynchronously revoked family.
            inputs[k] = [f for f in inputs[k] if f['family_id'] not in excluded]
    summaries, all_ids, groups, history_hashes, semantic = {}, set(), defaultdict(set), defaultdict(set), {}
    exported = []
    for split in ('train','validation','test'):
        fs, rows = [], []
        modes, kinds, grid, texts = Counter(), Counter(), Counter(), set()
        for f in inputs[split]:
            if f['family_id'] in all_ids: raise ValueError('duplicate family ID '+f['family_id'])
            all_ids.add(f['family_id'])
            if f['split'] != ('dev' if split == 'validation' else split): raise ValueError('split mismatch')
            factory.validate(f)
            errors, _ = quality.check_family(f)
            if errors: raise ValueError(f['family_id']+': '+str(errors))
            groups[split].add(f['split_group_id']); modes[f['history_mode']]+=1
            for h in f['histories']:
                history_hashes[quality.message_hash(h['messages'])].add(split)
            x = export(f); semantic[f['family_id']] = norm(x); fs.append(x); exported.append(x)
            for h in x['histories']:
                for b in x['branches']:
                    cs = [c for c in b['candidates'] if c['history_id']==h['id']]
                    if len(cs)!=4: raise ValueError('bad candidate count')
                    kinds[b['kind']]+=1
                    for c in cs:
                        grid[str(c['intended']['decision_correct'])+'/'+c['intended']['style']]+=1; texts.add(c['text'])
                    rows.append({'family_id':x['family_id'],'split_group_id':x['split_group_id'],
                        'history_id':h['id'],'history_mode':x['history_mode'],'history_posture':h['posture'],
                        'branch_id':b['id'],'branch_kind':b['kind'],
                        'actor_messages':factory.actor_messages(x,h,b),
                        'decision_inventory_json':json.dumps(x['decision_inventory'],ensure_ascii=False,sort_keys=True),
                        'allowed_decisions':b['allowed_decisions'],
                        'candidates':[{'id':c['id'],'text':c['text'],
                          'intended_decision_id':c['intended'].get('decision_id'),
                          'intended_decision_correct':c['intended'].get('decision_correct'),
                          'intended_style':c['intended'].get('style'),
                          'observed_decision_id':(c.get('observed') or {}).get('decision_id'),
                          'observed_decision_correct':(c.get('observed') or {}).get('decision_correct'),
                          'observed_evidence_ok':(c.get('observed') or {}).get('evidence_ok'),
                          'observed_naturalness':(c.get('observed') or {}).get('naturalness'),
                          'observed_requested_conditions':(c.get('observed') or {}).get('requested_conditions'),
                          'observed_feasible_verification':(c.get('observed') or {}).get('feasible_verification'),
                          'observed_premature_commitment':(c.get('observed') or {}).get('premature_commitment'),
                          'observed_audit_id':(c.get('observed') or {}).get('audit_id')} for c in cs]})
        gz('families/'+('dev' if split=='validation' else split)+'/part-00000.jsonl.gz',fs)
        gz('data/'+split+'/nodes-00000.jsonl.gz',rows)
        summaries[split]={'families':len(fs),'groups':len(groups[split]),'nodes':len(rows),'candidate_instances':len(rows)*4,'unique_candidate_texts':len(texts),'history_modes':dict(modes),'branch_nodes':dict(kinds),'intended_grid':dict(grid)}
    global_qa = quality.analyze(exported)
    if not global_qa['passed']: raise ValueError('export quality.analyze failed: '+str(global_qa['errors'][:10]))
    for a in groups:
        for b in groups:
            if a < b and groups[a]&groups[b]: raise ValueError('cross-split group collision: '+str(groups[a]&groups[b]))
    if any(len(v)>1 for v in history_hashes.values()): raise ValueError('cross-split exact history hash collision')
    # Pilot is calibration data and is excluded from the published splits.
    pilot=[]
    for f in inputs['pilot']:
        factory.validate(f)
        errors, _ = quality.check_family(f)
        if errors: raise ValueError(f['family_id']+': '+str(errors))
        pilot.append(export(f))
    gz('calibration/pilot.jsonl.gz',pilot)
    jwrite('audits/reference_mapping.json',mapping)
    jwrite('provenance/semantic_hashes.json',semantic)
    pending={}
    for name in ('quarantine','needs_review'):
        p=P/('runs/train5000-live/'+name+'.jsonl'); b, records=frozen(p); source_hashes[str(p.relative_to(P))]=sha(b)
        pending[name]={'records':len(records),'sha256':sha(b)}
    for pstr in ('runs/decision-crossaudit-20261101/confirmed_conflicts.json', 'runs/train-conflict-adjudication/collected/summary.json'):
        raw = (P/pstr).read_bytes(); item = json.loads(raw); source_hashes[pstr] = sha(raw)
        if 'excluded_families' in item:
            if all_ids.intersection(item['excluded_families']): raise ValueError('confirmed conflict in release')
            item = {'excluded_family_count': len(item['excluded_families']), 'basis': item.get('basis'), 'unrepresentative_sample': item.get('unrepresentative_sample')}
        pending[pstr] = {'sha256': sha(raw), 'metadata': item}
    jwrite('qa/quarantine_summary.json',pending)
    jwrite('reports/pending_summary.json',{'pilot_calibration':len(pilot),'train':pending})
    token_path = P/'runs/train5000-live/checkpoints/000500/token_measurements.json'
    token_bytes = token_path.read_bytes(); token = json.loads(token_bytes)
    source_hashes[str(token_path.relative_to(P))] = sha(token_bytes)
    token_counts = [h['token_count'] for f in token['families'] for h in f['histories']]
    token_summary = {'checkpoint': '000500', 'family_count': len(token['families']), 'history_count': len(token_counts), 'min_tokens': min(token_counts), 'max_tokens': max(token_counts), 'tokenizer': 'Phi-4-mini-instruct GPT2TokenizerFast', 'chat_template_sha256': token['chat_template_sha256'], 'input_sha256': token['input_sha256'], 'scope': 'full actor template with neutral user turn at checkpoint, not this entire later snapshot or other templates'}
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=P,text=True).strip()
    status=subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=P,text=True)
    diff=subprocess.check_output(['git','diff','HEAD','--','data_factory'],cwd=P)
    manifest={'build_utc':start,'code_head':head,'tracked_worktree_dirty':bool(status),'tracked_status':status.splitlines(),'data_factory_diff_sha256':sha(diff),'packager_sha256':sha(Path(__file__).read_bytes()),'sources_sha256':source_hashes,'counts':summaries,'pilot_calibration_count':len(pilot),'audit_objects':len(cache),'audit_references':len(mapping),'audit_identity_method':'sha256(original project-relative path) plus sha256(content); distinct source paths never merge even for identical bytes', 'review_protocol':'Mixed batches and protocols; no claim of uniformly granular blind review. Legacy cache and newer native independent reviews have different provenance; inspect each audit record.','semantic_hash_method':'SHA256 canonical sorted-key UTF-8 JSON with audit.records and candidate observed.audit_id replaced by fixed sentinel; all other values unchanged','history_token_measurement':token_summary}
    jwrite('provenance/manifest.json',manifest)
    jwrite('qa/release_validation.json',{'result':'pass','factory_validate_and_quality_check':'all released families','cross_split_group_overlap':0,'duplicate_family_ids':0,'candidate_id_scope':'unique within each family; use family_id plus candidate id as composite key','cross_split_history_hash_collisions':0,'all_audit_pointers_resolved':True,'export_quality_analyze_passed':True,'unique_observed_audit_ids':True,'semantic_hashes_match':True})
    table='\n'.join(f"| {s} | {v['families']} | {v['nodes']} | {v['candidate_instances']} | {v['unique_candidate_texts']} |" for s,v in summaries.items())
    card='''---
configs:
- config_name: default
  data_files:
  - split: train
    path: data/train/*.jsonl.gz
  - split: validation
    path: data/validation/*.jsonl.gz
  - split: test
    path: data/test/*.jsonl.gz
---
# Reason-sensitive roleplay 数据集 — IN_PROGRESS

私有研究数据，模型合成并经模型审查，未进行人类审查；不构成人类金标准。当前快照并非最终发布，曾发生质量修订与撤回；不同批次使用不同的审查流程，审查记录见 audits。标注中 intended 与 observed 分开，前者不应当作为真值。完整族文件含教师信息；默认节点视图不含教师脚手架或决策契约。

| split | families | nodes | candidate instances | unique candidate texts |
|---|---:|---:|---:|---:|
'''+table+'''

每族 12 个节点、48 个候选实例；实例数量与去重文本数量不同。目标为 train 5000 / validation 500 / test 800 families，当前尚有差距。Pilot 为独立校准数据，不计入已发布数据。候选 ID 仅保证族内唯一，跨族使用 family_id 与 candidate id 的复合键。按来源组隔离分割，已检查精确历史跨 split 散列冲突；这不排除语义近重复。000500 检查点以 Phi-4-mini 模板实测 514 族、1028 条历史，范围 450–1341 tokens；该实测不覆盖本快照全部族或其他模板。Test 严禁用于训练、teacher 或 probe。CrossWOZ 仅用于 train 统计与表达规律，未复制或读取其 test；参考摘要仅为小摘要。完整审计对象可能含审核用上下文，应在分享前审核访问范围。本数据未指定许可。
'''
    write('README.md',card.encode())
    write('build.log',('build_utc='+start+'\nresult=pass\n').encode())
    files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name!='SHA256SUMS')
    write('SHA256SUMS',''.join(sha(p.read_bytes())+'  '+str(p.relative_to(OUT))+'\n' for p in files).encode())
    print(json.dumps({'counts':summaries,'pilot_calibration':len(pilot),'files':len(files)+1,'bytes':sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()),'audit_objects':len(cache)},ensure_ascii=False))

if __name__=='__main__':
    try: main()
    except Exception as exc:
        print('BUILD FAILED:',repr(exc),file=sys.stderr)
        sys.exit(1)
