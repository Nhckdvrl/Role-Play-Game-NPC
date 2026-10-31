"""Mechanical quality checks and descriptive statistics; no semantic review is performed."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import statistics
import sys

import factory

GRID = {(correct, style) for correct in (True, False)
        for style in ('natural_character', 'plain_natural')}


def encoded(value):
    """Canonical JSON serialized as UTF-8; used for hashes and multiset comparison."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def message_hash(messages):
    return sha256(encoded(messages)).hexdigest()


def check_family(family):
    errors = []
    if family.get('status') == 'smoke_unreviewed':
        errors.append('smoke_unreviewed fixture is not production quality data')
    try:
        factory.validate(family)
    except Exception as exc:
        errors.append(f'factory.validate: {exc}')
    histories = family.get('histories', [])
    branches = family.get('branches', [])
    details = {'block_message_sha256': {}, 'history_message_sha256': {}}
    for b in branches:
        for h in histories:
            cs = [c for c in b.get('candidates', []) if c.get('history_id') == h.get('id')]
            grid = Counter((c['intended']['decision_correct'], c['intended']['style']) for c in cs)
            if len(cs) != 4 or set(grid) != GRID or any(count != 1 for count in grid.values()):
                errors.append(f"{h['id']}::{b['id']}: expected exactly one candidate per intended grid cell")
    if family.get('history_mode') == 'natural':
        for h in histories:
            messages = h.get('messages', [])
            if len(messages) % 2 or not 15 <= len(messages) // 2 <= 25:
                errors.append(f"{h['id']}: natural history requires 15..25 complete exchanges")
    elif family.get('history_mode') == 'exact_permutation':
        blocks = family.get('blocks', [])
        if not 4 <= len(blocks) <= 6:
            errors.append('exact permutation requires 4..6 blocks')
        if not {'cooperate', 'resist'} <= {b.get('posture') for b in blocks}:
            errors.append('exact permutation requires cooperative and resistant blocks')
        for b in blocks:
            details['block_message_sha256'][b['id']] = message_hash(b['messages'])
        baseline = Counter(encoded(m) for b in blocks for m in b['messages'])
        for h in histories:
            details['history_message_sha256'][h['id']] = message_hash(h['messages'])
            if Counter(encoded(m) for m in h['messages']) != baseline:
                errors.append(f"{h['id']}: message multiset differs from blocks")
            # Check each ordered segment against the unique source block hash as well.
            by_id = {b['id']: b for b in blocks}
            offset = 0
            for block_id in h.get('block_order', []):
                if block_id not in by_id:
                    errors.append(f"{h['id']}: unknown block {block_id}")
                    continue
                block = by_id[block_id]
                segment = h['messages'][offset:offset + len(block['messages'])]
                if message_hash(segment) != details['block_message_sha256'][block_id]:
                    errors.append(f"{h['id']}: block {block_id} hash mismatch")
                offset += len(block['messages'])
    kinds = {e.get('kind') for e in family.get('edges', [])}
    if not {'preserve', 'change'} <= kinds:
        errors.append('at least one preserve and one change edge required')
    for e in family.get('edges', []):
        for left, right in e.get('allowed_pairs', []):
            if (e['kind'] == 'preserve' and left != right) or (e['kind'] == 'change' and left == right):
                errors.append(f"edge {e['source']} -> {e['target']}: {e['kind']} pair inconsistent")
    for b in branches:
        for c in b.get('candidates', []):
            observed = c.get('observed')
            if family.get('status') == 'audited' and observed is None:
                errors.append(f"{c['id']}: audited candidate missing observed")
            if b.get('kind') == 'insufficient_evidence' and observed and observed['decision_correct']:
                requested = set(observed['requested_conditions'])
                if not any(set(route) <= requested for route in b.get('verification_routes', [])):
                    errors.append(f"{c['id']}: observed correct B6 lacks a complete route")
                if not observed['feasible_verification'] or observed['premature_commitment']:
                    errors.append(f"{c['id']}: observed correct B6 fails feasible/premature gate")
    return errors, details


def length_summary(values):
    if not values:
        return {'count': 0, 'min': None, 'median': None, 'mean': None, 'max': None}
    return {'count': len(values), 'min': min(values), 'median': statistics.median(values),
            'mean': statistics.mean(values), 'max': max(values)}


