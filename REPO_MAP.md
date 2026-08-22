# theia-core Repository Map

**Updated:** 2026-08-22  
**Status:** descriptive repository map; not a runtime registry, port registry, governance grant, or deployment record

## Purpose

This file satisfies the repository's pre-existing Canon Gate requirement that a repository map be present. It describes the surfaces that actually exist in `mirrornode/theia-core` and does not import historical MIRRORNODE node/port authority into this repository.

## Current top-level surfaces

| Surface | Role | Current interpretation |
| --- | --- | --- |
| `SYSTEM_CONTRACT.md` | inherited historical contract | preserved evidence; not sufficient by itself to define current MIRRORNODE-wide runtime authority |
| `AGENTS_TODO.md` | inherited agent/task record | historical/working record; not a current constitutional registry |
| `api/` | pre-existing API surface | legacy/core implementation surface; review before treating as current authority |
| `khepri/` | pre-existing Khepri surface | inherited implementation surface |
| `models/` | pre-existing model definitions | inherited implementation surface |
| `scripts/` | repository tooling including Canon Gate | enforcement/tooling surface |
| `docs/` | architecture and review documentation | descriptive/proposal documentation unless separately promoted |
| `thea/` | Thea verifier v0.1 proposal | deterministic supplied-manifest verification plus optional local Oracle interpretation; authority effect `NONE` |
| `tests/` | Thea deterministic tests | verification evidence, not merge or governance authority |
| `.github/workflows/` | repository validation | CI evidence only; workflow success is not authorization |
| `server.js` / `package.json` | pre-existing JavaScript service surface | inherited service entry surface; separate from the new Python Thea verifier service |

## Thea verifier boundary

The `thea/` package is intentionally non-authoritative. Its current v0.1 proof surface is limited to supplied-manifest semantics and deterministic adversarial checks. It does **not** by itself establish:

- an observed Git checkout at the claimed SHA;
- independent exact-head review;
- Council or constitutional clearance;
- merge authorization;
- deployment or runtime authority.

`thea/service.py` binds only to loopback and requires an explicitly selected local port. No canonical port is registered by this repository map.

Oracle is an interpretive layer above Thea's deterministic result. It may add risks or missing probes but cannot erase deterministic blockers or create authority.

## Source-of-truth rule

This map describes repository topology only. MIRRORNODE-wide governance, current runtime state, canonical decisions, and Operator authorization must be resolved from their owning records and current evidence. When this map conflicts with a newer ratified MIRRORNODE record, the owning ratified record controls; the conflict should be recorded rather than silently reinterpreted.
