# ADR-0002: Convergent AROS / Nexus architecture

- Status: Accepted as current architectural direction
- Date: 2026-10-07
- Scope: Nexus architecture
- Supersedes: the mandatory deployment topology implied by ADR-0001
- Retains: ADR-0001's separation between shared-pointer compatibility semantics and protected memory-safety semantics

## Context

The first Nexus architecture deliberately separated two execution models:

1. a Legacy Domain preserving ABI v1 shared-pointer semantics;
2. a Protected Domain using isolated address spaces, capabilities and explicit memory sharing.

That distinction remains technically valid.

Further source analysis and review of current upstream AROS showed, however, that making a full Legacy Cell the mandatory home of the normal AROS runtime would create risks of its own:

- too many permanent low-level layers;
- duplicated scheduling/runtime concepts;
- adapter maintenance as AROS evolves;
- unnecessary IPC crossings;
- pressure to create a parallel ExecNG ecosystem;
- a growing fork that becomes harder to synchronize with upstream.

At the same time, current AROS already contains several architectural mechanisms that are directly useful to Nexus:

- `kernel.resource` as a concentration point for low-level CPU/MMU/IRQ mechanisms;
- OOP/HIDD interfaces for hardware abstraction;
- `genmodule` and interface-description tooling;
- active x86-64, ARM64 and RISC-V work;
- current NVMe, AHCI, USB, graphics and network work;
- transparent m68k compatibility through `m68kemu.library`;
- generated m68k thunk tables and generated shadow-structure layouts.

In particular, upstream `m68kemu.library` already demonstrates an important design pattern:

> preserve the legacy ABI at the edge, generate translation where possible, and route compatible operations into the native AROS runtime.

Nexus should strengthen that pattern rather than build a parallel "Rosetta" stack.

## Decision

Nexus adopts a **convergent architecture**.

AROS remains the primary operating-system runtime and user-visible identity.

Nexus becomes a small privileged executive/substrate extracted incrementally from existing AROS low-level code and responsible only for machine-level mechanisms that require a modern protection boundary.

The target shape is:

```
applications
    |
    | native AROS / m68k compatibility / future protected APIs
    v
AROS system runtime
    |
    | Exec, DOS, Intuition, Zune, Wanderer,
    | HIDD/OOP, AHI, Poseidon, AROSTCP, m68kemu
    |
    | generated/stable Nexus contracts
    v
Nexus Executive
    |
    | CPU, Thread, AddressSpace, MemoryObject,
    | Endpoint, Capability, IRQ, Timer,
    | Device authority, DMA/IOMMU, faults
    v
hardware
```

## Decision 1 — AROS remains the primary runtime

Nexus does not replace AROS with a new userland personality.

The existing AROS runtime remains the main system environment.

That means the project prefers evolving and adapting:

- Exec;
- DOS;
- Intuition;
- Zune;
- Wanderer;
- HIDD/OOP;
- AHI;
- Poseidon;
- AROSTCP;
- m68kemu;

instead of recreating equivalent parallel subsystems.

## Decision 2 — no mandatory parallel ExecNG ecosystem

Nexus does not create a separate permanent ExecNG API/runtime merely because protected execution needs new primitives.

Where new semantics are required, they should preferably appear as:

- new AROS APIs;
- versioned interfaces;
- optional protected variants;
- internal Nexus contracts.

The strongest Exec ideas remain central:

- Tasks/threads;
- signals/events;
- message ports;
- libraries;
- devices;
- resources;
- asynchronous I/O.

Unsafe implementation assumptions do not become permanent Nexus contracts.

## Decision 3 — Nexus contains mechanisms; AROS contains policy

Nexus should know only low-level objects such as:

- CPU;
- Thread;
- AddressSpace;
- MemoryObject;
- Endpoint;
- Capability;
- IRQ;
- Timer;
- Device authority;
- DMA mapping.

AROS continues to own higher-level semantics such as:

- Exec task policy;
- DOS process semantics;
- library/device lifecycle;
- Intuition;
- Wanderer;
- most user-visible service policy.

This separation is the primary stability boundary.

## Decision 4 — extract rather than rewrite

Nexus should be formed by progressively extracting clean mechanisms from current AROS low-level code.

The default question is:

> Which existing AROS mechanism can be preserved, separated or wrapped?

not:

> Which subsystem can be rewritten?

A new independent kernel tree is not the default plan.

## Decision 5 — Legacy Cells become selective tools

Legacy Cells remain valid and useful where an ABI v1 shared-pointer environment must be contained as a unit.

They are no longer the mandatory topology for the entire normal AROS runtime.

Possible uses include:

- particularly unsafe legacy components;
- compatibility sandboxes;
- applications requiring historical privilege assumptions;
- future per-application legacy isolation;
- experimental failure containment.

The security invariant from ADR-0001 remains:

> raw shared pointers may exist inside one compatibility trust domain, but they do not become authority across a protected Nexus boundary.

## Decision 6 — upstream m68kemu is the primary Amiga binary compatibility path

Nexus will not build a competing m68k translation stack unless evidence later proves that upstream cannot support a required capability.

Current upstream `m68kemu.library` already provides:

- transparent Hunk detection;
- contained m68k memory;
- Moira CPU emulation;
- fake Amiga library bases;
- LVO interception;
- generated native thunks;
- generated structure-layout translation;
- routing to native AROS libraries.

Future performance work may introduce:

- a JIT/DBT backend;
- better CPU backends;
- stronger containment;
- more generated bridges.

