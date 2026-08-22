from __future__ import annotations

import json
from dataclasses import dataclass

from .model_adapter import LocalModelUnavailable, review_with_local_model
from .models import ReviewResult


ORACLE_SYSTEM_PROMPT = """You are Oracle, the interpretive review layer above Thea.
Thea's deterministic findings are authoritative evidence inputs for this review but do not grant execution or merge authority.
Your job is to attack assumptions, identify missing adversarial probes, compare claimed invariants against the supplied evidence, and explain uncertainty.
Never downgrade or erase a deterministic P1/P2 finding. Never claim independent provenance when reviewing implementation or corrections you participated in.
Return concise JSON with keys: additional_risks, missing_probes, synthesis, recommended_next_action.
"""


@dataclass(frozen=True)
class OracleResult:
    deterministic_verdict: str
    model_review_status: str
    model_output: str | None
    authority_effect: str = "NONE"

    def to_dict(self) -> dict[str, str | None]:
        return {
            "deterministic_verdict": self.deterministic_verdict,
            "model_review_status": self.model_review_status,
            "model_output": self.model_output,
            "authority_effect": self.authority_effect,
        }


def interpret(result: ReviewResult, context: str = "") -> OracleResult:
    payload = {
        "thea_result": result.to_dict(),
        "context": context,
        "review_rules": [
            "Treat exact-head identity as mandatory.",
            "Attack denotation beneath representation.",
            "Check positive containment, not only exclusion.",
            "Treat corrections as new attack surfaces.",
            "Separate technical usefulness from provenance independence.",
            "Passing tests are evidence, never adversarial completeness.",
            "Look for human-visible versus machine-consumed evidence divergence.",
            "Look for self-modification of validators, CI, policy, and audit evidence.",
        ],
    }
    try:
        output = review_with_local_model(
            ORACLE_SYSTEM_PROMPT,
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
        )
        status = "LOCAL_MODEL_COMPLETE"
    except LocalModelUnavailable:
        output = None
        status = "LOCAL_MODEL_UNAVAILABLE"
    return OracleResult(
        deterministic_verdict=result.verdict.value,
        model_review_status=status,
        model_output=output,
    )
