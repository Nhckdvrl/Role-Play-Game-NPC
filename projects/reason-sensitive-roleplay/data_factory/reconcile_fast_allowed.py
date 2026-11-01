"""Conservative metadata repair from two existing independent review contexts.

This never changes a candidate, an observed label, or the actor-visible input.
It cannot resolve reviewer disagreement or repair an actually wrong negative.
"""
from copy import deepcopy
import hashlib
import json

from factory import actor_messages, validate


def actor_hash(family):
    messages = [actor_messages(family, h, b)
                for h in family['histories'] for b in family['branches']]
    return hashlib.sha256(json.dumps(messages, ensure_ascii=False,
                                    sort_keys=True).encode()).hexdigest()


def reconcile(family, mapping, actors):
    repaired = deepcopy(family)
    before = actor_hash(family)
    changes = []
    for branch in repaired['branches']:
        views = [actors[n] for n, (_, bid) in mapping.items() if bid == branch['id']]
        if len(views) != 2 or set(views[0]) != set(views[1]):
            raise ValueError('history-specific independent action sets disagree')
        allowed = set(branch['allowed_decisions']) | set(views[0])
        if not allowed <= set(repaired['decision_inventory']):
            raise ValueError('unknown independent action')
        for candidate in branch['candidates']:
            observed = candidate['observed']
            if (not observed['decision_correct']) and observed['decision_id'] in allowed:
                raise ValueError('a negative is independently reasonable')
            if observed['decision_correct'] and observed['decision_id'] not in allowed:
                raise ValueError('positive action not supported')
        if allowed != set(branch['allowed_decisions']):
            changes.append({'branch': branch['id'], 'before': branch['allowed_decisions'],
                            'after': sorted(allowed), 'basis': 'same extra actions in both history-local judgments'})
            branch['allowed_decisions'] = sorted(allowed)
    by = {b['id']: b for b in repaired['branches']}
    edges = []
    for edge in repaired['edges']:
        a, b = edge['source'].split('::')[1], edge['target'].split('::')[1]
        left, right = set(by[a]['allowed_decisions']), set(by[b]['allowed_decisions'])
        if edge['kind'] == 'change' and left & right:
            continue
        edge = deepcopy(edge)
        edge['allowed_pairs'] = ([[d, d] for d in sorted(left & right)] if edge['kind'] == 'preserve'
                                 else [[x, y] for x in sorted(left) for y in sorted(right)])
        if edge['allowed_pairs']:
            edges.append(edge)
    for history in repaired['histories']:
        hid = history['id']
        existing = {tuple(sorted((e['source'].split('::')[1], e['target'].split('::')[1])))
                    for e in edges if e['kind'] == 'change' and e['source'].startswith(hid+'::')}
        for i in range(1, 7):
            for j in range(i+1, 7):
                a, b = f'B{i}', f'B{j}'
                left, right = set(by[a]['allowed_decisions']), set(by[b]['allowed_decisions'])
                if len(existing) >= 2 or (a, b) in existing or left & right:
                    continue
                edges.append({'source': hid+'::'+a, 'target': hid+'::'+b, 'kind': 'change',
                              'allowed_pairs': [[x, y] for x in sorted(left) for y in sorted(right)],
                              'justification': '两处可见事实：'+by[a]['visible_observation']+'；'
                              +by[b]['visible_observation']+'；独立审查后允许集合互不相交。'})
                existing.add((a, b))
        if len(existing) < 2:
            raise ValueError('fewer than two independently disjoint changes')
    repaired['edges'] = edges
    if actor_hash(repaired) != before:
        raise ValueError('actor-visible inputs changed')
    original_candidates = [b['candidates'] for b in family['branches']]
    if original_candidates != [b['candidates'] for b in repaired['branches']]:
        raise ValueError('candidate text or intended/observed labels changed')
    validate(repaired)
    return repaired, {'policy': 'metadata-only, both history-local judgments agree; negative conflicts block',
                      'actor_messages_sha256_before': before, 'actor_messages_sha256_after': actor_hash(repaired),
                      'candidate_text_intended_observed_unchanged': True, 'changes': changes,
                      'edges_before': family['edges'], 'edges_after': edges}
