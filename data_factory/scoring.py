"""Semantic-evaluator contract + rule-based composition, not a trained scorer.

A backend must extract meanings from text. No substring heuristic is a truth judge.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Protocol, Sequence
from family_reward import Score

@dataclass(frozen=True)
class EvaluationRequest:
    request_id: str
    actor_messages: list[dict]
    allowed_decisions: list[str]
    candidate_text: str
    branch_kind: str
    verification_routes: list[list[str]]
    applicable_contract: list[str]
    evidence: list[dict]

@dataclass(frozen=True)
class EvaluationReport:
    request_id: str
    decision: str
    decision_ok: float
    grounded: float
    naturalness: float
    requested_conditions: tuple[str, ...]
    feasible_verification: float
    premature_commitment: bool
    confidence: float
    status: str = 'ok'

    def __post_init__(self):
        from math import isfinite
        for field in ('decision_ok', 'grounded', 'naturalness', 'feasible_verification', 'confidence'):
            value = getattr(self, field)
            if not isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f'invalid {field}')
        if self.status not in ('ok', 'abstain', 'parse_error', 'service_error'):
            raise ValueError('invalid evaluator status')

class Evaluator(Protocol):
    version: str
    def score_batch(self, requests: Sequence[EvaluationRequest]) -> list[EvaluationReport]: ...


def cache_key(request: EvaluationRequest, evaluator_version: str):
    from dataclasses import asdict
    payload = {'input': asdict(request), 'evaluator_version': evaluator_version}
    return sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def compose(request: EvaluationRequest, report: EvaluationReport) -> Score:
    if report.request_id != request.request_id:
        raise ValueError('evaluator result/request mismatch')
    if report.status != 'ok':
        raise ValueError('unscored output: retry/quarantine; never silently score zero')
    decision_ok = report.decision_ok if report.decision in request.allowed_decisions else 0.0
    verify = 1.0
    if request.branch_kind == 'insufficient_evidence':
        if not request.verification_routes or any(not r for r in request.verification_routes):
            raise ValueError('B6 requires nonempty sufficient verification routes')
        pinpoint = any(set(route) <= set(report.requested_conditions)
                       for route in request.verification_routes)
        verify = float(pinpoint and not report.premature_commitment) * report.feasible_verification
    return Score(report.decision, decision_ok, report.grounded, report.naturalness, verify)
