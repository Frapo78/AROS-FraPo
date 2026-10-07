# Nexus Roadmap

> Status: living roadmap
>
> Current architectural direction: [ADR-0002](adr/0002-convergent-aros-nexus-architecture.md)

This roadmap is ordered by architectural dependency, not by feature visibility.

It is intentionally revisable.

A roadmap change is not a failure if new upstream work, tests, hardware evidence or red-team review shows that another path is better.

The project optimizes for:

1. correctness;
2. compatibility;
3. maintainability;
4. upstream convergence;
5. security/containment;
6. performance;
7. implementation speed.

## Roadmap principles

- **Keep AROS alive while changing it.**
- **Prefer extraction over replacement.**
- **Prefer upstream mechanisms over fork-specific duplicates.**
- **Prove seams before changing semantics.**
- **Use generated adapters where practical.**
- **Introduce protection selectively.**
- **Never confuse a working demo with a proven isolation level.**
- **Pause when real hardware is required.**
- **Allow architecture changes through reviewed ADRs.**

## Phase 0 — Convergence baseline and guardrails

Goal: understand current AROS deeply enough to extract modern mechanisms without freezing or duplicating the system.

Deliverables:

- exact upstream baseline;
- continuous upstream-head review;
- x86-64 boot map;
- privilege inventory;
- kernel.resource / Exec coupling inventory;
- x86-64 MMU/NX/W^X/TLB audit;
- ABI v1 compatibility contract;
- trust/fault model;
- U/A/N ownership classification;
- m68kemu integration analysis;
- HIDD/interface-generation analysis;
- reproducible x86-64 build;
- QEMU boot baseline;
- baseline diagnostics;
- regression-test inventory;
- mandatory three-pass review process;
- CI G0/G1/G2 foundations.

Exit criteria:

- current AROS builds reproducibly;
- reference QEMU reaches Wanderer;
- upstream changes are routinely ingestible;
- the first low-level extraction can be made without guessing about privilege, memory ownership or Exec policy;
- no architectural document still assumes that the whole AROS runtime must live in a Legacy Cell.

## Phase 1 — Extract the first Nexus mechanisms under unchanged AROS

Goal: create the first real Nexus substrate while preserving normal AROS behaviour.

Initial target: x86-64/QEMU.

### 1A — AddressSpace seam

- represent the current runtime MMU root as `NexusAddressSpace`;
- make runtime address-space ownership explicit;
- centralize ordinary CR3 activation;
- keep the existing AROS virtual layout unchanged;
- keep public ABI behaviour unchanged.

Gate:

- AROS still reaches Wanderer;
- no intended user-visible difference.

### 1B — real page protection

- enable/use hardware NX where supported;
- establish supervisor write protection where compatible;
- make R/W/X explicit in Nexus-native mapping logic;
- make failure observable rather than silently ignored.

Gate:

- protection tests are deterministic under QEMU.

### 1C — domain-aware faults

- classify faults by current Nexus execution context;
- distinguish Nexus-core faults from protected-context faults;
- collect diagnostics;
- keep Nexus alive after an expected protected-context fault.

### 1D — second protected context

- create a second address space;
- run minimal private code/data/stack;
- activate it through Nexus-owned mechanisms;
- prove L1 CPU memory isolation;
- implement correct TLB invalidation for the tested configuration.

### 1E — explicit shared memory

- introduce minimal `MemoryObject`;
- map it intentionally into multiple AddressSpaces;
- support different rights per mapping.

No full AROS migration is required in Phase 1.

## Phase 2 — Stable Nexus contracts and generation proof

Goal: prevent Nexus from becoming a maintenance-heavy set of manual adapters.

Work:

- identify the minimum semantic contract format that can reuse existing AROS descriptions;
- evaluate `genmodule`, FD files and HIDD `.conf` as sources of truth;
- generate validation metadata/stubs for one small, low-risk interface;
- support a direct path first;
- add an isolated transport only if the experiment proves the contract is sound.

The first generator proof should avoid:

- graphics;
- storage DMA;
- complex callback-heavy HIDDs.

Prefer a simple service/interface with clear scalar/handle semantics.

Exit criteria:

- one interface description can drive more than one transport representation;
- generated code is testable;
- upstream interface changes can be detected without hand-auditing duplicate declarations.

## Phase 3 — Protected AROS execution as an additive capability

Goal: allow selected AROS software to use protected execution without moving all existing software into a new personality.

Work may include:

- protected process/thread creation;
- capability-aware service access;
- explicit shared MemoryObjects;
- protected message endpoints;
- compatibility adapters to ordinary AROS services.

The exact public API is not frozen in advance.

Gate:

- one protected AROS program can coexist with normal ABI v1 software in the same system;
- the user still experiences one AROS desktop/runtime.

## Phase 4 — Selective service isolation

Goal: prove the direct/isolated dual-path architecture.

Choose one service where isolation has real value and QEMU can validate most behaviour.