Those improvements should preferably happen behind the same AROS compatibility contract so that upstream improvements remain directly reusable.

## Decision 7 — generate bridges from interface descriptions

Manual compatibility/adaptation layers are a long-term maintenance risk.

Nexus therefore adopts a generator-first direction.

Where practical, one semantic interface description should be capable of producing or validating multiple representations:

- direct native call;
- HIDD/OOP method;
- Nexus service stub;
- Nexus IPC proxy;
- ABI compatibility thunk;
- validation/metadata information.

Existing AROS infrastructure such as:

- `.conf` interface definitions;
- FD files;
- `genmodule`;
- HIDD/OOP metadata;
- m68k thunk generators;
- shadow-layout generators;

should be extended before creating unrelated schema systems.

Generated transport is not permission to serialize arbitrary pointers. Cross-boundary contracts still use handles, capabilities and explicit memory objects.

## Decision 8 — direct and isolated paths may share one semantic contract

Nexus is not required to be a pure microkernel.

A service interface may have:

- a direct-call implementation when isolation provides little value;
- a Nexus-mediated implementation when fault/security boundaries matter.

The caller should not need a completely different conceptual API solely because the implementation moved behind a protection boundary.

This permits performance-sensitive code to remain direct while enabling selective isolation.

## Decision 9 — code ownership is classified as U / A / N

To control fork divergence, Nexus classifies major code areas:

### U — Upstream-owned

Prefer to consume almost unchanged from AROS.

Examples may include:

- DOS;
- Intuition;
- Zune;
- Wanderer;
- m68kemu;
- many HIDDs;
- AROSTCP;
- applications and tools.

### A — Adapted

AROS code with a deliberately small Nexus seam or adapter.

Likely examples:

- selected Exec internals;
- kernel.resource;
- selected HIDD entry points;
- low-level platform initialization.

### N — Nexus-owned

New infrastructure that defines the protection substrate.

Examples:

- AddressSpace abstraction;
- Capability authority;
- MemoryObject;
- protected Endpoint;
- domain-aware fault ownership;
- DMA/IOMMU authority.

This classification is reviewed as the architecture evolves; it is not a permanent assignment for every file.

## Decision 10 — AI readiness is architectural, not a kernel dependency

Nexus should prepare for AI/agent workloads without putting an LLM inside the trusted kernel core.

The kernel remains deterministic and model-independent.

Future AI integration should be built from ordinary system mechanisms:

- message-based asynchronous services;
- capability-scoped tool access;
- MemoryObjects for large tensors/audio/images;
- generic compute-accelerator interfaces;
- local or remote model providers;
- an automation/command protocol inspired by the interoperability spirit of ARexx.

No Phase 1 kernel work depends on AI.

## Decision 11 — architecture is stable in principles, revisable in implementation

This ADR establishes a direction, not a claim that every future mechanism is already known.

Fine tuning is expected.

Larger revisions are allowed when supported by:

- upstream changes;
- implementation evidence;
- performance data;
- compatibility results;
- security findings;
- hardware validation;
- red-team review.

Major changes require a new ADR that explains what is being superseded and why.

The project must not preserve a bad idea merely because it was documented early.

## Consequences

### Positive

- AROS remains recognizably AROS.
- Upstream improvements remain easier to consume.
- m68k compatibility improves with upstream rather than through a parallel fork-only translator.
- Fewer permanent runtime layers reduce latency and maintenance cost.
- New protection mechanisms can be introduced under existing AROS APIs.
- Direct and isolated services can coexist.
- Interface generation can reduce adapter drift.
- AI/automation can grow later without contaminating the kernel TCB.

### Costs

- extracting clean mechanisms from existing coupled code may be harder than writing a clean-room subsystem;
- some AROS internals will need carefully maintained seams;
- the direct/isolated dual path needs strong interface discipline;
- generator tooling becomes strategically important;
- selective Legacy Cells may create multiple execution configurations that require testing;
- the architecture will evolve incrementally rather than arriving as a single clean redesign.

## Rejected alternative — full new kernel plus AROS personality

Rejected as the default strategy because it creates a long period in which two systems must be maintained and risks losing upstream momentum.

A clean-room kernel remains a useful comparison model but is not the implementation plan.

## Rejected alternative — mandatory Legacy Cell for all normal AROS

Rejected as the default topology because it would put a permanent translation boundary between the evolving AROS runtime and the machine even where no such boundary is needed.

Legacy Cells remain available selectively.

## Rejected alternative — pure microkernel IPC everywhere

Rejected because uniform isolation is not worth uniform IPC cost and complexity.

Isolation should be applied where it materially improves fault containment, authority control or restartability.

## Rejected alternative — fork-specific Rosetta implementation

Rejected because upstream AROS is already developing transparent m68k compatibility with generated thunk/shadow infrastructure.

Nexus should contribute to or consume that work rather than duplicate it.

## Relationship to ADR-0001

ADR-0001 remains correct about the irreducible distinction between:

- shared-pointer compatibility semantics;
- protected memory-safety semantics.

ADR-0002 narrows the deployment conclusion.

The existence of those two contracts does **not** require the complete AROS runtime to live permanently inside a Legacy Cell.

Protection boundaries may instead be introduced selectively beneath or around AROS components as Nexus mechanisms become available.

## Long-term invariant

Nexus succeeds only if both statements remain true:

1. **AROS can continue to evolve with its upstream community without being trapped behind a fork-specific compatibility stack.**
2. **Protected Nexus boundaries never rely on implicit shared raw-pointer authority.**

Any future architecture that breaks either statement requires explicit reconsideration.
