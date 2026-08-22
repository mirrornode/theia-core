# MIRRORNODE Adversarial Review v1

**Origin:** PR #53 specialized terminal-agent phase gating, 22 August 2026  
**Status:** review-memory proposal carried inside Thea; not canon  
**Authority effect:** NONE

## Core doctrine

A safe agentic system must govern not only actions, but the interpretation of the evidence used to authorize those actions. A string, digest, passing test, reviewer statement, green CI run, or council position is evidence. None of them becomes authority merely because it exists. Meaning depends on provenance, identity, context, scope, timing, denotation, independence, and the authority that consumes it.

## Twenty rules

1. Bind every review to an immutable exact head.
2. Separate validation from authorization.
3. Separate technical usefulness from reviewer independence.
4. Treat passing tests as evidence, never completeness.
5. Attack primitives beneath higher-order guarantees.
6. Normalize resource identities before comparing or authorizing them.
7. Prefer positive containment over purely negative exclusion.
8. Treat every correction as a new attack surface.
9. Keep implementation corrections bounded while widening verification around changed invariants.
10. Maintain permanent adversarial regression probes from every escaped defect.
11. Explicitly inspect self-modification and gate-modification paths.
12. Reconcile machine interpretation with human-visible evidence.
13. Preserve finding lineage across heads.
14. Never flatten `reviewed` into a single state.
15. Do not make external model quota a constitutional dependency.
16. Build and own an internal verification lane.
17. Give new reviewers failure history, not merely role descriptions.
18. Treat ambiguous multidimensional language as an engineering surface.
19. Require orthogonal review lenses rather than duplicate opinions.
20. Design for recoverable error, not imaginary infallibility.

## Review workflow

### 1. Establish review identity before reading code

Record repository, exact head, exact base, changed-file list and diff at that head, prior findings by head, and reviewer provenance. A correction author may produce valuable self-review but cannot supply independent closure.

### 2. Select orthogonal lenses

Use structural/schema, semantic-invariant, denotational/resource, authorization-lifecycle, adversarial state-transition, provenance, human-audit divergence, and self-modification lenses. Denotational and self-modification review are mandatory for authority-bearing scope changes.

### 3. Attack denotation

Ask both: do records contain the same representation, and do those representations identify the resource they claim to identify? When many guarantees depend on one primitive, attack the primitive.

### 4. Hunt inverse privilege surfaces

For every `not X` rule, enumerate the complement. Replace negative exclusion with positive containment wherever authority is at stake.

### 5. Run and extend the probe corpus

For every probe family, execute it or mark it not applicable with a reason. Security probes assert refusal; acceptance is a hole. Always include legitimate accept baselines so a validator that refuses everything cannot report clean.

### 6. Emit bounded claims

No lower claim implies a higher claim:

`SCHEMA_VALID` → `SEMANTIC_VALID` → `TEST_SUITE_PASS` → `ADVERSARIAL_PROBES_PASS` → `EXACT_HEAD_REVIEWED` → `INDEPENDENT_EXACT_HEAD_REVIEWED` → `CONSTITUTIONALLY_CLEARED` → `MERGE_AUTHORIZED`.

### 7. Preserve finding lineage

Record `finding → target head → correction → correction head → re-probe → disposition`. Disposition distinguishes closed, superseded, transformed, regressed, still applicable, and non-applicable due to architecture change.

### 8. Dispose and stop

Use `HOLD`, `CLEAR-WITH-CONDITIONS`, or `CLEAR FOR OPERATOR DISPOSITION`. A live P1 forces HOLD. Stop before merge, approval, canon promotion, deployment, runtime execution, or cosmetic thread resolution.

### 9. Feed the corpus back

Every escaped defect becomes a permanent regression probe. Once learned, the mistake should become cheap forever.

## Correction-pass protocol

Implementation scope stays narrow; verification scope widens around the changed invariant. A correction must be attacked for newly created authority surfaces, inverse privileges, denotational gaps, and self-modification paths. Discovering a new live P1 outside the authorized correction scope stops implementation and returns to Operator disposition.

## Confidence withdrawal

When later evidence invalidates an earlier confidence claim, the earlier claim is not silently rewritten. Record the original evidence, the overstated inference, the new counterexample, and the withdrawn implication. PR #53's `47/47 passing` result remained true as a test-suite fact while its implied adversarial completeness was explicitly withdrawn.

## PR #53 retained scars

The review memory must permanently retain these families: path traversal; normalized aliases; protected `.git`/`.github` targets; artifact-root escape; validator/CI self-modification; duplicate MOVE destinations; destination/source collisions; raw-versus-parsed evidence divergence; verification external effects; verification-specific authorization; handoff authorization lineage; working-directory binding; authorization revocation/supersession/expiry; and positive legitimate baselines.

## Provenance note

The decisive adversarial pass at PR #53 head `05d83494527a7318139d5255dd75fb4ff740600c` was performed by the correction-lane agent against its own correction. It was technically valuable but not independent closure. The original title `Independent Adversarial Review` overstated provenance; future artifacts should name self-review plainly.
