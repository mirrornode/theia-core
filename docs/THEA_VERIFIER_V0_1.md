# Thea Verifier v0.1

**Status:** implementation proposal on feature branch; not canon, not deployed, not merge-authorized  
**Authority effect:** `NONE`  
**Repository:** `mirrornode/theia-core`  
**Operator surface:** MOPCON, read-only projection first  
**Interpretive layer:** Oracle  

## 1. Purpose

Thea is MIRRORNODE's owned verification kernel. Its purpose is to make repeatable security and governance review available without depending on a vendor-specific code-review quota.

Thea is not yet an observed exact-head checkout verifier. v0.1 validates the semantics of a supplied target manifest and requires immutable-form 40-character Git identifiers, but it does not yet prove that the referenced repository checkout actually resolves to those commits. That observed checkout binding is the first open implementation requirement after this proposal.

A clean v0.1 result therefore carries the explicit claim limit:

`SUPPLIED_MANIFEST_SEMANTICS_ONLY`

It does **not** establish `EXACT_HEAD_REVIEWED`, independent review, constitutional clearance, merge authorization, deployment authorization, or runtime authority.

## 2. Architecture

Thea separates deterministic enforcement from model reasoning.

### Deterministic kernel

The deterministic layer validates bounded properties that should not depend on model judgment:

- immutable Git identifier shape;
- strict manifest types and boolean semantics;
- normalized repository-relative path denotation;
- bounded file-operation vocabulary;
- positive verification-artifact containment;
- separation of verification artifacts from implementation write targets;
- protected control roots such as `.git` and `.github`;
- write-target and destination collisions;
- verification-specific authorization presence;
- verification external-effect separation;
- caller-supplied status-path-set agreement;
- working-directory/report-binding equality;
- handoff authorization-lineage reference presence;
- refusal-first adversarial probe scoring.

### Oracle layer

Oracle sits above the deterministic kernel. It receives Thea evidence and asks a locally served model to generate counterexamples, missing probes, uncertainty, and synthesis.

Oracle may add concerns. It may not erase deterministic P1/P2 findings, convert a HOLD into authority, or claim independent provenance when the reviewing model participated in implementation or correction.

The v0.1 model adapter refuses non-loopback endpoints. There is no cloud fallback. A future remote-model adapter would require its own explicitly governed disclosure, credential, transport, and authority boundary.

## 3. MIRRORNODE invariants carried forward

The implementation follows current MIRRORNODE integration and approval semantics rather than treating older runtime descriptions as automatic present authority.

From MICC and related governance work:

- verification and authorization remain separate states;
- a successful health, conformance, model, or test result does not self-authorize;
- approval-bearing actions require machine-verifiable approval evidence;
- requesting, authorizing, and executing identities remain separately attributable;
- canonical evidence remains MIRRORNODE-owned;
- missing or contradictory authority context fails closed.

From the PR #53 review cycle:

- passing tests are evidence, not adversarial completeness;
- review claims bind to immutable targets;
- denotation must be attacked beneath representation;
- resource identities are normalized before equality, uniqueness, or authorization decisions;
- positive containment is preferred over negative exclusion;
- every correction is a new attack surface;
- technical usefulness and provenance independence are separate dimensions;
- machine-consumed and human-visible evidence must be reconciled;
- self-modification of validators, CI, policy, review instructions, and evidence is a mandatory attack lens;
- finding lineage is preserved rather than flattened into resolved/unresolved.

## 4. Current claim ladder

No lower claim implies a higher claim:

`SCHEMA_VALID`
→ `SEMANTIC_VALID`
→ `TEST_SUITE_PASS`
→ `ADVERSARIAL_PROBES_PASS`
→ `EXACT_HEAD_REVIEWED`
→ `INDEPENDENT_EXACT_HEAD_REVIEWED`
→ `CONSTITUTIONALLY_CLEARED`
→ `MERGE_AUTHORIZED`

Thea v0.1 can contribute to the first four claim levels. Until the checkout-binding adapter exists, it does not itself emit `EXACT_HEAD_REVIEWED`.

## 5. Deterministic v0.1 checks

