# AGENTS.md

> Operational contract for AI-assisted Nexus work.
>
> This file is intentionally short. It does not replace the architecture documents.

## 1. Current direction

Read these before non-trivial work:

- `docs/nexus/adr/0002-convergent-aros-nexus-architecture.md`
- `docs/nexus/ARCHITECTURE.md`
- `docs/nexus/ROADMAP.md`
- `docs/nexus/REVIEW_PROTOCOL.md`
- `docs/nexus/VERIFICATION_MODEL.md`

Current architecture:

> AROS remains the primary system runtime. Nexus becomes the small privileged executive beneath it.

Do not create a parallel OS, mandatory ExecNG ecosystem, mandatory whole-AROS Legacy Cell, or fork-specific m68k replacement without a superseding ADR.

## 2. Upstream first

Before touching a subsystem:

1. inspect current `aros-development-team/AROS:master`;
2. compare it with the recorded tested baseline;
3. identify relevant upstream commits;
4. integrate or account for them before implementing a competing local solution.

Before merge, repeat the upstream check.

`master` in this fork tracks upstream only.

Do not put Nexus implementation commits on `master`.

## 3. Tested baseline is not upstream head

Two concepts are distinct:

- **tracking head** — latest upstream state being monitored;
- **tested baseline** — upstream commit with recorded build/boot evidence.

Do not advance `docs/nexus/BASELINE.md` merely because `master` advanced.

## 4. U / A / N ownership

Classify every significant touched area:

- **U — upstream-owned:** keep almost unchanged;
- **A — adapted:** smallest possible Nexus seam;
- **N — Nexus-owned:** new Nexus substrate/tooling.

Too much A-class code is a warning.

For A-class code record:

- why the seam exists;
- why U-class is insufficient;
- how the seam could later be removed.

## 5. Trust ratchet

For machine authority, record the current state:

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

Once a protected mode reaches Nexus-owned authority, do not silently add a legacy bypass.

## 6. Bridgeability

Before crossing a protection boundary, classify the interface:

- **B0** — direct-only legacy;
- **B1** — generated value/handle bridge;
- **B2** — explicit manual bridge;
- **B3** — protected-native contract.

Never automatically serialize unknown raw pointers, pointer-to-pointer arguments, Hooks/callbacks, physical addresses or implicit shared lifetime.

Generators must fail closed on unknown unsafe types.

## 7. Work unit

One non-trivial issue should normally have:

- one focused feature branch;
- one logical scope;
- one integrator responsible for final coherence.

Multiple agents may contribute analysis/tests/review to the same branch.

Do not create several competing implementation branches for the same kernel seam unless the issue explicitly calls for an experiment comparison.

## 8. Acceptance criteria before implementation

A non-trivial issue must define:

- goal;
- non-goals;
- preconditions;
- U/A/N class;
- acceptance criteria;
- negative/red-team criteria;
- required automated evidence;
- required human evidence;
- required hardware evidence;
- affected L0-L5 claim, if any;
- stop conditions.

If the task cannot be falsified, refine the task before coding.

## 9. Three reviews

Every non-trivial code or architecture change requires three distinct passes.

### Review 1 — Construction

Check:

- correctness;
- scope;
- ownership/lifetime;
- error paths;
- API clarity;
- unnecessary complexity.

### Review 2 — Integration

Check:

- regressions;
- ABI;
- SMP/concurrency;
- portability;
- latest upstream;
- U/A/N impact;
- affected build/test paths.

### Review 3 — Evidence Red Team

Assume the change is wrong.

Try to produce external evidence that falsifies it:

- negative test;
- failing regression;
- malformed input;
- fault injection;
- race/stress test;
- invalid capability;
- permission violation;
- stale-handle test;
- TLB/IRQ/DMA scenario;
- direct/isolated conformance failure.

Rule:

> **NO TEST, EXPLAIN WHY.**

If an executable test cannot be produced, document why and provide the strongest concrete counterexample/failure scenario available.

An AI opinion alone is not red-team evidence.

## 10. Evidence hierarchy

Confidence increases roughly in this order:

