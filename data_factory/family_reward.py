"""Frozen, factorized family rewards. No LLM scorer or trainer is hidden here.

All candidates passed to advantages() must be independent current-policy draws.
Offline anchors are a separate fixed reward argument, never rollout replacements.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import isfinite
from typing import Mapping, Sequence

@dataclass(frozen=True)
class Score:
    decision: str
    decision_ok: float
    grounded: float
    naturalness: float
    verification_ok: float = 1.0

    def __post_init__(self):
        if not self.decision:
            raise ValueError('decision must be nonempty')
        for key in ('decision_ok', 'grounded', 'naturalness', 'verification_ok'):
            value = getattr(self, key)
            if not isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f'{key} outside [0,1]')

    @property
    def q(self):
        return self.decision_ok * self.grounded * self.verification_ok

@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    kind: str
    allowed_pairs: tuple[tuple[str, str], ...]


def weights(nodes: Sequence[str], edges: Sequence[Edge], mode='degree'):
    """Symmetric coefficients of ONE scalar objective, not per-node rescaling.

    Degree mode: F = mean_b f_b + lam * mean_b mean_{e incident b} kappa_e.
    An isolated node contributes zero relation reward.
    """
    if not nodes or len(set(nodes)) != len(nodes):
        raise ValueError('unique nonempty nodes required')
    if mode not in ('degree', 'uniform'):
        raise ValueError('mode must be degree or uniform')
    degree = dict.fromkeys(nodes, 0)
    seen = set()
    for e in edges:
        key = tuple(sorted((e.source, e.target)))
        if (e.source == e.target or e.source not in degree or e.target not in degree
                or key in seen or e.kind not in ('preserve', 'change')
                or not e.allowed_pairs or any(len(p) != 2 for p in e.allowed_pairs)):
            raise ValueError(f'invalid or duplicate edge: {e}')
        seen.add(key)
        degree[e.source] += 1
        degree[e.target] += 1
    if mode == 'uniform':
        return [1 / len(edges)] * len(edges) if edges else []
    return [(1 / degree[e.source] + 1 / degree[e.target]) / len(nodes) for e in edges]


def node_reward(s: Score, eta=0.2):
    return s.q * (1 + eta * s.naturalness)


def kernel(left: Score, right: Score, edge: Edge):
    return left.q * right.q * float((left.decision, right.decision) in edge.allowed_pairs)


def _check(nodes, edges, lam, eta, alpha, anchors, mode):
    for name, value in (('lam', lam), ('eta', eta), ('alpha', alpha)):
        if not isfinite(value) or value < 0:
            raise ValueError(f'invalid {name}')
    if alpha > 1:
        raise ValueError('alpha must be <= 1')
    result = weights(nodes, edges, mode)
    if alpha:
        if anchors is None or any(n not in anchors or not anchors[n] for n in nodes):
            raise ValueError('fixed nonempty anchor pool required for each node')
        if any(s.q < 0.999 for n in nodes for s in anchors[n]):
            raise ValueError('only audited correct anchors are allowed')
    return result


def _mean(values):
    values = list(values)
    return sum(values) / len(values)


def score_family(outputs: Mapping[str, Score], edges: Sequence[Edge], *,
                 lam=0.5, eta=0.2, mode='degree', alpha=0.0,
                 anchors: Mapping[str, Sequence[Score]] | None = None):
    """Optional anchor objective is explicitly different from pure on-policy F.

    edge_alpha = (1-alpha)*k(yu,yv)
               + alpha/2*(E_av k(yu,av) + E_au k(au,yv)).
    Anchors and alpha are fixed BEFORE drawing this rollout batch.
    """
    ws = _check(list(outputs), edges, lam, eta, alpha, anchors, mode)
    value = _mean(node_reward(s, eta) for s in outputs.values())
    for e, w in zip(edges, ws):
        left, right = outputs[e.source], outputs[e.target]
        relation = (1 - alpha) * kernel(left, right, e)
        if alpha:
            relation += alpha / 2 * (
                _mean(kernel(left, a, e) for a in anchors[e.target])
                + _mean(kernel(a, right, e) for a in anchors[e.source]))
        value += lam * w * relation
    return value


def conditional_scores(pools: Mapping[str, Sequence[Score]], edges: Sequence[Edge], *,
                       lam=0.5, eta=0.2, mode='degree', alpha=0.0, anchors=None):
    """E[F|current candidate] minus candidate-independent constants.

    Complexity O(sum_edges K_u*K_v), plus fixed-anchor cross products.
    Scores/evaluator/graph are detached and frozen during each update.
    """
    ws = _check(list(pools), edges, lam, eta, alpha, anchors, mode)
    if any(len(p) < 2 for p in pools.values()):
        raise ValueError('each node needs >=2 independent online candidates')
    out = {n: [node_reward(s, eta) / len(pools) for s in p] for n, p in pools.items()}
    for e, w in zip(edges, ws):
        left, right = pools[e.source], pools[e.target]
        for i, a in enumerate(left):
            for j, b in enumerate(right):
                r = lam * w * (1 - alpha) * kernel(a, b, e)
                out[e.source][i] += r / len(right)
                out[e.target][j] += r / len(left)
        if alpha:
            for i, a in enumerate(left):
                out[e.source][i] += lam*w*alpha/2*_mean(
                    kernel(a, ref, e) for ref in anchors[e.target])
            for j, b in enumerate(right):
                out[e.target][j] += lam*w*alpha/2*_mean(
                    kernel(ref, b, e) for ref in anchors[e.source])
    return out


def advantages(pools, edges, **kwargs):
    scores = conditional_scores(pools, edges, **kwargs)
    return {n: [v - (sum(values) - v)/(len(values)-1) for v in values]
            for n, values in scores.items()}


def recovery_diagnostics(pools, threshold=0.5):
    """Suggest a SEPARATE auxiliary CE/KL batch; never alter online pools.

    All-equal nonzero scores also give zero LOO. Record it, not just all-fail.
    This helper does not train a teacher or guarantee a successful update.
    """
    if not 0 <= threshold <= 1 or any(not p for p in pools.values()):
        raise ValueError('invalid recovery inputs')
    return {n: {'all_fail': max(s.q for s in p) < threshold,
                'quality_tied': max(s.q for s in p)-min(s.q for s in p) < 1e-12,
                'auxiliary_loss': 'audited_teacher_ce_or_kl' if max(s.q for s in p) < threshold else None}
            for n, p in pools.items()}
