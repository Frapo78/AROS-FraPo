# Nexus Trust and Fault Model

> Status: architectural baseline
>
> This document defines what Nexus is trying to protect, from whom, and at which implementation stage.

## 1. Why this document exists

"Memory protection" is too vague to be a useful engineering claim.

A system may protect one process from an accidental pointer bug while still allowing the same process to:

- execute arbitrary privileged instructions;
- disable physical interrupts;
- program device DMA;
- map physical memory;
- monopolise CPUs;
- corrupt a shared driver;
- halt the machine through a privileged compatibility API.

Nexus therefore describes isolation as a set of independently measurable properties.

No milestone may claim that a Legacy Cell, protected process, service domain, or the normal ABI v1 runtime is isolated without stating which properties are actually enforced.

## 2. Trusted Computing Base

The long-term Nexus TCB should contain only code that must be trusted to enforce isolation.

### Trusted

- Nexus core;
- architecture backend required for privilege transitions;
- page-table management;
- interrupt/trap entry;
- capability validation;
- scheduler core;
- physical-memory allocator;
- IPC primitive implementation;
- IOMMU/DMA mapping authority;
- the minimal code required to start or stop protection domains.

### Conditionally trusted

Some components may temporarily remain trusted during migration:

- early console;
- boot loader/bootstrap;
- selected firmware interfaces;
- selected hardware drivers on platforms without isolation support;
- compatibility glue that has not yet been moved out of the privileged domain.

Every temporary trusted component must be recorded as technical debt rather than silently treated as part of the final design.

### Intended to become untrusted across explicit Nexus boundaries

- protected AROS applications;
- protected service domains;
- Legacy Cells;
- isolated driver domains;
- network/filesystem services where isolated;
- future AI/automation agents;
- POSIX applications when running protected.

### Transitional compatibility trust domain

The ordinary ABI v1 AROS shared-memory runtime is a **Compatibility Trust Domain (CTD)** during convergence.

Until real privilege separation is established for that runtime, Nexus must not pretend that a hostile ABI v1 task is fully untrusted relative to the machine.

The CTD may still contain historical authority such as:

- shared writable system structures;
- supervisor APIs;
- direct interrupt control;
- direct hardware access.

As each machine mechanism is extracted beneath Nexus, that authority is reduced.

This distinction prevents the architecture from overstating security during migration.

A component may be trusted in one deployment mode and untrusted in another.

## 3. Primary threat classes

Nexus should eventually contain all of the following.

### T1 — accidental user-space corruption

Examples:

- NULL dereference;
- stale pointer;
- buffer overflow;
- use-after-free;
- execution from a non-executable page.

Required outcome:

The responsible domain fails without arbitrary modification of Nexus or another protected domain.

### T2 — deliberately hostile protected application

Examples:

- fabricated handles;
- malformed IPC;
- deliberate page faults;
- attempts to map another process;
- attempts to invoke privileged operations.

Required outcome:

Validation rejects the operation or terminates the offending process/domain.

### T3 — deliberately hostile ABI v1 application

This threat has two deployment states.

#### Transitional normal ABI v1 runtime

While ABI v1 executes inside the ordinary shared Compatibility Trust Domain and still retains direct machine privilege, a hostile ABI v1 application may be able to compromise the whole CTD and potentially machine state.

Nexus must **not** claim containment that has not yet been implemented.

The convergence roadmap progressively removes this authority.

#### Selective Legacy Cell / protected compatibility domain

When ABI v1 software executes inside an explicitly protected compatibility domain, it may compromise shared legacy state inside that domain but must not thereby compromise:

- Nexus;
- another protected domain;
- an isolated driver;
- unrelated protected applications;
- arbitrary physical memory.

The threat claim therefore depends on the actual deployment and demonstrated L0-L5 level.

### T4 — faulty or hostile driver

Where hardware isolation is available, a driver should not be trusted with arbitrary physical memory or arbitrary devices.

Required mechanisms include:

- device ownership;
- IRQ routing ownership;
- MMIO/PIO capability control;
- DMA mapping control;
- IOMMU enforcement where available.

### T5 — malformed external input

Examples:

- network packets;
- filesystems;
- USB descriptors;
- device responses.

The long-term goal is to keep parsers and large protocol stacks outside the Nexus TCB.

## 4. Denial of service

Nexus aims to prevent an explicitly protected domain from trivially freezing the whole machine through historical APIs. The normal ABI v1 Compatibility Trust Domain reaches this property only as privilege mechanisms are extracted and mediated.

