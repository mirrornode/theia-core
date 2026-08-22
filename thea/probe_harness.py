from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class ProbeResult:
    label: str
    family: str | None
    expected: str
    observed: str
    detail: str = ""

    @property
    def ok(self) -> bool:
        return self.expected == self.observed


@dataclass
class ProbeSuite:
    """Adversarial probe harness with inverted test polarity.

    Security probes declare inputs that MUST be refused. Acceptance is a hole.
    Unexpected exceptions are harness faults, not successful refusals. A clean
    result is invalid unless at least one legitimate accept-baseline also ran.
    """

    schema_validate: Callable[[Any], None]
    semantic_validate: Callable[[Any], None] | None = None
    refusal_errors: tuple[type[BaseException], ...] = (ValueError,)
    results: list[ProbeResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def _run(self, record: Any) -> tuple[str, str]:
        for stage, fn in (("schema", self.schema_validate), ("semantic", self.semantic_validate)):
            if fn is None:
                continue
            try:
                fn(record)
            except self.refusal_errors as exc:
                return "REFUSED", f"{stage}: {exc}"
            except Exception as exc:
                raise RuntimeError(
                    f"{stage} raised unscored {type(exc).__name__}: {exc}; "
                    "unexpected exceptions never count as security refusals"
                ) from exc
        return "ACCEPTED", ""

    def refuse(self, label: str, record: Any, *, family: str | None = None) -> bool:
        try:
            observed, detail = self._run(record)
        except RuntimeError as exc:
            self.errors.append(f"{label}: {exc}")
            return False
        self.results.append(ProbeResult(label, family, "REFUSED", observed, detail))
        return observed == "REFUSED"

    def accept(self, label: str, record: Any, *, family: str | None = None) -> bool:
        try:
            observed, detail = self._run(record)
        except RuntimeError as exc:
            self.errors.append(f"{label}: {exc}")
            return False
        self.results.append(ProbeResult(label, family, "ACCEPTED", observed, detail))
        return observed == "ACCEPTED"

    def disposition(self) -> dict[str, object]:
        holes = [result for result in self.results if not result.ok and result.expected == "REFUSED"]
        broken = [result for result in self.results if not result.ok and result.expected == "ACCEPTED"]
        baselines = [result for result in self.results if result.expected == "ACCEPTED"]
        families = sorted({result.family for result in self.results if result.family})

        if not baselines:
            verdict = "INVALID_RUN_NO_ACCEPT_BASELINE"
        elif self.errors:
            verdict = "INVALID_RUN_HARNESS_ERROR"
        elif broken:
            verdict = "BROKEN_VALID_INPUT_REFUSED"
        elif holes:
            verdict = "HOLD"
        else:
            verdict = "ADVERSARIAL_PROBES_PASS"

        return {
            "verdict": verdict,
            "probe_count": len(self.results),
            "families_covered": families,
            "holes": [result.label for result in holes],
            "broken_baselines": [result.label for result in broken],
            "harness_errors": list(self.errors),
            "claim_limit": (
                "ADVERSARIAL_PROBES_PASS never implies EXACT_HEAD_REVIEWED, "
                "INDEPENDENT_EXACT_HEAD_REVIEWED, CONSTITUTIONALLY_CLEARED, or MERGE_AUTHORIZED"
            ),
        }
