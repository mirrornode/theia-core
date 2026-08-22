from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    INFO = "INFO"


class Verdict(str, Enum):
    HOLD = "HOLD"
    CLEAR_FOR_INDEPENDENT_REVIEW = "CLEAR_FOR_INDEPENDENT_REVIEW"


@dataclass(frozen=True)
class FileOperation:
    path: str
    operation: str
    destination_path: str | None = None


@dataclass(frozen=True)
class TargetManifest:
    repository: str
    head_sha: str
    base_sha: str
    changed_files: tuple[FileOperation, ...] = ()
    verification_artifacts: tuple[str, ...] = ()
    verification_artifact_root: str | None = None
    external_effects: tuple[str, ...] = ()
    working_directory: str | None = None
    report_binding_working_directory: str | None = None
    verification_authorized: bool = False
    handoff_authorized_scope_digest: str | None = None
    handoff_changed_paths: tuple[str, ...] = ()
    raw_status_paths: tuple[str, ...] = ()
    parsed_status_paths: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "TargetManifest":
        operations = tuple(
            FileOperation(
                path=item["path"],
                operation=item["operation"],
                destination_path=item.get("destination_path"),
            )
            for item in value.get("changed_files", [])
        )
        return cls(
            repository=value["repository"],
            head_sha=value["head_sha"],
            base_sha=value["base_sha"],
            changed_files=operations,
            verification_artifacts=tuple(value.get("verification_artifacts", [])),
            verification_artifact_root=value.get("verification_artifact_root"),
            external_effects=tuple(value.get("external_effects", [])),
            working_directory=value.get("working_directory"),
            report_binding_working_directory=value.get("report_binding_working_directory"),
            verification_authorized=bool(value.get("verification_authorized", False)),
            handoff_authorized_scope_digest=value.get("handoff_authorized_scope_digest"),
            handoff_changed_paths=tuple(value.get("handoff_changed_paths", [])),
            raw_status_paths=tuple(value.get("raw_status_paths", [])),
            parsed_status_paths=tuple(value.get("parsed_status_paths", [])),
        )


@dataclass(frozen=True)
class Finding:
    check_id: str
    severity: Severity
    title: str
    detail: str
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["severity"] = self.severity.value
        return result


@dataclass(frozen=True)
class ReviewResult:
    target: TargetManifest
    findings: tuple[Finding, ...]
    checks_run: tuple[str, ...]
    verdict: Verdict
    authority_effect: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": asdict(self.target),
            "findings": [item.to_dict() for item in self.findings],
            "checks_run": list(self.checks_run),
            "verdict": self.verdict.value,
            "authority_effect": self.authority_effect,
        }
