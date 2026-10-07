# Nexus Architecture

> Status: architectural baseline
>
> Current direction: convergent AROS / Nexus architecture
>
> Governing decision: [ADR-0002](adr/0002-convergent-aros-nexus-architecture.md)

Nexus is the protected executive architecture being explored inside AROS-FraPo.

Its purpose is to let AROS evolve deeply without splitting into two permanently separate operating systems.

The central architectural decision is:

> **AROS remains the primary runtime. Nexus becomes the small privileged executive beneath it.**

For the detailed model, see:

- [VISION.md](VISION.md)
- [CONVERGENT_ARCHITECTURE.md](CONVERGENT_ARCHITECTURE.md)
- [TRUST_MODEL.md](TRUST_MODEL.md)
- [ADDRESS_SPACE_MODEL.md](ADDRESS_SPACE_MODEL.md)
- [NEXUS_EXEC_SPLIT.md](NEXUS_EXEC_SPLIT.md)
- [UPSTREAM_INTEGRATION.md](UPSTREAM_INTEGRATION.md)
- [AI_FOUNDATIONS.md](AI_FOUNDATIONS.md)

## 1. Non-negotiable goals

Nexus must aim to satisfy all of the following:

1. Existing AROS software remains usable and upstream AROS remains continuously integrable.
2. Amiga/AROS compatibility is preserved as an explicit contract rather than treated as temporary baggage.
3. New protected execution becomes possible with hardware-enforced address-space boundaries.
4. Machine privilege, page tables, physical IRQ ownership and DMA authority can be separated from unsafe legacy assumptions.
5. Exec remains central to the identity of the system; Nexus does not replace it with a Unix process model.
6. Modernization is incremental and measurable.
7. The trusted Nexus core stays small and architecture-neutral.
8. Protection is selective: boundaries are introduced where they provide meaningful safety or restartability.
9. No protected boundary relies on implicit cross-domain raw-pointer authority.
10. The architecture remains revisable when implementation evidence or upstream evolution demands it.

## 2. System shape

The long-term model has three major planes.

```
┌──────────────────────────────────────────────────┐
│                  APPLICATIONS                    │
│ native AROS | m68k Amiga | future protected    │
└──────────────────────┬───────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────┐
│                 AROS RUNTIME                     │
│ Exec • DOS • Intuition • Zune • Wanderer        │
│ HIDD/OOP • AHI • Poseidon • AROSTCP • m68kemu   │
└──────────────────────┬───────────────────────────┘
                       │
             stable/generated contracts
                       │
╔══════════════════════▼═══════════════════════════╗
║                NEXUS EXECUTIVE                   ║
║ CPU • Thread • AddressSpace • MemoryObject       ║
║ Endpoint • Capability • IRQ • Timer              ║
║ Device authority • DMA/IOMMU • fault ownership  ║
╚══════════════════════╤═══════════════════════════╝
                       │
┌──────────────────────▼───────────────────────────┐
│                    HARDWARE                      │
└──────────────────────────────────────────────────┘
```

This is not intended to become a rigid stack of translation layers.

Most AROS calls should remain direct unless crossing a protection boundary has a concrete benefit.

## 3. Nexus kernel contract

The Nexus core should understand only low-level protection objects:

- CPU;
- Thread;
- AddressSpace;
- MemoryObject;
- Endpoint;
- Capability;
- IRQ;
- Timer;
- Device authority;
- DMA mapping/domain.

It must not need to understand:

- Window;
- Gadget;
- DOS Process;
- BOOPSI;
- Wanderer;
- FileInfoBlock;
- application policy.

Those remain in AROS.

## 4. Mechanism below, policy above

This is the most important stability boundary.

### Nexus mechanism

Examples:

- switch AddressSpace;
- schedule a protected Thread;
- map/revoke MemoryObject rights;
- deliver physical IRQ events;
- classify faults;
- allocate DMA authority.

### AROS policy

Examples:

- Exec Task scheduling semantics;
- Forbid/Permit;
- DOS process semantics;
- library/device lifecycle;
- Intuition behaviour;
- user-facing resource policy.

