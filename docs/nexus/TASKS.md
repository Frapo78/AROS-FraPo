# Nexus Tasks

GitHub Issues are the source of truth for task-level progress. This file is the high-level phase index.

## Phase 0 — Baseline and guardrails

Parent: #1

### P0.1 — x86-64 boot map
Status: **draft complete / source review ongoing**
Issue: #2

Deliverable: `docs/nexus/X86_64_BOOT_MAP.md`

### P0.2 — Reproducible QEMU baseline
Status: **todo**
Issue: #3

### P0.3 — Privileged-operation inventory
Status: **todo**
Issue: #4

### P0.4 — Regression/test inventory
Status: **todo**
Issue: #5

### P0.5 — Baseline diagnostics
Status: **todo**
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
Status: **design documented / source audit pending**
Issue: #14

Document:
- `ADDRESS_SPACE_MODEL.md`

### P0.9 — Nexus CI and QEMU implementation gate
Status: **todo**
Issue: #15

## Phase 1 preparation

### P1.1 — Internal NexusAddressSpace abstraction
Status: **blocked by Phase 0 gates**
Issue: #7

Scope: AS0/AS1 only — explicit representation and target ownership with no intended AROS semantic change.

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