| Check | Current behavior | Claim limit |
|---|---|---|
| Immutable identifier shape | requires full lowercase 40-character head/base SHAs | does not prove commits exist or are checked out |
| Manifest typing | rejects truthy strings for booleans and malformed arrays/operation records | validates supplied JSON only |
| Path denotation | rejects traversal, absolute/home/drive-letter forms, control characters, backslashes, dot/empty segments, trailing separators, segment whitespace, overlength paths; NFC-normalizes Unicode | does not yet inspect symlinks/filesystem aliases |
| Operation vocabulary | accepts only `CREATE`, `MODIFY`, `DELETE`, `MOVE`, `RENAME`, `RESTORE` | does not execute operations |
| Positive artifact containment | artifacts must be under a declared root | root is supplied manifest evidence |
| Verification/implementation separation | artifact root and artifacts may not overlap implementation write targets | does not yet derive write scope from an observed Git diff |
| Protected roots | verification artifacts cannot target `.git` or `.github` | additional project-specific protected roots can be added later |
| Destination collision | normalized source/destination targets participate in collision detection | filesystem semantics not yet executed |
| Verification authorization | verification work carrying artifacts/effects requires a verification-specific authorization flag | v0.1 verifies typed presence, not a signed authorization object |
| External effects | verification external effects force a finding | no provider-side effect execution exists |
| Status path-set agreement | compares caller-supplied raw-derived and parsed path sets | **does not yet parse raw Git status itself** |
| Working-directory binding | supplied working directory must equal report-bound directory | does not yet prove either path is the checkout for the target SHA |
| Handoff lineage | handoff changes require an authorization-scope digest reference | does not yet recompute the digest or prove each changed path was authorized |

A P1 or P2 finding returns `HOLD`. A finding-free supplied manifest returns `CLEAR_FOR_INDEPENDENT_REVIEW` with `claim_limit=SUPPLIED_MANIFEST_SEMANTICS_ONLY`.

## 6. Permanent adversarial memory

`thea/adversarial_corpus.json` and `thea/probe_harness.py` are the first executable review-memory layer.

The harness uses inverted polarity:

- malicious probes are expected to be refused;
- acceptance is scored as a hole;
- unexpected exceptions are harness-integrity errors, not successful refusals;
- a clean adversarial run is invalid unless legitimate accept baselines were also exercised.

The initial permanent corpus includes:

- traversal and path aliases;
- protected `.git` / `.github` targets;
- verification artifact-root escape;
- validator/CI self-modification;
- duplicate MOVE destinations and source/destination collisions;
- status-evidence divergence;
- verification external effects;
- verification-specific authorization;
- handoff authorization lineage;
- working-directory binding;
- authorization revocation, supersession, and expiry lessons retained from PR #53;
- positive legitimate baselines.

Once a serious escaped defect is learned, the intended rule is that it becomes cheap to test forever.

## 7. Full-review corrections already made

The first internal review of Thea found several defects or overclaims in Thea itself. They are retained as review lineage rather than erased:

- **Harness disposition precedence:** an unexpected validator exception initially lost precedence to the missing-accept-baseline condition. Fixed so `INVALID_RUN_HARNESS_ERROR` dominates scoreability.
- **Operation vocabulary:** arbitrary operation names initially passed through the semantic kernel. Fixed with a bounded six-operation vocabulary.
- **Artifact-root overlap:** positive containment initially did not also reject an artifact root covering implementation write targets. Fixed.
- **Manifest booleans:** Python truthiness would have interpreted the string `"false"` as true. Fixed with strict boolean parsing.
- **Model egress:** the environment variable for the Oracle endpoint could have pointed to a remote service despite the documentation describing a local-only model. Fixed by enforcing loopback endpoints in v0.1.
- **Exact-head overclaim:** SHA shape was described too strongly as observed exact-head identity. Documentation and check naming corrected; checkout proof remains open.
- **Raw-status overclaim:** supplied path-set comparison was described too strongly as raw/parsed reconciliation. Documentation and check naming corrected; raw Git-status parsing remains open.
- **Handoff lineage depth:** current check verifies only lineage-reference presence. Cryptographic recomputation and path authorization remain open.

## 8. MOPCON projection boundary