Work:

- define semantic interface;
- direct implementation remains available;
- generated/validated proxy path;
- isolated service domain;
- restart/failure experiment.

Exit criteria:

- same conceptual AROS service works directly or across a Nexus boundary;
- caller code does not need a completely separate API;
- measured overhead is documented;
- service failure does not require whole-system failure.

## Phase 5 — Hardware authority and driver isolation

Goal: move machine privilege out of selected risky components.

Mechanisms:

- device authority;
- MMIO mapping rights;
- IRQ ownership;
- PCI-function ownership;
- DMA grants;
- IOMMU domains.

Progress driver by driver.

Possible priorities:

1. a QEMU-friendly virtual device;
2. storage;
3. network;
4. USB;
5. graphics/audio where practical.

Every driver-domain milestone reports its actual L0-L5 isolation level.

## Phase 6 — DMA/IOMMU hardening

Goal: establish L4 where hardware supports it.

Requirements:

- Nexus-owned IOMMU configuration;
- DMA mapping derived from authorized MemoryObjects;
- device-specific DMA domain;
- revocation;
- real-hardware validation.

This phase is subject to the hardware stop rule.

QEMU success alone is not sufficient evidence for physical DMA containment.

## Phase 7 — m68k compatibility convergence

Goal: make classic Amiga compatibility improve with upstream AROS rather than through a separate Nexus stack.

Primary implementation remains upstream `m68kemu.library`.

Potential work:

- strengthen tests;
- improve containment;
- improve generated thunks;
- improve shadow synchronization;
- reduce fixed limits;
- improve multi-process behaviour;
- evaluate JIT/DBT only when profiling justifies it.

If a JIT is pursued, prefer an execution engine behind the existing m68kemu contract.

Do not create a second transparent launcher/runtime without a strong reason.

## Phase 8 — Desktop/service resilience

Goal: use Nexus mechanisms to reduce the blast radius of user-visible failures.

Possible work:

- restartable network service;
- isolated risky parsers;
- optional desktop service restart;
- surface/compositor evolution;
- protected shared graphics buffers.

Preserve Intuition/Zune/Wanderer compatibility.

## Phase 9 — SMP and performance consolidation

Goal: ensure protection does not destroy the Amiga expectation of responsiveness.

Work:

- remote TLB shootdown;
- scheduling scalability;
- lock/contention analysis;
- IPC batching;
- shared rings;
- MemoryObject zero-copy;
- PCID/architecture optimizations where justified;
- benchmark direct versus isolated service paths.

Optimize measured bottlenecks, not imagined ones.

## Phase 10 — ARM64 convergence

Goal: express the same Nexus contracts over current AROS ARM64 work.

Do not fork the runtime.

Reuse upstream platform progress.

Port only the Nexus-owned mechanisms and adapted seams required by the architecture.

## Phase 11 — RISC-V convergence

Apply the same model to current AROS RISC-V/OpenSBI work.

Use this phase as an architecture-neutrality test:

> if a Nexus primitive only makes sense on x86-64, revisit the generic contract.

## Phase 12 — Automation and AI service foundations

Goal: make AROS programmable and agent-ready without putting AI in the kernel.

Possible work:

- structured application command discovery;
- capability-scoped tool access;
- asynchronous AI/service broker;
- provider abstraction;
- MemoryObject-based large data exchange;
- generic compute accelerator service/HIDD.

This phase must remain optional.

AROS must boot, run and remain fully useful with no AI subsystem present.

See `AI_FOUNDATIONS.md`.

## Phase 13 — Migration SDK and ecosystem tools

Provide tools to help developers understand where software fits.

Possible analysis output:

- normal ABI v1;
- protected-compatible;
- direct-hardware dependency;
- legacy privilege dependency;
- cross-boundary raw-pointer dependency;
- candidate for generated bridge.

Compiler/runtime modes may be explored later.

## Upstream checkpoints

At every major phase:

1. inspect latest upstream AROS;
2. classify relevant changes U/A/N;
3. integrate or account for them;
4. update the recorded baseline only after successful build/test;
5. remove Nexus workarounds made obsolete by upstream.

## Community checkpoints

At the end of each major phase publish:

- what was demonstrated;
- what changed;
- what stayed compatible;
- current upstream SHA reviewed;
- measured regressions/overhead;
- red-team findings;
- active isolation level;
- unresolved questions;
- next smallest safe step.

## Architecture-change rule

The roadmap is not a contract to preserve an implementation strategy forever.

A substantial change is allowed when:

- upstream evolves;
- a prototype disproves an assumption;
- performance data invalidates a boundary;
- compatibility suffers;
- security review finds a flaw;
- hardware evidence contradicts the model.

Such a change requires:

- a new/superseding ADR;
- the three-review protocol;
- explicit migration impact;
- updated roadmap.

The project should never continue down a known-wrong path merely because it was once planned.
