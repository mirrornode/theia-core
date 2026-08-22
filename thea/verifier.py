from __future__ import annotations

import re
from collections import Counter

from .models import Finding, ReviewResult, Severity, TargetManifest, Verdict
from .path_policy import PathPolicyError, normalize_repo_path, validate_artifact_path

_SHA40 = re.compile(r"^[0-9a-f]{40}$")
MOVE_OPERATIONS = {"MOVE", "RENAME"}


def _finding(check_id: str, severity: Severity, title: str, detail: str, **evidence: object) -> Finding:
    return Finding(check_id, severity, title, detail, dict(evidence))


def _check_exact_head(target: TargetManifest) -> list[Finding]:
    findings: list[Finding] = []
    if not _SHA40.fullmatch(target.head_sha):
        findings.append(_finding("THEA-ID-001", Severity.P1, "Target is not bound to an immutable head", "head_sha must be a full 40-character lowercase Git SHA.", value=target.head_sha))
    if not _SHA40.fullmatch(target.base_sha):
        findings.append(_finding("THEA-ID-002", Severity.P2, "Base is not bound to an immutable commit", "base_sha must be a full 40-character lowercase Git SHA.", value=target.base_sha))
    if target.head_sha == target.base_sha:
        findings.append(_finding("THEA-ID-003", Severity.P2, "Head and base are identical", "A review target must identify a meaningful comparison surface."))
    return findings


def _check_file_operations(target: TargetManifest) -> list[Finding]:
    findings: list[Finding] = []
    write_targets: list[str] = []
    source_paths: set[str] = set()

    for item in target.changed_files:
        try:
            source = normalize_repo_path(item.path)
        except PathPolicyError as exc:
            findings.append(_finding("THEA-PATH-001", Severity.P1, "Unsafe source path", str(exc), path=item.path, operation=item.operation))
            continue

        if source in source_paths:
            findings.append(_finding("THEA-COLLISION-001", Severity.P2, "Duplicate source operation", "More than one operation is declared for the same normalized source path.", path=source))
        source_paths.add(source)
        write_targets.append(source)

        operation = item.operation.upper()
        if operation in MOVE_OPERATIONS:
            if not item.destination_path:
                findings.append(_finding("THEA-PATH-002", Severity.P2, "Move/rename has no destination", "MOVE and RENAME require a destination_path.", path=source))
                continue
            try:
                destination = normalize_repo_path(item.destination_path)
            except PathPolicyError as exc:
                findings.append(_finding("THEA-PATH-003", Severity.P1, "Unsafe destination path", str(exc), path=item.destination_path, source=source))
                continue
            if destination == source:
                findings.append(_finding("THEA-COLLISION-002", Severity.P2, "Move/rename targets itself", "Source and destination resolve to the same normalized path.", path=source))
            write_targets.append(destination)
        elif item.destination_path is not None:
            findings.append(_finding("THEA-PATH-004", Severity.P2, "Unexpected destination path", "Only MOVE and RENAME may declare a destination_path.", path=source, operation=operation))

    counts = Counter(write_targets)
    for path, count in sorted(counts.items()):
        if count > 1:
            findings.append(_finding("THEA-COLLISION-003", Severity.P2, "Write-target collision", "Two or more declared operations converge on the same normalized write target.", path=path, occurrences=count))
    return findings


def _check_verification_scope(target: TargetManifest) -> list[Finding]:
    findings: list[Finding] = []
    if target.verification_artifacts and not target.verification_artifact_root:
        findings.append(_finding("THEA-VERIFY-001", Severity.P1, "Verification artifacts lack a positive root", "Artifact paths must be positively contained under a declared verification_artifact_root; disjointness alone is insufficient."))
        return findings
    if target.verification_artifact_root:
        try:
            root = normalize_repo_path(target.verification_artifact_root)
        except PathPolicyError as exc:
            findings.append(_finding("THEA-VERIFY-002", Severity.P1, "Unsafe verification artifact root", str(exc), root=target.verification_artifact_root))
            return findings
        for path in target.verification_artifacts:
            try:
                validate_artifact_path(path, root)
            except PathPolicyError as exc:
                findings.append(_finding("THEA-VERIFY-003", Severity.P1, "Verification artifact escapes its authority boundary", str(exc), path=path, artifact_root=root))

    if target.external_effects:
        findings.append(_finding("THEA-VERIFY-004", Severity.P2, "Verification carries external effects", "Verification external effects require a separately declared and authorized effect surface; inherited implementation effects fail closed.", external_effects=list(target.external_effects)))
    if not target.verification_authorized and (target.verification_artifacts or target.external_effects):
        findings.append(_finding("THEA-VERIFY-005", Severity.P2, "Verification-specific authorization is absent", "Implementation authorization must not be interpreted as verification authorization."))
    return findings


def _check_evidence_agreement(target: TargetManifest) -> list[Finding]:
    findings: list[Finding] = []
    if target.raw_status_paths or target.parsed_status_paths:
        raw: set[str] = set()
        parsed: set[str] = set()
        try:
            raw = {normalize_repo_path(path) for path in target.raw_status_paths}
            parsed = {normalize_repo_path(path) for path in target.parsed_status_paths}
        except PathPolicyError as exc:
            findings.append(_finding("THEA-EVIDENCE-001", Severity.P1, "Status evidence contains unsafe path identity", str(exc)))
            return findings
        if raw != parsed:
            findings.append(_finding("THEA-EVIDENCE-002", Severity.P2, "Raw and parsed status evidence disagree", "Human-visible status and machine-consumed status must reconcile exactly after parsing and normalization.", raw_paths=sorted(raw), parsed_paths=sorted(parsed)))
    return findings


def _check_lineage(target: TargetManifest) -> list[Finding]:
    findings: list[Finding] = []
    if target.working_directory != target.report_binding_working_directory:
        findings.append(_finding("THEA-LINEAGE-001", Severity.P2, "Working directory is outside the report binding", "The checkout identity used for execution must match the directory identity bound into the report.", working_directory=target.working_directory, report_binding_working_directory=target.report_binding_working_directory))
    if target.handoff_changed_paths and not target.handoff_authorized_scope_digest:
        findings.append(_finding("THEA-LINEAGE-002", Severity.P2, "Handoff is unbound to authorized scope", "A handoff reporting changed paths must carry forward the authorization lineage or its immutable scope digest.", changed_paths=list(target.handoff_changed_paths)))
    return findings


def verify_target(target: TargetManifest) -> ReviewResult:
    checks = (
        "exact-head-identity",
        "normalized-path-denotation",
        "write-target-collision",
        "positive-verification-containment",
        "verification-authority-separation",
        "raw-parsed-evidence-agreement",
        "handoff-and-checkout-lineage",
    )
    findings = (
        _check_exact_head(target)
        + _check_file_operations(target)
        + _check_verification_scope(target)
        + _check_evidence_agreement(target)
        + _check_lineage(target)
    )
    blocking = any(item.severity in {Severity.P1, Severity.P2} for item in findings)
    verdict = Verdict.HOLD if blocking else Verdict.CLEAR_FOR_INDEPENDENT_REVIEW
    return ReviewResult(target, tuple(findings), checks, verdict)
