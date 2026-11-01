#!/usr/bin/env python3
"""Resume metadata-only holds using verified cached reviews; never calls a model."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator
import agent_dispatch
import fast_generate as gen
import fast_review


def cached(task, run, model, effort):
    identity = {k: task[k] for k in ('stage', 'payload', 'instruction', 'output_schema')}
    identity.update(model=model, effort=effort)
    digest = hashlib.sha256(agent_dispatch._canonical(identity).encode()).hexdigest()
    base = Path(run)/'raw'/task['stage']/digest
    for attempt in sorted(base.glob('attempt-*')):
        try:
            meta = json.loads((attempt/'metadata.json').read_text())
            result = json.loads((attempt/'result.json').read_text())
            assert meta['status'] == 'success' and meta['task_hash'] == digest
            Draft202012Validator(task['output_schema']).validate(result)
            return {'status': 'success', 'path': str(attempt), 'result': result, 'reused': True}
        except (OSError, ValueError, KeyError, AssertionError):
            continue
    raise ValueError('offline reconciliation requires an existing matching successful review')


def reconcile_run(run):
    run = Path(run).resolve()
    with (run/'.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state_path = run/'state.json'
        original = json.loads(state_path.read_text())
        split = original['split']
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
        out = run/'metadata_reconciliation'/stamp
        out.mkdir(parents=True)
        gen.put(out/'state_before.json', original)
        accepted = {f['family_id']: f for f in gen.read_rows(run/'families.jsonl')}
        novelty = [(fid, gen.novelty_features(f, gen.summary_of(f))) for fid, f in accepted.items()]
        pending = list(gen.read_rows(run/'needs_review.jsonl'))
        exclusions = json.loads((run/'exclusions.json').read_text()) if (run/'exclusions.json').exists() else {}
        results = []
        for item in original['completed']:
            issues = item.get('review', {}).get('issues', [])
            metadata_hold = bool(issues) and all(':needs_allowed_reconciliation:' in s for s in issues)
            import_failure = item.get('error', '').startswith("ImportError: cannot import name 'reconcile' from 'reconcile_allowed'")
            if item['status'] != 'needs_review' or not (metadata_hold or import_failure):
                continue
            fid = item['family_id']
            if fid in exclusions:
                continue
            job = Path(item['job'])
            family = json.loads((job/'draft.json').read_text())
            result = gen.gate_review(fast_review.review(family, job, gen.MODEL, dispatcher=cached))
            row = {'family_id': fid, 'review': result, 'model_calls': 0}
            if import_failure:
                gen.put(out/(fid+'-engineering_failure.json'), item)
                item.pop('error', None)
                item.update(status=result['status'], review=result, engineering_retry_utc=stamp)
                pending = [p for p in pending if p['family_id'] != fid]
                if result['status'] != 'audited':
                    pending.append(dict(item))
            if result['status'] == 'audited':
                repaired = json.loads(Path(result['reviewed_path']).read_text())
                features = gen.novelty_features(repaired, item.get('summary') or gen.summary_of(repaired))
                duplicate = next((other for other, old in novelty if gen.similar_features(features, old)), None)
                cross = None if duplicate else gen.registry_append(run.parent/'split_fingerprints.jsonl', split,
                                                                   repaired['split_group_id'], repaired)
                if duplicate or cross:
                    row['withheld_novelty'] = duplicate or cross
                    if import_failure:
                        item.update(status='quarantined', error='possible duplicate of '+str(duplicate or cross))
                        pending.append(dict(item))
                else:
                    gen.put(out/(fid+'-previous_result.json'), item)
                    item.update(status='audited', review=result, metadata_reconciled_utc=stamp)
                    accepted[fid] = repaired
                    novelty.append((fid, features))
                    pending = [p for p in pending if p['family_id'] != fid]
                    gen.put(out/(fid+'-family.json'), repaired)
                    row['released'] = True
            results.append(row)
        original['audited_families'] = len(accepted)
        original['audited_train'] = len(accepted) if split == 'train' else 0
        original['candidate_instances'] = sum(len(b['candidates']) for f in accepted.values() for b in f['branches'])
        original['unique_candidate_texts_within_families'] = sum(len({c['text'] for b in f['branches'] for c in b['candidates']}) for f in accepted.values())
        original['unique_candidate_texts_global'] = len({c['text'] for f in accepted.values() for b in f['branches'] for c in b['candidates']})
        original['quality_scheduler'] = {'version': 'yield-warning70-stop50-v1', **gen.yield_gate(original['completed'])}
        original.setdefault('metadata_reconciliation_history', []).append({'path': str(out), 'model_calls': 0,
            'newly_released': sum(bool(x.get('released')) for x in results)})
        gen.jsonl(run/'families.jsonl', accepted.values())
        gen.jsonl(run/'needs_review.jsonl', pending)
        gen.put(state_path, original)
        gen.put(out/'summary.json', {'results': results, 'model_calls': 0, 'families_after': len(accepted)})
        print(json.dumps({'split': split, 'checked': len(results),
            'newly_released': sum(bool(x.get('released')) for x in results),
            'families_after': len(accepted), 'quality_scheduler': original['quality_scheduler'], 'model_calls': 0}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    reconcile_run(parser.parse_args().run_dir)
