# Thea Verifier v0.1

**Status:** implementation proposal on feature branch; not canon, not deployed, not merge-authorized  
**Authority effect:** NONE  
**Repository:** `mirrornode/theia-core`  
**Operator surface:** MOPCON (read-only projection first)  
**Interpretive layer:** Oracle  

## 1. Purpose

Thea is MIRRORNODE's owned exact-head verification kernel. It exists so the ability to inspect a change does not depend on an external AI-review quota or vendor-specific review entitlement.

Thea is intentionally split into two layers:

1. **Deterministic kernel** — exact-head identity, normalized resource denotation, positive containment, collision analysis, evidence reconciliation, authorization-lineage checks, and permanent adversarial regression probes.
2. **Oracle layer** — a self-hosted model-backed adversarial interpreter that invents additional attacks and synthesizes uncertainty. Oracle may add findings but may not erase deterministic blockers or convert evidence into authority.

Thea is not a merge bot and is not a constitutional approver.

## 2. Existing MIRRORNODE contracts used

The implementation follows the current MIRRORNODE direction rather than the older `SYSTEM_CONTRACT.md` runtime registry where those conflict.

### MICC-derived invariants

- verification and authorization are separate states;
- a passing health/conformance check cannot self-authorize;
- governed invocations fail closed when context, scope, authority, or lifecycle evidence is absent;
- approval-bearing actions require machine-verifiable approval references;
- canonical evidence remains MIRRORNODE-owned;
- requesting, authorizing, and executing identities remain separately attributable.

### PR #53-derived review doctrine

- passing tests are evidence, not adversarial completeness;
- bind review to an immutable full head SHA;
- attack denotation beneath representation;
- normalize resource identity before comparison;
- prefer positive containment over pure exclusion;
- treat every correction as a new attack surface;
- preserve reviewer provenance separately from technical usefulness;
- detect machine/human evidence divergence;
- explicitly probe validator, CI, policy, and audit self-modification paths;
- preserve finding lineage across heads.

## 3. Current market expectations incorporated

As of August 2026, mainstream AI code-review products establish several reasonable expectations that Thea should meet or exceed:

- automatic review/re-review on new pushes;
- repository-wide and path-specific review instructions;
- use of repository agent instructions and task-specific review skills;
- tool/MCP context where useful;
- actionable, file-specific findings;
- review output that remains advisory rather than silently becoming a required human approval;
- reproducible evidence and session/attribution visibility.

Thea extends those expectations with MIRRORNODE-specific requirements: exact-head binding, provenance independence, positive authority containment, deterministic adversarial replay, and no dependency on a vendor review quota.

## 4. NIST alignment target

Thea does **not** claim NIST certification or compliance by existence. It is designed to produce evidence and operating practices that can support a NIST-aligned secure-development program.

### AI RMF 1.0 / NIST AI 600-1

The architecture maps naturally to the AI RMF functions:

- **GOVERN:** explicit authority boundaries, provenance, roles, review doctrine, retention of failure history.
- **MAP:** exact target identity, changed resource surface, external-effect and authority surface mapping.
- **MEASURE:** deterministic checks, adversarial probes, severity, evidence agreement, regression corpus.
- **MANAGE:** fail-closed HOLD disposition, bounded next action, regression capture, continuous improvement.

The GenAI Profile is reflected in the explicit handling of model uncertainty, provenance, misuse/abuse surfaces, human oversight, and continuous evaluation.

### NIST SP 800-218 SSDF v1.1

Thea supports SSDF outcomes by:

- preserving and protecting software-development evidence;
- enforcing repeatable verification tasks;
- checking source integrity and exact immutable targets;
- identifying vulnerabilities and unsafe design conditions before release;
- converting escaped defects into regression tests to address root causes;
- separating development/correction from independent verification evidence.

NIST published SP 800-218 Rev. 1 / SSDF v1.2 as an initial public draft in December 2025. Until it is final, Thea treats v1.1 as the final baseline and tracks the v1.2 draft as a forward-compatibility target.

### NIST SP 800-218A

Because Thea uses an AI model in the Oracle layer, model-specific secure-development and acquisition considerations are treated as part of the system lifecycle rather than as an exception to ordinary software security.

### NIST CSF 2.0

