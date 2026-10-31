#!/usr/bin/env python3
"""Snapshot actual run artifacts and metered CLI attempts; targets are not results."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

from factory import validate


def read(path, default=None):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return default


def jsonl(path):
    rows, errors = [], []
    if path.exists():
        for i, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            if line.strip():
                try: rows.append(json.loads(line))
                except ValueError: errors.append(i)
    return rows, errors


def family_files(path, recursive=False):
    files = path.rglob('RCD-*.json') if recursive else path.glob('RCD-*.json')
    found={}
    for p in files:
        x=read(p)
        if isinstance(x,dict) and isinstance(x.get('family'),dict):x=x['family']
        if isinstance(x,dict) and x.get('family_id') and x.get('status')!='smoke_unreviewed':found[x['family_id']]=x
    return found


def stamp(s):
    try: return datetime.fromisoformat(s.replace('Z', '+00:00'))
    except (ValueError, AttributeError): return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', required=True, type=Path)
    a = parser.parse_args(); root = a.run_dir.resolve()
    if not root.is_dir(): parser.error('run directory does not exist')
    plan_path = Path(__file__).with_name('production_plan.json')
    config = read(root / 'run_config.json', {}) or {}
    plan = read(plan_path, {}) or {}
    target = config.get('initial_end_to_end_batch', plan.get('initial_end_to_end_batch'))
    train_target = config.get('family_targets', {}).get('train', plan.get('family_targets', {}).get('train'))
    designed = family_files(root/'skeletons', True)
    if not designed: designed = family_files(root/'designs', True)
    prepared = family_files(root/'prepared')
    inherited = read(root/'source_run.json', {}) or {}
    if inherited.get('source_run'):
        ancestor = Path(inherited['source_run'])
        if not designed: designed = family_files(ancestor/'skeletons', True)
        if not prepared: prepared = family_files(ancestor/'prepared')
    histories = family_files(root/'with_histories')
    histories = {k:v for k,v in histories.items() if len(v.get('histories', [])) == 2 and all(h.get('messages') for h in v['histories'])}
    drafts = family_files(root/'drafts')
    if not histories:
        histories = {k:v for k,v in drafts.items() if len(v.get('histories', [])) == 2 and all(h.get('messages') for h in v['histories'])}
    good, bad = [], {}
    for fid, f in drafts.items():
        try: validate(f); good.append(fid)
        except Exception as exc: bad[fid] = str(exc)
    final, final_errors = jsonl(root/'families.jsonl')
    pending, pending_errors = jsonl(root/'needs_review.jsonl')
    audited = []
    for f in final:
        if f.get('status') != 'audited' or f.get('split') not in ('pilot','train','dev','test'): continue
        try: validate(f); audited.append(f)
        except Exception as exc: bad[f.get('family_id', '<unknown>')] = str(exc)
    needs_review = [f for f in pending if f.get('status') == 'needs_review' and f.get('split') in ('pilot','train','dev','test')]
    candidates = [c for f in drafts.values() for b in f.get('branches', []) for c in b.get('candidates', [])]
    node_ids = {(fid, c.get('history_id'), b.get('id')) for fid,f in drafts.items() for b in f.get('branches', []) for c in b.get('candidates', [])}
    stages = defaultdict(Counter); token_sums = Counter(); token_present = Counter(); missing_usage = 0
    starts, ends, models, efforts = [], [], set(), set()
    attempts = sorted((root/'raw').glob('*/*/attempt-*'))
    unfinished = 0
    for attempt in attempts:
        if not attempt.is_dir() or not re.fullmatch(r'attempt-\d+', attempt.name): continue
        stage = attempt.parent.parent.name; meta = read(attempt/'metadata.json')
        if not isinstance(meta, dict):
            unfinished += 1; stages[stage]['unfinished'] += 1; continue
        s = stages[stage]
        launched = meta.get('failure_type') != 'launch_error' and not str(meta.get('error') or '').startswith('CLI launch failed:')
        if launched:
            s['calls'] += 1
            if int(attempt.name.split('-')[1]) > 0: s['retries'] += 1
        else: s['launch_errors'] += 1
        s[meta.get('status', 'unknown')] += 1
        if meta.get('timed_out'): s['timeout'] += 1
        kind = meta.get('failure_type') or (meta.get('error') or '').lower()
        if 'parse' in kind: s['parse_failure'] += 1
        if 'schema' in kind: s['schema_failure'] += 1
        if meta.get('model'): models.add(meta['model'])
        if meta.get('effort'): efforts.add(meta['effort'])
        start, end = stamp(meta.get('started_utc')), stamp(meta.get('finished_utc'))
        if start: starts.append(start)
        if end: ends.append(end)
        usage = meta.get('usage')
        if not isinstance(usage, dict):
            if launched: missing_usage += 1
        else:
            for key in ('input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens'):
                v = usage.get(key)
                if isinstance(v, (int,float)) and not isinstance(v,bool): token_sums[key] += v; token_present[key] += 1
    token_values = {k: token_sums[k] if token_present[k] else None for k in ('input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens')}
    references = sorted(str(p.relative_to(root)) for p in root.glob('*reference*report*.json'))
    measurements = sorted(str(p.relative_to(root)) for p in root.rglob('*.json') if 'token' in p.name.lower() and 'raw' not in p.relative_to(root).parts)
    counts = {'designed_unique':len(designed),'prepared':len(prepared),'histories_complete':len(histories),
              'drafts':len(drafts),'drafts_structure_validated':len(good),'audited_in_final':len(audited),
              'needs_review_in_separate_file':len(needs_review),'candidate_nodes':len(node_ids),
              'candidate_instances':len(candidates),'candidate_unique_texts':len({c.get('text') for c in candidates if c.get('text')}),
              'human_review_not_sampled':sum(f.get('audit',{}).get('human_review')=='not_sampled' for f in audited+needs_review)}
    train_count = sum(f.get('split')=='train' for f in audited)
    report = {'snapshot_utc':datetime.now(timezone.utc).isoformat(), 'counts':counts,
              'structure_errors':bad, 'jsonl_parse_error_lines':{'families':final_errors,'needs_review':pending_errors},
              'split_freeze':read(root/'split_freeze.json'), 'review_decisions':read(root/'review_decisions.json'),
              'reference_reports':references,'token_measurements':measurements,
              'first_delivery_target':target,'first_delivery_complete':len(audited)>=target if isinstance(target,int) else None,
              'train_target_from_configuration':train_target, 'audited_train_in_this_run':train_count,
              'train_target_reached_in_this_run':train_count>=train_target if isinstance(train_target,int) else None,
              'target_source':str(plan_path) if 'family_targets' not in config else 'run_config.json',
              'api_sessions_by_stage':dict(stages), 'unfinished_attempts':unfinished,
              'measured_tokens':token_values,'token_field_observations':dict(token_present),'attempts_missing_usage':missing_usage,
              'cost_usd':None,'models':sorted(models),'efforts':sorted(efforts),'concurrency':config.get('concurrency'),
              'first_attempt_started_utc':min(starts).isoformat() if starts else None,
              'last_attempt_finished_utc':max(ends).isoformat() if ends else None,
              'observed_wall_seconds':(max(ends)-min(starts)).total_seconds() if starts and ends else None,
              'excluded_unmetered_work':{'native_design_subagents_tokens':None,'cli_probes_tokens':None,'web_download_cost_usd':None,
                    'note':'These activities are not completely represented by raw attempt metadata; usage and cost are unknown.'},
              'scope':'Snapshot of artifacts present in this run only; planned seeds and smoke data are not completed families.'}
    report['inherited_stage_source'] = inherited.get('source_run')
    (root/'run_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    files=[]; errors=[]
    for p in sorted(root.rglob('*')):
        if not p.is_file() or p.name == 'artifact_manifest.json': continue
        try:
            digest=hashlib.sha256(); size=0
            with p.open('rb') as stream:
                while chunk := stream.read(1024*1024): digest.update(chunk); size+=len(chunk)
            files.append({'path':str(p.relative_to(root)),'bytes':size,'sha256':digest.hexdigest()})
        except OSError as exc: errors.append({'path':str(p.relative_to(root)),'error':str(exc)})
    (root/'artifact_manifest.json').write_text(json.dumps({'snapshot_utc':report['snapshot_utc'],'files':files,'errors':errors,'note':'Manifest excludes itself; concurrent writes may change artifacts after snapshot.'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f"DATA_PROGRESS: designed={counts['designed_unique']}, histories={counts['histories_complete']}, drafts={counts['drafts']}, audited={counts['audited_in_final']}, needs_review={counts['needs_review_in_separate_file']}; CLI calls={sum(s['calls'] for s in stages.values())}, unfinished={unfinished}; USD unknown. Train target reached in this run: {report['train_target_reached_in_this_run']}.")


if __name__=='__main__': main()
