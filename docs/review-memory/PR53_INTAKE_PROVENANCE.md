# PR #53 Adversarial Review Intake Provenance

**Intake date:** 2026-08-22  
**Package name:** `mirrornode-adversarial-review`  
**Contributing lane:** Perplexity correction-lane agent  
**Authority effect:** NONE

## Package received

The intake package contained:

- `SKILL.md` — twenty review rules, nine-step workflow, bounded claim ladder, correction-pass protocol, confidence-withdrawal protocol.
- `references/pr53-case-study.md` — failure history and exact counterexamples from PR #53.
- `references/review-lenses.md` — eight orthogonal lenses and their blind spots.
- `references/probe-corpus.md` — sixteen earned probe families plus generic probes.
- `references/language-traps.md` — ambiguous terms whose ordinary meanings are unsafe in authority-bearing review.
- `scripts/path_denotation.py` — positive repository-path containment and canonical identity checks.
- `scripts/probe_harness.py` — refusal-first probe harness with legitimate accept baselines and strict exception classification.

## Intake validation

The package was executed before incorporation.

`path_denotation.py`:

- refused the seven path examples that escaped PR #53 head `05d83494527a7318139d5255dd75fb4ff740600c`;
- refused generic absolute, home-relative, drive-letter, alias, empty-segment, control-character, whitespace, and over-length cases;
- accepted legitimate Unicode and ordinary repository-relative paths;
- demonstrated segment-aware positive containment: `buildother/x.log` is not contained by root `build`.

`probe_harness.py`:

- reproduced nine holes against its intentionally vulnerable validator;
- refused all nine against the hardened positive-containment validator;
- required legitimate accept probes before permitting a clean result;
- refused to score unexpected exceptions as security refusals;
- emitted only `ADVERSARIAL_PROBES_PASS` for the declared families and explicitly denied higher-order clearance implications.

## Provenance correction retained

The decisive PR #53 review was a correction-lane self-review, not independent closure. Its technical findings are retained; its independence claim is not. Future review artifacts must state this relationship directly.

## Incorporation into Thea

The package is not maintained as a second competing verifier.

Thea absorbed:

- the stronger denotational rules into `thea/path_policy.py`;
- refusal-first harness semantics into `thea/probe_harness.py`;
- permanent regression cases into the Thea test/corpus surface;
- the twenty-rule doctrine, workflow, claim ladder, lineage and correction rules into `MIRRORNODE_ADVERSARIAL_REVIEW_V1.md`.

The source package remains historical evidence for this derivation. Thea's executable implementation is the maintained verifier surface.