Thea's evidence model is compatible with the CSF 2.0 emphasis on governance and risk communication. Thea findings are designed to be consumable as governed evidence rather than opaque model output.

## 5. The deterministic kernel

Current v0.1 checks:

| Check | Behavior |
|---|---|
| Exact-head identity | requires full immutable head and base SHAs |
| Path denotation | rejects absolute, traversal, dot, empty, backslash, control-character, and trailing-separator paths |
| Positive artifact containment | verification artifacts must be under a declared root |
| Protected control roots | `.git` and `.github` are not valid verification artifact roots/targets |
| Destination collision | all normalized write targets participate in collision analysis |
| Verification external effects | inherited external effects fail closed |
| Verification authorization | implementation authority does not imply verification authority |
| Raw/parsed agreement | human-visible and machine-consumed path evidence must agree |
| Working-directory binding | execution checkout must match report-bound checkout |
| Handoff lineage | changed-path handoff requires carried authorization-scope evidence |

A P1 or P2 produces `HOLD`.

A clean deterministic result produces only `CLEAR_FOR_INDEPENDENT_REVIEW` — never `APPROVED`, `AUTHORIZED`, or `MERGE`.

## 6. Oracle layer

Oracle is above, not inside, the deterministic trust boundary.

Oracle receives:

- immutable target identity;
- deterministic findings;
- checks run;
- optional architecture/review context;
- standing MIRRORNODE review doctrine.

Oracle is instructed to:

- construct counterexamples;
- identify missing probe classes;
- challenge newly introduced boundaries;
- identify prose-vs-machine divergence;
- identify self-modification surfaces;
- state uncertainty;
- preserve provenance limitations.

Oracle cannot:

- erase deterministic findings;
- convert HOLD to authorization;
- claim independent provenance when contaminated;
- invoke a cloud fallback when the local model is absent.

The initial adapter targets an operator-owned OpenAI-compatible endpoint at `127.0.0.1` and can therefore sit behind Ollama, vLLM, llama.cpp-compatible gateways, or another locally controlled serving layer without changing Thea semantics.

## 7. Permanent adversarial memory

`thea/adversarial_corpus.json` is the seed review-memory corpus.

Serious escaped defects are never merely closed. They become permanent probes.

The initial corpus includes the PR #53 families for:

- traversal;
- protected control paths;
- path control characters;
- trailing separators;
- artifact-root escape;
- destination collision;
- raw/parsed divergence;
- verification external effects;
- handoff lineage;
- verification-specific authorization;
- working-directory binding.

## 8. MOPCON projection contract

The first MOPCON integration should remain read-only.

MOPCON may display:

- repository;
- exact head/base;
- deterministic verdict;
- P1/P2/P3 counts;
- checks run;
- Oracle availability;
- Oracle additional-risk synthesis;
- provenance state;
- next action required.

MOPCON must not infer authorization from a Thea pass.

Recommended operator labels:

- `HOLD`
- `CLEAR FOR INDEPENDENT REVIEW`
- `INDEPENDENT REVIEW PENDING`
- `CONSTITUTIONAL CONFIRMATION PENDING`
- `OPERATOR DISPOSITION REQUIRED`

## 9. Next implementation slices

1. Bind Thea directly to Git/GitHub exact-head checkout and diff acquisition.
2. Add deterministic repository tree containment and symlink escape checks in an isolated checkout.
3. Add schema/state-machine fuzzing adapters.
4. Add AST-aware self-modification detection for validators, policy, CI, and review instructions.
5. Run the permanent corpus automatically against every correction head.
6. Add reviewer provenance ledger and finding lineage store.
7. Add read-only MOPCON projection.
8. Benchmark candidate local review models against the permanent corpus before designating a default Oracle model.

## 10. References

- NIST AI RMF 1.0 — NIST AI 100-1
- NIST AI RMF Generative AI Profile — NIST AI 600-1
- NIST SP 800-218 — Secure Software Development Framework v1.1 (final)
- NIST SP 800-218A — Secure Software Development Practices for Generative AI and Dual-Use Foundation Models (final)
- NIST SP 800-218 Rev. 1 — SSDF v1.2 (initial public draft, December 2025)
- NIST Cybersecurity Framework 2.0
- GitHub Copilot Code Review documentation (current market reference for automatic re-review, custom instructions, agent skills, MCP context, and advisory review semantics)