Nexus should not need to follow every internal AROS representation change.

## 5. Current kernel.resource is an extraction seam

`kernel.resource` remains strategically important because it already concentrates:

- MMU functions;
- CPU context operations;
- interrupts;
- scheduling-adjacent mechanisms;
- SMP/IPI support;
- diagnostics.

It is not itself Nexus.

Current implementations still depend on:

- `SysBase`;
- `struct Task`;
- Exec lists;
- legacy privilege semantics.

The extraction target is therefore:

```
AROS / Exec policy
        |
   narrow adapter
        |
-------- stable mechanism boundary --------
        |
Nexus Executive
```

See [NEXUS_EXEC_SPLIT.md](NEXUS_EXEC_SPLIT.md).

## 6. Exec remains the native programming culture

Nexus does not create a mandatory parallel ExecNG runtime.

Where new protected semantics are needed, prefer:

- additive AROS APIs;
- versioned interfaces;
- optional protected variants;
- internal Nexus adapters.

The following concepts remain valuable:

- tasks/threads;
- signals/events;
- message ports;
- libraries;
- devices;
- resources;
- asynchronous I/O.

Unsafe implementation assumptions should not become permanent protected contracts.

## 7. Compatibility contracts

### Native AROS ABI v1

ABI v1 remains supported by the normal AROS runtime.

The shared-pointer model may continue where compatibility requires it.

That does not give shared pointers authority across protected Nexus boundaries.

### Selective Legacy Cells

Legacy Cells remain available when software requires:

- historical supervisor assumptions;
- strong containment as a group;
- risky legacy execution;
- compatibility experimentation.

They are not the mandatory home of the entire normal AROS runtime.

### m68k Amiga software

The primary path is upstream AROS `m68kemu.library`.

Nexus should consume and, where useful, contribute to:

- its transparent launch integration;
- generated thunks;
- shadow-structure translation;
- containment;
- future acceleration.

A fork-specific replacement translator is not the default plan.

## 8. Protected execution

Protected execution is an additional capability of AROS, not a separate operating-system personality.

A protected boundary uses:

- isolated AddressSpaces;
- explicit MemoryObjects;
- validated Endpoints;
- capabilities/handles;
- real R/W/X permissions;
- domain-aware fault handling.

No raw virtual address is assumed to be meaningful across such a boundary.

The exact public protected-process API is intentionally not frozen yet.

## 9. Service fabric

Existing AROS interfaces should drive both direct and isolated implementations.

Conceptually:

```
               semantic interface
                 /          \
                /            \
        direct call       generated proxy
                               |
                         Nexus Endpoint
                               |
                           service domain
```

A direct path is valid when:

- the code is trusted;
- latency matters;
- isolation brings little value.

An isolated path is valuable when:

- the component parses hostile input;
- driver failure should be recoverable;
- authority should be restricted;
- restartability matters.

Nexus is not a pure microkernel and does not require IPC everywhere.

## 10. Generator-first bridge strategy

AROS already provides:

- FD files;
- module `.conf` descriptions;
- `genmodule`;
- HIDD/OOP metadata;
- m68k thunk generation;
- shadow-layout generation.

Nexus should extend those sources before inventing separate interface schemas.

Potential generated artifacts include:

- direct stubs;
- service dispatch;
- validation metadata;
- IPC proxies;
- ABI thunks;
- tests/documentation.

Generated code must still enforce protected-boundary rules.

## 11. Shared memory without global authority

Nexus uses MemoryObjects to represent shareable pages.

A mapping grants:

- object;
- offset;
- length;
- rights.

not "this process may dereference another process's arbitrary pointer".

Expected uses include:

- graphics surfaces;
- audio;
- network rings;
- storage buffers;
- video;
- compute/AI data;
- DMA buffers.

## 12. Hardware ownership

Physical machine authority belongs to Nexus mechanisms.

This includes, progressively:

- page tables;
- physical interrupt routing;
- privileged CPU state;
- MMIO ownership;
- PCI/device authority;
- DMA/IOMMU mappings.

Existing AROS drivers do not all need to move behind IPC immediately.