def analyze(families, comparison=(), notes=()):
    errors = []
    details = []
    kinds, motives, intended_decisions, observed_decisions = Counter(), Counter(), Counter(), Counter()
    texts, lengths, audits = Counter(), defaultdict(list), {}
    b6 = Counter()
    by_family, groups = {}, {}
    note_map = {n['family_id']: n for n in notes if 'family_id' in n}
    for snapshot_name, rows in [('input', families), ('comparison', comparison)]:
        seen = set()
        for f in rows:
            fid, group, split = f['family_id'], f['split_group_id'], f['split']
            if fid in seen:
                errors.append(f'{snapshot_name}: duplicate family_id {fid}')
            seen.add(fid)
            identity = (group, split)
            if fid in by_family and by_family[fid] != identity:
                errors.append(f'family identity conflict for {fid}: {by_family[fid]} vs {identity}')
            by_family[fid] = identity
            if group in groups and groups[group] != split:
                errors.append(f'split_group contamination for {group}: {groups[group]} vs {split}')
            groups[group] = split
            if snapshot_name != 'input':
                continue
            family_errors, family_details = check_family(f)
            errors.extend(f'{fid}: {err}' for err in family_errors)
            details.append({'family_id': fid, **family_details, 'errors': family_errors})
            note = note_map.get(fid, {})
            motive = note.get('motive')
            if isinstance(motive, list):
                motives.update(motive)
            elif motive:
                motives[motive] += 1
            else:
                motives['unprovided'] += 1
            for b in f.get('branches', []):
                kinds[b['kind']] += 1
                for c in b.get('candidates', []):
                    texts[c['text']] += 1
                    intended = c['intended']
                    intended_decisions[intended['decision_id']] += 1
                    key = f"{intended['decision_correct']}::{intended['style']}"
                    lengths[key].append(len(c['text']))
                    obs = c.get('observed')
                    if obs is not None:
                        audit_id = obs['audit_id']
                        ref = (fid, c['id'])
                        if audit_id in audits:
                            errors.append(f'duplicate observed audit_id {audit_id}: {audits[audit_id]} and {ref}')
                        else:
                            audits[audit_id] = ref
                        observed_decisions[obs['decision_id']] += 1
                    if b['kind'] == 'insufficient_evidence':
                        if obs is None:
                            b6['unobserved'] += 1
                        else:
                            b6['observed'] += 1
                            complete = any(set(route) <= set(obs['requested_conditions']) for route in b['verification_routes'])
                            b6['route_complete' if complete else 'route_incomplete'] += 1
                            b6['feasible' if obs['feasible_verification'] else 'not_feasible'] += 1
                            b6['premature' if obs['premature_commitment'] else 'not_premature'] += 1
    return {'passed': not errors, 'errors': errors, 'families': details,
            'statistics': {'family_count': len(families), 'branch_kind': dict(kinds), 'motive_from_notes': dict(motives),
                           'intended_decisions': dict(intended_decisions), 'observed_decisions': dict(observed_decisions),
                           'candidate_instances': sum(texts.values()), 'unique_candidate_texts': len(texts),
                           'repeated_text_distinct_count': sum(n > 1 for n in texts.values()),
                           'repeated_text_extra_instances': sum(n - 1 for n in texts.values() if n > 1),
                           'repeated_texts': [{'text': t, 'count': n} for t, n in texts.items() if n > 1],
                           'intended_grid_character_lengths': {k: length_summary(v) for k, v in sorted(lengths.items())},
                           'b6_observed': dict(b6)},
            'limitations': 'Mechanical checks and counts only; no semantic evidence, naturalness, audit independence, or factual validity has been established. Observed labels are recorded annotations, not verified truth. Length is Unicode code points.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input')
    parser.add_argument('--report', required=True)
    parser.add_argument('--comparison', help='another JSONL snapshot for family and split-group identity checks')
    parser.add_argument('--notes', help='optional JSONL with family_id and motive (string or array)')
    args = parser.parse_args(argv)
    families = list(factory.read_jsonl(args.input))
    comparison = list(factory.read_jsonl(args.comparison)) if args.comparison else []
    notes = list(factory.read_jsonl(args.notes)) if args.notes else []
    report = analyze(families, comparison, notes)
    output = Path(args.report)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'passed': report['passed'], 'families': len(families), 'errors': len(report['errors'])}))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
