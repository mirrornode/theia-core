import pytest

from thea.models import TargetManifest
from thea.path_policy import PathPolicyError, normalize_repo_path, validate_artifact_path
from thea.probe_harness import ProbeSuite
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
    assert result.claim_limit == "SUPPLIED_MANIFEST_SEMANTICS_ONLY"
    assert "immutable-identifier-shape" in result.checks_run
    assert "status-path-set-agreement" in result.checks_run


def test_manifest_boolean_is_strict_not_truthy_string():
    with pytest.raises(ValueError, match="verification_authorized must be a boolean"):
        manifest(verification_authorized="false")


@pytest.mark.parametrize(
    "path",
    [
        "../../other-repo/secret.ts",
        "a/../../../etc/passwd",
        "src/../../escape.ts",
        ".git/config",
        ".github/workflows/audit.yml",
        "src/x\ny.ts",
        "src/dir/",
        "/etc/passwd",
        "~/secrets",
        "C:/Windows/System32",
        "src//a.ts",
        "./src/a.ts",
        "src/./a.ts",
        "src/b/../a.ts",
        "src/ a.ts/x",
        "src/a\x00.ts",
        "x" * 2000,
    ],
)
def test_adversarial_path_corpus_refused(path):
    with pytest.raises(PathPolicyError):
        if path.startswith(".git") or path.startswith(".github"):
            validate_artifact_path(path, "artifacts/thea")
        else:
            normalize_repo_path(path)


@pytest.mark.parametrize(
    "path",
    ["src/a.ts", "a/b/c/d/e.txt", "file-with.many.dots.ts", "unicode/café.ts"],
)
def test_legitimate_path_baselines_accepted(path):
    assert normalize_repo_path(path)


def test_positive_containment_is_segment_aware():
    assert validate_artifact_path("build/report.json", "build") == "build/report.json"
    with pytest.raises(PathPolicyError):
        validate_artifact_path("buildother/report.json", "build")


def test_traversal_fails_closed():
    result = verify_target(
        manifest(changed_files=[{"path": "src/../../escape.py", "operation": "MODIFY"}])
    )
    assert result.verdict.value == "HOLD"
    assert "THEA-PATH-001" in ids(result)


def test_unknown_operation_fails_closed():
    result = verify_target(manifest(changed_files=[{"path": "src/a.py", "operation": "FLY"}]))
    assert result.verdict.value == "HOLD"
    assert "THEA-OP-001" in ids(result)


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
    result = verify_target(manifest(verification_artifacts=[".github/workflows/audit.yml"]))
    assert "THEA-VERIFY-003" in ids(result)


def test_verification_root_must_not_cover_implementation_surface():
    result = verify_target(
        manifest(
            changed_files=[{"path": "src/a.py", "operation": "MODIFY"}],
            verification_artifact_root="src",
            verification_artifacts=["src/thea/report.json"],
        )
    )
    assert result.verdict.value == "HOLD"
    assert "THEA-VERIFY-006" in ids(result)


def test_external_effect_does_not_inherit_into_verification():
    result = verify_target(manifest(external_effects=["POST https://prod.example/deploy"]))
    assert "THEA-VERIFY-004" in ids(result)


def test_supplied_status_path_sets_must_agree():
    result = verify_target(
        manifest(raw_status_paths=["src/a.py"], parsed_status_paths=["src/b.py"])
    )
    assert "THEA-EVIDENCE-002" in ids(result)


def test_handoff_must_carry_authorization_lineage_reference():
    result = verify_target(manifest(handoff_changed_paths=["src/a.py"]))
    assert "THEA-LINEAGE-002" in ids(result)


def test_verification_requires_specific_authorization():
    result = verify_target(manifest(verification_authorized=False))
    assert "THEA-VERIFY-005" in ids(result)


def test_probe_harness_requires_accept_baseline():
    suite = ProbeSuite(schema_validate=lambda value: None)
    suite.refuse("must refuse", {"bad": True})
    assert suite.disposition()["verdict"] == "INVALID_RUN_NO_ACCEPT_BASELINE"


def test_probe_harness_scores_acceptance_as_hole():
    suite = ProbeSuite(schema_validate=lambda value: None)
    suite.refuse("unsafe accepted", {"bad": True}, family="PATH_TRAVERSAL")
    suite.accept("legitimate baseline", {"ok": True})
    disposition = suite.disposition()
    assert disposition["verdict"] == "HOLD"
    assert disposition["holes"] == ["unsafe accepted"]


def test_probe_harness_does_not_count_unexpected_exception_as_refusal():
    def broken(_value):
        raise RuntimeError("validator crashed")

    suite = ProbeSuite(schema_validate=broken, refusal_errors=(ValueError,))
    suite.refuse("crash is not a refusal", {"bad": True})
    suite.accept("baseline", {"ok": True})
    assert suite.disposition()["verdict"] == "INVALID_RUN_HARNESS_ERROR"
