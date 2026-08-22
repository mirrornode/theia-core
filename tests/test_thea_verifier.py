from thea.models import TargetManifest
from thea.verifier import verify_target


HEAD = "a" * 40
BASE = "b" * 40


def manifest(**overrides):
    value = {
        "repository": "mirrornode/example",
        "head_sha": HEAD,
        "base_sha": BASE,
        "changed_files": [{"path": "src/a.py", "operation": "MODIFY"}],
        "verification_artifact_root": "artifacts/thea",
        "verification_artifacts": ["artifacts/thea/report.json"],
        "verification_authorized": True,
        "working_directory": "checkout/repo",
        "report_binding_working_directory": "checkout/repo",
    }
    value.update(overrides)
    return TargetManifest.from_dict(value)


def ids(result):
    return {finding.check_id for finding in result.findings}


def test_clean_manifest_clears_for_independent_review():
    result = verify_target(manifest())
    assert result.verdict.value == "CLEAR_FOR_INDEPENDENT_REVIEW"
    assert result.authority_effect == "NONE"


def test_traversal_fails_closed():
    result = verify_target(
        manifest(changed_files=[{"path": "src/../../escape.py", "operation": "MODIFY"}])
    )
    assert result.verdict.value == "HOLD"
    assert "THEA-PATH-001" in ids(result)


def test_destination_collision_fails_closed():
    result = verify_target(
        manifest(
            changed_files=[
                {"path": "src/a.py", "operation": "MOVE", "destination_path": "src/c.py"},
                {"path": "src/b.py", "operation": "MOVE", "destination_path": "src/c.py"},
            ]
        )
    )
    assert "THEA-COLLISION-003" in ids(result)


def test_verification_artifact_requires_positive_containment():
    result = verify_target(
        manifest(verification_artifacts=[".github/workflows/audit.yml"])
    )
    assert "THEA-VERIFY-003" in ids(result)


def test_external_effect_does_not_inherit_into_verification():
    result = verify_target(manifest(external_effects=["POST https://prod.example/deploy"]))
    assert "THEA-VERIFY-004" in ids(result)


def test_raw_parsed_status_must_agree():
    result = verify_target(
        manifest(raw_status_paths=["src/a.py"], parsed_status_paths=["src/b.py"])
    )
    assert "THEA-EVIDENCE-002" in ids(result)


def test_handoff_must_carry_authorization_lineage():
    result = verify_target(manifest(handoff_changed_paths=["src/a.py"]))
    assert "THEA-LINEAGE-002" in ids(result)


def test_verification_requires_specific_authorization():
    result = verify_target(manifest(verification_authorized=False))
    assert "THEA-VERIFY-005" in ids(result)
