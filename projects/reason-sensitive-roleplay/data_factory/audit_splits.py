#!/usr/bin/env python3
"""Audit frozen cross-split nearest neighbours using the shared eight model slots.

Only actor-visible material enters the independent quality calls. Writers receive
neither other-split text nor review feedback. Retrieval is heuristic, not a proof
of semantic independence. Existing raw calls and decisions remain immutable.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import fcntl
import hashlib
import json
from pathlib import Path
import time

import watch_global_quality as qa
from quality import analyze

RUNS = {'train': 'train5000-live', 'dev': 'dev500-live', 'test': 'test800-live'}
TARGETS = {'train': 5000, 'dev': 500, 'test': 800}
PRIORITY = {'train': 0, 'dev': 1, 'test': 2}


def freeze():
    families, sources = [], {}
    for split, directory in RUNS.items():
        path = qa.ROOT/'runs'/directory/'families.jsonl'
        raw = path.read_bytes()
        excluded = qa.read(path.parent/'exclusions.json', {})
        rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
        assert all(f['split'] == split for f in rows)
        rows = [f for f in rows if f['status'] == 'audited' and f['family_id'] not in excluded]
        sources[split] = {'path': str(path.relative_to(qa.ROOT)),
                          'sha256': hashlib.sha256(raw).hexdigest(), 'families': len(rows)}
        families.extend(rows)
    return families, sources


def merge_exclusions(families):
    byid = {f['family_id']: f for f in families}
    additions = {split: {} for split in RUNS}
    for path in (qa.OUT/'decisions').glob('*.json'):
        rec = qa.read(path, {})
        if rec.get('status') != 'confirmed_duplicate':
            continue
        if rec.get('a') not in byid or rec.get('b') not in byid:
            continue
        a, b = byid[rec['a']], byid[rec['b']]
        assert a['split'] != b['split']
        keep, hold = sorted((a, b), key=lambda f: PRIORITY[f['split']])
        additions[hold['split']][hold['family_id']] = {
            'reason': 'two independent blind reviews confirm cross-split concrete-story duplication',
            'related_family_id': keep['family_id'], 'source': str(path.relative_to(qa.ROOT))}
    for split, records in additions.items():
        if not records:
            continue
        run = qa.ROOT/'runs'/RUNS[split]
        with (run/'cross_split_exclusions.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            existing = qa.read(run/'exclusions.json', {})
            existing.update({k: v for k, v in records.items() if k not in existing})
            qa.atomic(run/'exclusions.json', existing)


def once():
    families, sources = freeze()
    mechanical = analyze(families)
    if not mechanical['passed']:
        raise ValueError('cross-split mechanical validation failed: '+str(mechanical['errors'][:5]))
    tasks = []
    keys = []
    for score, a, b in qa.top_pairs(families, cross_split=True):
        a, b = sorted((a, b), key=lambda f: PRIORITY[f['split']])
        key = qa.pair_key(a, b)
        keys.append(key)
        if not (qa.OUT/'decisions'/f'{key}.json').exists():
            tasks.append((a, b, key))
    # Small batches bound each review context. All calls share dispatch's slots.
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = [pool.submit(qa.pair_batch, tasks[i:i+4]) for i in range(0, len(tasks), 4)]
        for job in as_completed(jobs):
            job.result()
    byid = {f['family_id']: f for f in families}
    for key in keys:
        rec = qa.read(qa.OUT/'decisions'/f'{key}.json', {})
        if rec.get('status') == 'pending':
            qa.adjudicate_pending(rec, byid[rec['a']], byid[rec['b']])
    merge_exclusions(families)
    statuses = Counter(qa.read(qa.OUT/'decisions'/f'{key}.json', {}).get('status', 'missing') for key in keys)
    record = {'utc_epoch': time.time(), 'sources': sources, 'mechanical_passed': True,
              'retrieval': 'global top 30 cross-split character-trigram TF-IDF pairs; heuristic',
              'pairs': keys, 'status_counts': dict(statuses), 'shared_total_model_slots': 8,
              'human_review': 'not_sampled'}
    batch = qa.digest(sources)[:20]
    qa.atomic(qa.OUT/'batches'/f'{batch}.json', record)
    qa.atomic(qa.OUT/'latest.json', record)
    print(json.dumps(record, ensure_ascii=False), flush=True)
    return {split: data['families'] for split, data in sources.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--watch', action='store_true')
    args = parser.parse_args()
    qa.OUT = qa.ROOT/'runs/split-quality-live'
    for sub in ('decisions', 'batches', 'raw'):
        (qa.OUT/sub).mkdir(parents=True, exist_ok=True)
    with (qa.OUT/'watch.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        previous = None
        while True:
            try:
                if not (qa.ROOT/'runs/CLI_QUOTA_EXHAUSTED.json').exists():
                    _, sources = freeze()
                    counts = {split: data['families'] for split, data in sources.items()}
                    changed = previous is None or counts['train'] >= previous['train']+250 or any(
                        counts[s] >= previous[s]+50 for s in ('dev','test'))
                    final = all(counts[s] >= TARGETS[s] for s in TARGETS)
                    if changed or (final and counts != previous):
                        previous = once()
            except Exception as exc:
                qa.event('cross_split_watch_error', error=repr(exc))
                if not args.watch:
                    raise
            if not args.watch:
                return
            time.sleep(45)


if __name__ == '__main__':
    main()
