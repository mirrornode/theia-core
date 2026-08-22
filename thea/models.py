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


def _required_string(value: dict[str, Any], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise ValueError(f"{key} must be a non-empty string")
    return item


def _optional_string(value: dict[str, Any], key: str) -> str | None:
    item = value.get(key)
    if item is None:
        return None
    if not isinstance(item, str) or not item:
        raise ValueError(f"{key} must be null or a non-empty string")
    return item


def _string_tuple(value: dict[str, Any], key: str) -> tuple[str, ...]:
    item = value.get(key, [])
    if not isinstance(item, (list, tuple)):
        raise ValueError(f"{key} must be an array of strings")
    if any(not isinstance(entry, str) or not entry for entry in item):
        raise ValueError(f"{key} must contain only non-empty strings")
    return tuple(item)


def _strict_bool(value: dict[str, Any], key: str, default: bool = False) -> bool:
    item = value.get(key, default)
    if type(item) is not bool:
        raise ValueError(f"{key} must be a boolean")
    return item


def _operations(value: dict[str, Any]) -> tuple[FileOperation, ...]:
    raw = value.get("changed_files", [])
    if not isinstance(raw, (list, tuple)):
        raise ValueError("changed_files must be an array")
    operations: list[FileOperation] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"changed_files[{index}] must be an object")
        path = item.get("path")
        operation = item.get("operation")
        destination = item.get("destination_path")
        if not isinstance(path, str) or not path:
            raise ValueError(f"changed_files[{index}].path must be a non-empty string")
        if not isinstance(operation, str) or not operation:
            raise ValueError(f"changed_files[{index}].operation must be a non-empty string")
        if destination is not None and (not isinstance(destination, str) or not destination):
            raise ValueError(
                f"changed_files[{index}].destination_path must be null or a non-empty string"
            )
        operations.append(FileOperation(path=path, operation=operation, destination_path=destination))
    return tuple(operations)


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
        if not isinstance(value, dict):
            raise ValueError("manifest must be an object")
        return cls(
            repository=_required_string(value, "repository"),
            head_sha=_required_string(value, "head_sha"),
            base_sha=_required_string(value, "base_sha"),
            changed_files=_operations(value),
            verification_artifacts=_string_tuple(value, "verification_artifacts"),
            verification_artifact_root=_optional_string(value, "verification_artifact_root"),
            external_effects=_string_tuple(value, "external_effects"),
            working_directory=_optional_string(value, "working_directory"),
            report_binding_working_directory=_optional_string(
                value, "report_binding_working_directory"
            ),
            verification_authorized=_strict_bool(value, "verification_authorized"),
            handoff_authorized_scope_digest=_optional_string(
                value, "handoff_authorized_scope_digest"
            ),
            handoff_changed_paths=_string_tuple(value, "handoff_changed_paths"),
            raw_status_paths=_string_tuple(value, "raw_status_paths"),
            parsed_status_paths=_string_tuple(value, "parsed_status_paths"),
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
    claim_limit: str = "SUPPLIED_MANIFEST_SEMANTICS_ONLY"

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": asdict(self.target),
            "findings": [item.to_dict() for item in self.findings],
            "checks_run": list(self.checks_run),
            "verdict": self.verdict.value,
            "authority_effect": self.authority_effect,
            "claim_limit": self.claim_limit,
        }
