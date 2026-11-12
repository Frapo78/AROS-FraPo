# ARBM Tasks

GitHub Issues are the source of truth for task-level progress. This file is the high-level phase index.

## Architecture refinement

### ADR-0002 — Convergent AROS / ARBM architecture
Status: **accepted architectural direction (ADR-0002); PR #19 is historical, not a pending integration gate**
Issue: #18

Core documents:
- `adr/0002-convergent-aros-nexus-architecture.md`
- `CONVERGENT_ARCHITECTURE.md`
- `UPSTREAM_INTEGRATION.md`
- `AI_FOUNDATIONS.md`

The direction remains intentionally revisable through future ADRs when evidence justifies it.

## Phase 0 — Convergence baseline and guardrails

Parent: #1

### P0.1 — x86-64 boot map
Status: **draft complete / source review ongoing**
Issue: #2

Deliverable: `docs/nexus/X86_64_BOOT_MAP.md`

### P0.2 — Reproducible QEMU baseline
Status: **G1 reference build evidence recorded on PR #24; current main-line baseline and full desktop gate not promoted**
Issue: #3

### P0.3 — Privileged-operation inventory
Status: **partial source/privilege inventory; verification remains open**
Issue: #4

### P0.4 — Regression/test inventory
Status: **partial upstream m68k/SMP inventory documented in `REGRESSION_MATRIX_P04.md`; named host and guest suites not executed for that checkpoint**
Issue: #5

### P0.5 — Baseline diagnostics
Status: **early serial diagnostics observed on PR #24; full boot diagnostics not accepted**
Issue: #6

### P0.6 — Trust, fault and legacy privilege validation
Status: **architecture documented / source audit pending**
Issue: #12

Documents:
- `TRUST_MODEL.md`
- `LEGACY_PRIVILEGE_MODEL.md`

### P0.7 — kernel.resource / Exec coupling inventory
Status: **architecture documented / source inventory pending**
Issue: #13

Document:
- `NEXUS_EXEC_SPLIT.md`

### P0.8 — x86-64 NX/W^X/MMU/TLB audit
Status: **source audit in progress; findings remain valid under ADR-0002**
Issue: #14

Document:
- `ADDRESS_SPACE_MODEL.md`

### P0.9 — ARBM CI and QEMU implementation gate
Status: **G0 active; PR #24 has recorded G1 and G2a early-marker success on its pinned commit; G2b/G2c full Wanderer proof still open; PR #24 not merged**
Issue: #15

### P0.10 — Evidence-driven agent engineering
Status: **controls defined and present on `nexus/main`; PR #23 is historical**
Issue: #22

Core controls:
- root `AGENTS.md`;
- `VERIFICATION_MODEL.md`;
- Evidence Red Team with **NO TEST, EXPLAIN WHY**;
- H0-H3 human/hardware gates;
- falsifiable task templates.

## Phase 0 code and tooling checkpoint (2026-11-01)

- **Merged:** PR #34, `cf6a26fe0ea76e5d86536bbe6052fc64ff65ca99`: ARBM-owned **standalone host C** mapping-rights validator and negative NX input tests. The host CI passed. No AROS MMU/page-table integration, kernel ABI change or isolation claim.
- **Open:** PR #24: resource-aware G1/G2a QEMU harness; recorded successful early serial marker, not a verified Wanderer desktop.
- **Open:** PR #35: G2c desktop evidence capture and adversarial host tests, cleanly based on main; CI passed, but no real guest Wanderer interaction proof. Replaces closed PR #30.
- **Closed as superseded:** PRs #27/#28 (obsolete upstream candidate), #29/#33 (superseded by merged #34), #30 (superseded by #35).
- **Evidence boundary:** E2 host-only for #34 and #35; historical E4 early-boot G2a on #24. No completed Phase 0 exit, no Phase 1 implementation, no L0-L5 protection claim.

## Phase 1 preparation

### P1.1 — Internal ARBMAddressSpace abstraction
Status: **blocked by Phase 0 gates**
Issue: #7

Scope: AS0/AS1 only — extract explicit AddressSpace representation beneath the normal AROS runtime, with no intended AROS semantic change and no mandatory Legacy Cell migration.

### P1 fault precondition — domain-aware fault classification
Status: **blocked by P1.1 and Phase 0 audit**
Issue: #16

### P1.2 — Second protected x86-64 address space
Status: **blocked by #7, #14, #15 and #16**
Issue: #8

Target proof: L1 CPU memory isolation.

### P1.3 — Protected IPC + shared MemoryObject proof
Status: **blocked by P1.2**
Issue: #9

## Recorded baseline

See `BASELINE.md`.

Current implementation baseline:

`aros-development-team/AROS master @ 2edd46536d08e3b54ecd1315f337a9b7de896f3a`

## Tracking rule

Do not mark a protection milestone complete using the unqualified word "isolated".

Record the highest isolation level actually demonstrated:

- L0 compatibility containment
- L1 CPU memory isolation
- L2 privilege isolation
- L3 hardware isolation
- L4 DMA isolation
- L5 service fault isolation
