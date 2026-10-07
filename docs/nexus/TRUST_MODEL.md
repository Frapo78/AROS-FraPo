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

No milestone may claim "the Legacy Cell is isolated" without stating which properties are actually enforced.

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

### Not trusted by Nexus

- ABI v1 applications;
- ABI v2 applications;
- POSIX applications;
- Legacy Cells;
- driver domains;
- network stacks;
- filesystems where isolation is available;
- desktop services;
- GUI applications.

A component may be trusted by another service while still being untrusted by Nexus.

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

A legacy application is allowed to exploit the shared-memory assumptions inside its own Legacy Cell.

It must not be allowed to turn those historical assumptions into arbitrary Nexus authority.

A hostile legacy application may therefore compromise:

- itself;
- other software in the same Legacy Cell;
- shared ABI v1 state in that cell.

It must not thereby compromise:

- Nexus;
- another Legacy Cell;
- an ABI v2 process;
- an isolated driver domain;
- arbitrary physical memory.

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

Nexus aims to prevent a Legacy Cell or protected process from trivially freezing the whole machine through historical APIs.

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

### L0 — Compatibility containment

ABI v1 execution is conceptually separated from Nexus, but no hardware memory boundary is yet proven.

Useful for architecture work only.

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

## 8. Legacy shared-memory limitation

Nexus cannot provide per-application memory isolation *inside* a conventional ABI v1 Legacy Cell without breaking software that depends on shared pointers.

That is intentional.

Applications requiring stronger isolation may eventually run in:

- a separate Legacy Cell;
- an ABI v2 process;
- a compatibility sandbox.

This is not considered a failure of the architecture. It is the explicit boundary between compatibility and protection.

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
