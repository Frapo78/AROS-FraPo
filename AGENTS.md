# AGENTS.md

> Operational contract for AI-assisted Nexus work.
> Detailed rationale lives under `docs/nexus/`.

## Current direction

ADR-0002 is current.

> AROS remains the primary runtime. Nexus becomes the small privileged executive beneath it.

Without a superseding ADR, do not create:
- a parallel OS;
- mandatory ExecNG;
- mandatory whole-AROS Legacy Cell;
- fork-only m68k replacement stack.

Read when relevant:
- `docs/nexus/ARCHITECTURE.md`
- `docs/nexus/ROADMAP.md`
- `docs/nexus/REVIEW_PROTOCOL.md`
- `docs/nexus/VERIFICATION_MODEL.md`

## Upstream first

Before touching a subsystem:
1. inspect current `aros-development-team/AROS:master`;
2. compare with the tested baseline;
3. identify relevant upstream commits;
4. integrate/account for them before local implementation.

Repeat before merge.

Fork `master` tracks upstream only. Never put Nexus implementation on `master`.

## Tracking head != tested baseline

- tracking head = latest upstream state monitored;
- tested baseline = upstream commit with recorded build/boot evidence.

Do not move `BASELINE.md` just because upstream moved.

## U / A / N

Classify each significant area:
- **U** — upstream-owned;
- **A** — adapted through the smallest Nexus seam;
- **N** — Nexus-owned.

Too much A-class code is a warning. For A-class work record why the seam exists and how it could later disappear.

## Trust ratchet

For machine authority record:
1. legacy-owned;
2. shared/adapted;
3. Nexus-owned for the protected mode.

Applies to CR3/page tables, privilege, IDT/APIC/interrupts, physical memory, PCI/MMIO, DMA/IOMMU and device ownership.

Do not reintroduce a legacy bypass after protected ownership reaches Nexus.

## Bridgeability

Before crossing a protection boundary classify:
- **B0** — direct-only legacy;
- **B1** — generated value/handle bridge;
- **B2** — explicit manual bridge;
- **B3** — protected-native contract.

Never blindly serialize raw pointers, pointer-to-pointer arguments, Hooks/callbacks, physical addresses or implicit shared lifetime. Generators fail closed on unknown unsafe types.

## Work unit

A non-trivial issue normally has:
- one focused feature branch;
- one logical scope;
- one logical integrator.

Multiple agents may contribute. One integrator owns final coherence.

## Acceptance criteria first

Before implementation define:
- goal and non-goals;
- preconditions;
- U/A/N and B0-B3 when relevant;
- acceptance criteria;
- negative/red-team criteria;
- required automated evidence;
- required human/hardware evidence;
- affected L0-L5 claim;
- stop conditions.

If the task cannot be falsified, refine it before coding.

## Three reviews

### Review 1 — Construction
Check correctness, scope, ownership/lifetime, error paths and unnecessary complexity.

### Review 2 — Integration
Check regressions, ABI, SMP/concurrency, portability, latest upstream, U/A/N impact and affected test/build paths.

### Review 3 — Evidence Red Team
Assume the change is wrong. Try to falsify it with a negative/regression test, malformed input, fault injection, race/stress test, invalid capability, permission violation, stale handle, TLB/IRQ/DMA scenario or conformance failure.

> **NO TEST, EXPLAIN WHY.**

If no executable adversarial test is possible, document:
- why;
- strongest concrete failure scenario;
- current evidence;
- prerequisite for a future executable test.

AI agreement alone is not evidence.

## Evidence levels

- E0 — reasoning;
- E1 — static/mechanical validation;
- E2 — focused executable test;
- E3 — integration/regression;
- E4 — deterministic QEMU;
- E5 — cross-architecture;
- E6 — physical hardware;
- E7 — independent expert review.

More agents do not automatically raise evidence level.

## QEMU budget

QEMU is evidence, not a default background expense.

Rules:
- no automatic QEMU on every push;
- no scheduled/nightly matrix by default;
- normal PR QEMU runs only at selected lifecycle points for relevant x86-64/kernel/build paths;
- rerun after later commits only when required, using explicit manual dispatch;
- one vCPU/reference configuration before any matrix;
- cancel obsolete runs for the same PR/ref;
- use hard workflow and guest-marker timeouts;
- upload short-lived logs/manifests, not the ISO by default;
- expand the QEMU matrix only when a specific falsifiable claim requires it.

A QEMU marker proves only that named checkpoint. It does not imply Wanderer, SMP, isolation, DMA or real-hardware correctness.

## Human/hardware gates

### H0 — machine-verifiable
Typical docs/tooling/simple non-critical generators.

### H1 — human technical review
Required for kernel, scheduler, MMU, fault handling, privilege, capability/IPC authority and ABI/protection-boundary changes.

AI may implement/review; AI-only acceptance is insufficient.

### H2 — physical hardware
Required for material claims involving IOMMU/DMA, PCIe/NVMe, interrupt remapping, firmware/UEFI/chipset, USB/xHCI, GPU or power/resume.

### H3 — independent expert
Required before strong release-level L2-L5 security/isolation claims.

## Isolation claims

Use only the highest demonstrated level:
- L0 — compatibility-domain classification/containment;
- L1 — CPU memory isolation;
- L2 — privilege isolation;
- L3 — hardware/MMIO/IRQ isolation;
- L4 — DMA isolation;
- L5 — service fault isolation.

No L1-L5 claim is accepted on AI review alone.

Never infer:
- different address space => hardware isolation;
- MMU isolation => DMA isolation;
- m68k contained memory => Nexus sandbox;
- process boundary => restartability.

## Hardware stop

If QEMU cannot establish the required property:
1. stop dependent work;
2. prepare exact commit/artifact;
3. document hardware, procedure, expected result and recovery/risk;
4. wait for real evidence.

Independent work may continue only if it does not assume the blocked result.

## m68k

Primary compatibility path: upstream `rom/m68kemu`.

Do not build a competing fork-only translator without strong evidence and a dedicated ADR. Compatibility is not security containment.

## AI scope

AI/LLM is a future optional service consumer, not part of the Nexus kernel TCB.

Do not block Phase 0-5 on AI. General foundations may include async messaging, capabilities, MemoryObjects, service discovery, structured automation and future compute abstraction.

## Branch / PR discipline

For non-trivial implementation:
- branch from current `nexus/main`;
- keep one logical change;
- document Review 1/2/3;
- rerun upstream check before merge;
- require relevant checks green;
- satisfy H1/H2/H3 when applicable.

Squash corrective commits when they add no historical value.

## Upstream contribution

Current upstream AROS `CONTRIBUTING.md` has no explicit blanket AI ban. Do not assume that remains true.

Before significant Nexus-originated upstream work:
- re-read current policy;
- discuss changes with the AROS team when requested;
- ask what AI-assistance disclosure they expect;
- disclose assistance honestly where relevant;
- keep human responsibility for code, tests, licensing and provenance.

## Pace

A productive cycle may end with analysis, a failing test, rejected idea, documentation, upstream integration, reduced scope, hardware stop or no commit.

Reduced uncertainty is progress.

## First protection milestone

N1 should eventually demonstrate with executable evidence:
- distinct CR3/address spaces;
- private mappings blocked cross-domain;
- explicit shared MemoryObject works;
- NX fault is real;
- supervisor write protection is real where required;
- protected fault is contained;
- repeated safe context switches.

Do not declare N1 from code inspection.