Examples:

- infinite loop after `Forbid()`;
- virtual interrupt disable never re-enabled;
- CPU-bound task;
- service crash.

This requires Nexus to retain control of physical scheduling and interrupts.

Nexus does **not** initially promise complete defence against every resource-exhaustion attack.

Resource quotas for:

- CPU;
- memory;
- capabilities;
- IPC queues;
- pinned DMA memory;

are later hardening work.

## 5. Isolation levels

Nexus uses explicit isolation levels so prototypes cannot overstate their security.

### L0 — Compatibility-domain classification

The compatibility trust boundary is identified, but hardware protection is not yet proven.

For the normal ABI v1 runtime, L0 may still mean a trusted shared world with historical machine authority.

For a Legacy Cell prototype, L0 may mean conceptual containment without a proven hardware boundary.

### L1 — CPU memory isolation

A domain has a separate hardware address space.

It cannot directly read or write private Nexus mappings or another protected domain through normal CPU memory accesses.

### L2 — Privilege isolation

The domain cannot obtain real Nexus supervisor authority.

Historical interfaces such as:

- `Supervisor()`;
- `SuperState()`;
- `Disable()/Enable()`;
- privileged I/O instructions;
- CRx/MSR manipulation;

are denied, virtualised or mediated.

### L3 — Hardware isolation

The domain cannot directly control arbitrary:

- MMIO;
- PIO;
- IRQ controllers;
- PCI configuration;
- physical memory mappings.

Hardware access is provided through Nexus-controlled capabilities or services.

### L4 — DMA isolation

A device controlled by an untrusted driver cannot DMA outside explicitly granted memory.

Preferred mechanism:

- IOMMU domain + Nexus-owned DMA MemoryObjects.

Without an IOMMU, L4 cannot be honestly claimed for a driver that can program unrestricted DMA.

### L5 — Service fault isolation

Major drivers and services can fail or restart without forcing a Nexus reboot or corrupting unrelated domains.

## 6. Security claims during development

Every prototype or milestone should state its highest proven level.

Examples:

- "Legacy Cell prototype: L1 only";
- "protected payload: L2";
- "NVMe domain on VT-d: L4";
- "NVMe domain without IOMMU: L3, trusted DMA driver".

Documentation and community announcements must use these levels rather than the unqualified word "isolated".

## 7. Fault classification

A trap or fault is classified by the domain that owned the interrupted execution context.

### Nexus fault

A fault while Nexus is executing privileged core code is a kernel failure.

Initial policy:

- capture diagnostics;
- panic/halt.

Later recovery may be possible for selected subsystems, but Nexus core corruption must never be hidden.

### Protected-domain fault

Examples:

- page fault;
- invalid opcode;
- protection violation;
- invalid capability operation.

Policy:

- record diagnostics;
- terminate the affected process/domain;
- release resources;
- keep Nexus alive.

### Legacy Cell fault

Policy depends on the fault.

Recoverable ABI-visible traps may continue to be forwarded to legacy Exec when compatible.

A fatal Cell-level protection violation must:

- stop the Cell;
- revoke Cell capabilities;
- revoke hardware/service channels;
- free or quarantine Cell memory;
- keep Nexus alive.

## 8. ABI v1 shared-memory limitation

Nexus cannot transparently give every existing ABI v1 task a separate address space while preserving arbitrary pointer-sharing semantics.

That is intentional.

The convergent architecture therefore permits several modes:

- normal ABI v1 inside the shared Compatibility Trust Domain;
- protected AROS applications using explicit Nexus boundaries;
- selective Legacy Cells for risky legacy software;
- adapted/generated service boundaries.

Strong isolation is added where the contract permits it rather than being falsely claimed for all ABI v1 software at once.

## 9. Hardware without an IOMMU

A platform without usable DMA remapping cannot offer the same driver threat model as one with an IOMMU.

Nexus should expose this honestly.

Possible policies:

- keep selected DMA drivers in the trusted domain;
- use bounce buffers where practical;
- mark the system's active isolation level in diagnostics;
- refuse untrusted driver-domain mode for unsafe devices.

No software abstraction can make unrestricted bus-master DMA safe without a hardware or equivalent mediation mechanism.

## 10. Success criterion

The security architecture is successful when the system can answer, for every failure:

1. Which domain caused it?
2. Which authority did that domain possess?
3. Which memory could it access?
4. Which device could it program?
5. Why did the fault not cross the declared boundary?

If those questions cannot be answered, the boundary is not yet a security boundary.