The architecture permits selective migration.

## 13. HIDD relationship

HIDD/OOP remains an important AROS abstraction and should be preserved.

HIDD method frames are not assumed to be wire-safe.

Interfaces containing:

- pointers;
- Hooks;
- Interrupt structures;
- TagItems;
- OOP objects;

require explicit/generated bridge logic before crossing an isolation boundary.

HIDD remains the semantic interface; Nexus transport is an implementation choice.

## 14. DMA and IOMMU

CPU page protection alone cannot contain bus-master DMA.

On supported hardware, Nexus should eventually own:

- IOMMU configuration;
- device DMA domains;
- mapping of authorized MemoryObjects;
- revocation.

On systems without usable IOMMU support, affected drivers must be classified as trusted or use a reduced-isolation design.

The active protection level must be visible in diagnostics.

## 15. Isolation levels

Nexus reports the highest property actually demonstrated:

- **L0** — compatibility containment;
- **L1** — CPU memory isolation;
- **L2** — privilege isolation;
- **L3** — hardware/MMIO/IRQ isolation;
- **L4** — DMA isolation;
- **L5** — service fault isolation.

No milestone should claim "fully isolated" merely because one of these properties works.

## 16. POSIX

POSIX remains a compatibility/runtime facility.

Nexus does not redefine itself as a Unix kernel in order to support POSIX.

Where protected primitives help POSIX, they may be reused.

## 17. AI and automation

No LLM belongs in the Nexus trusted kernel.

Nexus only provides general mechanisms useful to future AI/agent systems:

- async messaging;
- capabilities;
- MemoryObjects;
- service discovery;
- generic compute acceleration;
- protected tool/service access.

AROS may later expose AI/automation services above those mechanisms.

See [AI_FOUNDATIONS.md](AI_FOUNDATIONS.md).

## 18. Upstream ownership model

Nexus classifies areas as:

- **U — upstream-owned**;
- **A — adapted**;
- **N — Nexus-owned**.

The goal is to keep most AROS code in U, keep A diffs narrow, and concentrate divergence in N.

See [UPSTREAM_INTEGRATION.md](UPSTREAM_INTEGRATION.md).

## 19. First implementation direction

The first architecture target remains x86-64/QEMU.

The first Nexus code is still deliberately small.

### Proof 1 — explicit AddressSpace ownership

Wrap the current runtime MMU root in an internal `NexusAddressSpace` abstraction with no intended AROS-visible behaviour change.

### Proof 2 — real protection semantics

Establish actual executable/write protection and domain-aware fault ownership.

### Proof 3 — second protected context

Run a tiny separate AddressSpace and prove L1 CPU memory isolation.

### Proof 4 — explicit sharing

Share a MemoryObject intentionally between protected contexts.

None of these steps requires moving the complete AROS runtime into a Legacy Cell.

## 20. Performance principles

- do not require IPC for trusted local paths;
- use zero-copy MemoryObjects for large data;
- prefer asynchronous/batched interfaces;
- keep the trusted core small;
- measure every new protection boundary;
- remove abstractions that cost more than the property they provide.

## 21. Evolution policy

Nexus has stable principles, not frozen mechanics.

Fine tuning is expected.

Larger changes are acceptable through ADRs when supported by evidence.

The project should willingly remove a Nexus abstraction when:

- upstream AROS provides a better solution;
- tests show the abstraction is unnecessary;
- performance is unacceptable;
- a security review invalidates it;
- portability requires another mechanism.

## 22. Architectural prohibitions

Until superseded by an ADR:

- do not freeze AROS inside a fork-specific guest architecture;
- do not create a parallel Exec ecosystem without evidence that extension is impossible;
- do not duplicate upstream m68k compatibility by default;
- do not expose raw Nexus pointers across protected boundaries;
- do not make POSIX the native kernel identity;
- do not require IPC everywhere;
- do not put AI/LLM inference into the kernel TCB;
- do not give untrusted drivers unrestricted DMA;
- do not claim a protection level without a reproducible proof;
- do not accept a deep fork from upstream as normal maintenance cost.
