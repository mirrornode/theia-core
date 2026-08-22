# Thea v0.1 — Full Internal Review

**Review date:** 2026-08-22  
**Repository:** `mirrornode/theia-core`  
**PR:** #1  
**Review posture:** internal implementation review; not independent constitutional closure  
**Authority effect:** `NONE`

## Review question

Does Thea v0.1 actually enforce the claims made by its architecture documentation, and does it preserve the PR #53 lessons rather than reproducing them inside the verifier itself?

## Disposition

**HOLD FOR PROPOSAL REVIEW / NOT MERGE-CLEARED.**

The deterministic kernel is useful and its current unit workflow has demonstrated executable coverage, but v0.1 remains a supplied-manifest verifier rather than an observed exact-head checkout verifier. Several review findings were corrected during this pass; three proof-depth limitations remain intentionally open and are now documented as such.

## Findings

### THEA-R1 — P1 — Exact-head proof was overstated

**Original condition:** The kernel required 40-character head/base SHA strings and described that as exact-head identity.

**Problem:** string shape does not prove that the named repository contains those commits or that the reviewed checkout is actually at the supplied head.

**Correction:** check names and architecture documentation now describe this as immutable-identifier shape. `ReviewResult.claim_limit` is fixed to `SUPPLIED_MANIFEST_SEMANTICS_ONLY`.

**Remaining work:** observed local Git checkout binding must verify repository identity, exact HEAD, base existence, and diff acquisition before Thea itself may emit an `EXACT_HEAD_REVIEWED` claim.

**Status:** OPEN AS BOUNDED NEXT SLICE; overclaim corrected.

### THEA-R2 — P2 — Raw/parsed evidence proof was overstated

**Original condition:** two supplied path sets were compared and described as raw/parsed status reconciliation.

**Problem:** Thea did not parse a raw `git status --porcelain=v1 -z` capture. A producer could supply two mutually agreeing derived path lists that both diverged from the actual raw capture.

**Correction:** implementation and documentation now call this `status-path-set-agreement` and state the claim limit explicitly.

**Remaining work:** parse the raw capture inside the trusted verifier boundary and structurally compare the derived records.

**Status:** OPEN AS BOUNDED NEXT SLICE; overclaim corrected.

### THEA-R3 — P2 — File-operation vocabulary was unbounded

**Original condition:** any operation string other than the special MOVE/RENAME paths could pass through as a normal write operation.

**Counterexample:** `operation: "FLY"` could reach a finding-free supplied manifest.

**Correction:** bounded vocabulary enforced: `CREATE`, `MODIFY`, `DELETE`, `MOVE`, `RENAME`, `RESTORE`. Unknown values fail closed with `THEA-OP-001`.

**Status:** FIXED; regression test added.

### THEA-R4 — P1 — Positive artifact root could overlap implementation write scope

**Original condition:** artifacts had to be positively contained under a declared root, but the root itself was not checked against implementation write targets.

**Counterexample:** implementation writes `src/a.py`; verification root `src`; verification artifact `src/thea/report.json`.

**Problem:** this reintroduced the PR #53 inverse-privilege family in a subtler form: the artifact root was positive but not independent.

**Correction:** the artifact root is now checked bidirectionally against every normalized implementation write target, and exact artifact/write-target collisions also fail closed.

**Status:** FIXED; regression test added.

### THEA-R5 — P2 — Manifest boolean coercion changed authorization meaning

**Original condition:** `verification_authorized=bool(value)` used Python truthiness.

**Counterexample:** JSON/string-like input `"false"` becomes Python `True`.

**Correction:** strict manifest parser now requires actual booleans, arrays of non-empty strings, non-empty required strings, and structured operation objects.

**Status:** FIXED; regression test added.

### THEA-R6 — P2 — Oracle model endpoint could violate the local-only claim

**Original condition:** default endpoint was loopback, but `THEA_MODEL_ENDPOINT` could point anywhere.

**Problem:** documentation promised a locally owned model boundary while configuration allowed silent evidence egress to a remote endpoint.

**Correction:** v0.1 refuses non-loopback hosts, embedded URL credentials, invalid timeout ranges, malformed output, and oversized model responses. There remains no cloud fallback.

**Status:** FIXED.

### THEA-R7 — P2 — Handoff lineage is presence-only

**Current condition:** handoff changes require `handoff_authorized_scope_digest` to be present.

**Problem:** v0.1 does not recompute that digest, carry an authoritative scope snapshot, or prove each handoff path was authorized.

**Correction in this pass:** documentation no longer calls the current check full handoff-lineage verification.

**Remaining work:** cryptographic scope recomputation plus changed-path reconciliation.

**Status:** OPEN AS BOUNDED NEXT SLICE.

### THEA-R8 — REVIEW-HARNESS — Harness error precedence

**Original condition:** an unexpected validator exception could lead to `INVALID_RUN_NO_ACCEPT_BASELINE` because the exception prevented the baseline from being recorded.

**Problem:** the most important fact was harness integrity failure, not absence of a valid baseline.

**Correction:** `INVALID_RUN_HARNESS_ERROR` now takes precedence over scoreability/baseline conditions.

**Status:** FIXED; failed run retained in lineage.

### THEA-R9 — BASELINE — Pre-existing Canon Gate mismatch

**Condition:** the repository's existing Canon Gate requires `REPO_MAP.md`, but `theia-core` currently lacks that file.

**Scope:** this is not caused by Thea v0.1 and was not corrected by fabricating a file or weakening the gate.

**Status:** OPEN REPOSITORY-BASELINE DISPOSITION.

## What v0.1 can honestly claim

A finding-free Thea v0.1 manifest run may claim:

- strict input shape accepted;
- supplied immutable identifiers have valid full-SHA form;
- supplied paths satisfy Thea's current denotation rules;
- supplied operation classes are bounded;
- supplied verification artifacts are positively contained and separated from supplied implementation write targets;
- supplied verification/effect/lineage fields satisfy current semantic checks;
- executed probe families behaved as reported.

It may **not** claim solely from that result:

- the repository was actually observed at the supplied head;
- the supplied changed-file list equals the real Git diff;
- a raw Git status capture agrees with its parsed representation;
- a handoff scope digest is authentic or complete;
- independent review occurred;
- constitutional clearance;
- merge or runtime authorization.

## Recommended next order

1. Finish current exact-head CI after these review corrections.
2. Add observed local checkout binding.
3. Add raw Git-status parser/reconciliation.
4. Add cryptographic handoff-scope recomputation.
5. Re-run the permanent corpus and this review against the resulting exact head.
6. Only then consider Thea v0.1 ready for an independent reviewer and MOPCON read-only integration.

## Review conclusion

Thea is already useful because its first serious review produced defects in **Thea itself**, and those defects were observable, recorded, and converted into stronger semantics. That is evidence that the review-memory architecture is functioning in the intended direction.

The correct conclusion is not that Thea is finished. It is that the verifier has crossed the threshold from an architectural idea into an auditable engineering surface whose own claims can now be attacked precisely.