1. agent reasoning/opinion;
2. static analysis;
3. unit/negative test;
4. integration/regression test;
5. deterministic QEMU test;
6. cross-architecture test;
7. real-hardware test;
8. independent competent human review.

More agents do not automatically increase evidence level.

Three agreeing models are weaker evidence than one reproducible failing test.

## 11. Human/hardware gates

### H0 — machine-verifiable

Typical:

- docs;
- project tooling;
- simple generators;
- non-critical tests.

CI + normal review may be sufficient.

### H1 — human review required before merge

Required for changes affecting:

- kernel;
- scheduler;
- MMU;
- fault handling;
- privilege;
- capability/IPC core;
- ABI/protection boundary.

AI may implement and review, but must not be the only basis for acceptance.

### H2 — real-hardware evidence required

Required when the claim materially depends on physical:

- IOMMU/DMA;
- PCIe/NVMe;
- interrupt remapping;
- firmware/UEFI/chipset;
- USB/xHCI;
- GPU;
- power/resume.

Stop dependent work until hardware evidence is recorded.

### H3 — independent expert review required for strong security claims

Before a release makes serious claims such as strong L2-L5 isolation/security, obtain competent independent review of the relevant invariants.

## 12. Isolation claims

Use only the highest level actually demonstrated:

- L0 — compatibility-domain classification/containment;
- L1 — CPU memory isolation;
- L2 — privilege isolation;
- L3 — hardware/MMIO/IRQ isolation;
- L4 — DMA isolation;
- L5 — service fault isolation.

Never infer:

- different address space => hardware isolation;
- MMU isolation => DMA isolation;
- m68k contained memory => Nexus sandbox;
- service process => restartable/contained;
- AI review => security proof.

No L1-L5 claim is accepted on AI review alone.

## 13. Hardware stop rule

If QEMU cannot establish the required property with sufficient confidence:

1. stop dependent implementation;
2. prepare exact commit/artifact;
3. document hardware required;
4. document test procedure;
5. document expected result;
6. document risk/recovery procedure;
7. wait for real evidence.

Independent work may continue only if it does not assume the blocked result.

## 14. m68k compatibility

Primary path is upstream `rom/m68kemu`.

Do not build a competing fork-only translator without strong evidence and a dedicated ADR.

Compatibility is not the same as security containment.

## 15. AI/LLM scope

AI is a future optional service consumer, not part of the Nexus kernel TCB.

Do not block Phase 0-5 work on AI.

Useful general foundations are:

- asynchronous messaging;
- capabilities;
- MemoryObjects;
- service discovery;
- structured automation;
- future compute abstraction.

## 16. Required branch/PR discipline

For non-trivial implementation:

- feature branch from current `nexus/main`;
- focused PR;
- one logical change;
- all required checks green;
- Review 1/2/3 documented;
- upstream rechecked before merge;
- H1/H2/H3 requirements satisfied when applicable.

Use squash merge when intermediate corrective commits add no historical value.

## 17. Upstream contribution discipline

Current upstream AROS `CONTRIBUTING.md` does not state an explicit blanket AI ban.

Do not infer broad permission from that.

Before the first significant Nexus-originated upstream PR:

- discuss the change with the AROS core/community as their CONTRIBUTING guide requests;
- ask whether they expect specific AI-assistance disclosure;
- disclose AI assistance honestly when relevant;
- make the human contributor responsible for the submitted code, tests and license/provenance.

## 18. Pace

A productive work cycle may end with:

- analysis;
- a failing test;
- a rejected idea;
- documentation;
- upstream integration;
- reduced scope;
- a hardware stop;
- no commit.

Commit count is not progress.

Evidence and reduced uncertainty are progress.

## 19. First protection milestone

The first meaningful protection milestone remains falsifiable.

A future N1 CPU Protection Proof should eventually demonstrate, with executable evidence:

- distinct CR3/address spaces;
- private mappings inaccessible across domains;
- explicit shared MemoryObject still accessible;
- NX fault is real;
- supervisor write protection is real where required;
- protected fault is classified/contained;
- repeated safe context switches.

Do not declare N1 from code inspection alone.