The first MOPCON integration remains read-only.

MOPCON may project:

- repository and supplied head/base identifiers;
- whether checkout binding has been independently observed;
- deterministic verdict;
- claim limit;
- P1/P2/P3 counts;
- checks actually run;
- adversarial corpus coverage;
- Oracle availability and additional-risk synthesis;
- reviewer provenance / independence state;
- finding lineage;
- next lawful action.

MOPCON must not infer authorization from a Thea pass.

Recommended operator labels include:

- `HOLD`
- `MANIFEST CHECKS CLEAR`
- `EXACT-HEAD BINDING PENDING`
- `INDEPENDENT REVIEW PENDING`
- `CONSTITUTIONAL CONFIRMATION PENDING`
- `OPERATOR DISPOSITION REQUIRED`

## 9. NIST alignment target

Thea makes no claim of NIST certification or compliance merely by existing. It is designed to produce auditable engineering evidence that can support a NIST-aligned secure-development and AI-risk program.

### AI RMF

NIST AI 100-1, AI RMF 1.0, remains the published framework while NIST is working on a revision. Thea maps naturally to its `GOVERN`, `MAP`, `MEASURE`, and `MANAGE` functions through explicit authority boundaries, target/scope mapping, repeatable measurements and probes, fail-closed dispositions, and continuous regression capture.

NIST AI 600-1, the Generative AI Profile, is used as a companion reference for model-specific uncertainty, misuse/abuse surfaces, provenance, human oversight, and continuous evaluation.

### SSDF

NIST SP 800-218 SSDF v1.1 remains final. Thea supports its direction by protecting development evidence, making verification repeatable, preserving provenance, identifying vulnerabilities before release, and turning escaped defects into root-cause regression tests.

NIST SP 800-218A is final and augments SSDF v1.1 with AI-model-specific secure-development practices; it is relevant to Oracle model selection, serving, evaluation, provenance, and acquisition.

NIST SP 800-218 Rev. 1 / SSDF v1.2 is an initial public draft released December 17, 2025. Thea tracks it as a forward-compatibility reference, not as the final controlling SSDF baseline.

### CSF 2.0

Thea's evidence and disposition model is compatible with the CSF 2.0 emphasis on governance, risk communication, and evidence-backed risk management.

## 10. Current market expectations

Contemporary AI code-review systems make automatic re-review, repository/path instructions, agent instructions, tool/MCP context, file-specific findings, and review-session attribution reasonable baseline expectations.

Thea's differentiators are intended to be:

- owned availability rather than vendor review quota;
- deterministic refusal checks below model reasoning;
- exact target / provenance claim separation;
- permanent adversarial memory;
- explicit authority non-escalation;
- failure-lineage preservation;
- MOPCON projection of what is known, unknown, and still unauthorized.

## 11. Next implementation slices

Priority order after v0.1 review:

1. observed local Git checkout binding: repository identity, exact HEAD, base existence, diff acquisition;
2. raw `git status --porcelain=v1 -z` parsing and exact structural reconciliation;
3. cryptographic authorization-scope digest recomputation and handoff-path reconciliation;
4. symlink and repository-tree escape detection in isolated checkout;
5. schema/state-machine fuzzing adapters;
6. AST-aware self-modification detection for validators, policy, CI, and review instructions;
7. automatic corpus execution against every correction head;
8. reviewer-provenance ledger and finding-lineage store;
9. read-only MOPCON projection;
10. benchmark candidate local models against the permanent corpus before designating a default Oracle model.

## 12. Reference set

- NIST AI 100-1 — Artificial Intelligence Risk Management Framework (AI RMF 1.0)
- NIST AI 600-1 — Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile
- NIST SP 800-218 — Secure Software Development Framework v1.1 (Final)
- NIST SP 800-218A — Secure Software Development Practices for Generative AI and Dual-Use Foundation Models (Final)
- NIST SP 800-218 Rev. 1 — SSDF v1.2 (Initial Public Draft, 2025-12-17)
- NIST Cybersecurity Framework 2.0
- MIRRORNODE MICC v0.1 and current approval/governance evidence
- PR #53 exact-head adversarial review and retained review-memory corpus
