# AGENTS.md

> Operational contract for AI-assisted Nexus work.
>
> Read this before non-trivial implementation or review.
> Detailed rationale lives under `docs/nexus/`.

## 1. Current architecture

Current direction: ADR-0002.

> AROS remains the primary system runtime. Nexus becomes the small privileged executive beneath it.

Do not create, without a superseding ADR:

- a parallel OS;
- mandatory ExecNG ecosystem;
- mandatory whole-AROS Legacy Cell;
- fork-only m68k replacement stack.

Read when relevant:

- `docs/nexus/ARCHITECTURE.md`
- `docs/nexus/ROADMAP.md`
- `docs/nexus/REVIEW_PROTOCOL.md`
- `docs/nexus/VERIFICATION_MODEL.md`

## 2. Upstream first

Before touching a subsystem:

1. inspect current `aros-development-team/AROS:master`;
2. compare with the tested baseline;
3. identify relevant upstream changes;
4. integrate or account for them before local implementation.

Repeat before merge.

Fork `master` tracks upstream only.

Do not put Nexus implementation on `master`.

## 3. Tracking head != tested baseline

- tracking head = latest upstream state monitored;
- tested baseline = upstream commit with recorded build/boot evidence.

Do not move `BASELINE.md` just because upstream moved.

## 4. U / A / N ownership

Classify every significant touched area:

- **U** — upstream-owned;
- **A** — adapted through the smallest useful Nexus seam;
- **N** — Nexus-owned.

Too much A-class code is a warning.

For A-class work record why the seam exists and how it could later be removed.

## 5. Trust ratchet

For machine authority record:

1. legacy-owned;
2. shared/adapted;
3. Nexus-owned for the protected mode.

Relevant authority includes:

- CR3/page tables;
- privilege;
- IDT/APIC/interrupt control;
- physical memory;
- PCI/MMIO;
- DMA/IOMMU;
- device ownership.

Do not reintroduce a legacy bypass after protected ownership reaches Nexus.

## 6. Bridgeability

Before crossing a protection boundary classify:

- **B0** — direct-only legacy;
- **B1** — generated value/handle bridge;
- **B2** — explicit manual bridge;
- **B3** — protected-native contract.

Never blindly serialize:

- raw pointers;
- pointer-to-pointer arguments;
- Hooks/callbacks;
- physical addresses;
- implicit shared lifetime.

Generators fail closed on unknown unsafe types.

## 7. Work unit

A non-trivial issue normally has:

- one focused feature branch;
- one logical scope;
- one logical integrator.

Multiple agents may contribute analysis, code, tests or review.

One integrator owns final coherence.

## 8. Acceptance criteria first

Before implementation define:

- goal;
- non-goals;
- preconditions;
- U/A/N ownership;
- B0-B3 if relevant;
- acceptance criteria;
- negative/red-team criteria;
- required automated evidence;
- required human/hardware evidence;
- affected L0-L5 claim;
- stop conditions.

If the task cannot be falsified, refine it before coding.

## 9. Three reviews

### Review 1 — Construction

Check:

- correctness;
- scope;
- ownership/lifetime;
- error paths;
- unnecessary complexity.

### Review 2 — Integration

Check:

- regressions;
- ABI;
- SMP/concurrency;
- portability;
- latest upstream;
- U/A/N impact;
- affected test/build paths.

### Review 3 — Evidence Red Team

Assume the change is wrong.

Try to falsify it with:

- negative/regression test;
- malformed input;
- fault injection;
- race/stress test;
- invalid capability;
- permission violation;
- stale handle;
- TLB/IRQ/DMA scenario;
- direct/isolated conformance failure.

Rule:

> **NO TEST, EXPLAIN WHY.**

If an executable adversarial test is not possible, document why, the strongest concrete failure scenario, current evidence and what prerequisite would make the test possible.

AI agreement alone is not evidence.

## 10. Evidence hierarchy

Confidence roughly increases through:

- E0 reasoning;
- E1 static/mechanical validation;
- E2 focused executable test;
- E3 integration/regression;
- E4 deterministic QEMU;
- E5 cross-architecture;
- E6 physical hardware;
- E7 independent expert review.

More agents do not automatically raise the evidence level.

## 11. Human/hardware gates

### H0 — machine-verifiable

Typical docs/tooling/simple non-critical generators.

### H1 — human technical review required

Required for:

- kernel;
- scheduler;
- MMU;
- fault handling;
- privilege;
- capability/IPC authority;
- ABI/protection boundary.

AI may implement/review, but AI-only acceptance is insufficient.

### H2 — physical-hardware evidence required

Required for material claims involving:

- IOMMU/DMA;
- PCIe/NVMe;
- interrupt remapping;
- firmware/UEFI/chipset;
- USB/xHCI;
- GPU;
- power/resume.

### H3 — independent expert review

Required before strong release-level L2-L5 security/isolation claims.

## 12. Isolation claims

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

## 13. Hardware stop

If QEMU cannot establish the required property:

1. stop dependent work;
2. prepare exact commit/artifact;
3. document hardware;
4. document procedure;
5. document expected result;
6. document risk/recovery;
7. wait for real evidence.

Independent work may continue only if it does not assume the blocked result.

## 14. m68k

Primary compatibility path: upstream `rom/m68kemu`.

Do not build a competing fork-only translator without strong evidence and a dedicated ADR.

Compatibility is not security containment.

## 15. AI scope

AI/LLM is a future optional service consumer, not part of the Nexus kernel TCB.

Do not block Phase 0-5 on AI.

General foundations may include:

- async messaging;
- capabilities;
- MemoryObjects;
- service discovery;
- structured automation;
- future compute abstraction.

## 16. Branch / PR discipline

For non-trivial implementation:

- branch from current `nexus/main`;
- keep one logical change;
- document Review 1/2/3;
- rerun upstream check before merge;
- require relevant checks green;
- satisfy H1/H2/H3 when applicable.

Squash intermediate corrective commits when they add no historical value.

## 17. Upstream contribution

Current upstream AROS `CONTRIBUTING.md` has no explicit blanket AI ban.

Do not assume that remains true.

Before significant Nexus-originated upstream work:

- re-read current policy;
- discuss changes with the AROS team when requested;
- ask what AI-assistance disclosure they expect;
- disclose assistance honestly where relevant;
- keep human responsibility for code, tests, licensing and provenance.

## 18. Pace

A productive cycle may end with:

- analysis;
- failing test;
- rejected idea;
- documentation;
- upstream integration;
- reduced scope;
- hardware stop;
- no commit.

Reduced uncertainty is progress.

## 19. First protection milestone

N1 should eventually demonstrate with executable evidence:

- distinct CR3/address spaces;
- private mappings blocked cross-domain;
- explicit shared MemoryObject works;
- NX fault is real;
- supervisor write protection is real where required;
- protected fault is contained;
- repeated safe context switches.

Do not declare N1 from code inspection.
