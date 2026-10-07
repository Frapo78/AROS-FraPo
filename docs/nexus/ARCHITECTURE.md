# Nexus Architecture

> Status: architectural baseline
>
> Branch: `nexus/main`

Nexus is the protected execution architecture proposed for AROS-FraPo. Its purpose is to let AROS preserve the classic Amiga/AROS execution model where that model is required for compatibility, while also providing modern isolation, SMP scalability, driver containment and hardware support.

## 1. Non-negotiable goals

Nexus must satisfy all of the following:

1. Existing AROS/Amiga ABI v1 software must continue to run with its expected Exec/DOS/Intuition semantics.
2. New native software must be able to run in isolated address spaces with hardware-enforced memory protection.
3. The modern kernel must not depend on Amiga shared-pointer semantics.
4. Legacy compatibility must not determine the security model of the whole operating system.
5. Hardware ownership, DMA, interrupts and privileged CPU state belong to Nexus.
6. The user must experience one coherent desktop, filesystem, clipboard, network and device environment.
7. Modernization must be incremental: every milestone must leave the system bootable and testable.

## 2. Core idea: two execution domains

The historical conflict cannot be solved inside one address-space contract. ABI v1 assumes that tasks may exchange pointers and inspect shared structures. A protected process model assumes that arbitrary pointers are not valid across process boundaries.

Nexus therefore separates these semantics.

### Legacy Domain

A Legacy Cell contains the existing AROS execution environment:

- Exec tasks
- DOS processes
- classic message ports
- signals
- library bases
- Intuition
- BOOPSI/Zune
- legacy device semantics
- shared-pointer ABI v1 behaviour

Inside a Legacy Cell, the classic programming model remains valid.

The cell as a whole is unprivileged from the point of view of Nexus.

### Protected Domain

Native Nexus applications use:

- isolated address spaces
- opaque handles/capabilities
- protected IPC endpoints
- explicit shared-memory grants
- controlled device access
- W^X mappings
- per-process credentials
- fault containment

No arbitrary pointer may cross a protection boundary.

## 3. Nexus kernel contract

The Nexus core should understand only low-level objects:

- CPU
- Thread
- AddressSpace
- MemoryObject
- Capability
- Endpoint
- IRQ
- Timer
- Device
- DMA mapping

It must not know about:

- Window
- Gadget
- DOS Process
- Amiga library internals
- BOOPSI
- Wanderer

Those belong above the protection boundary.

## 4. Legacy Cell contract

A Legacy Cell is a protected container for the existing ABI v1 world.

Within a cell:

- pointers remain meaningful across Exec tasks;
- `PutMsg()`, `Signal()`, `OpenLibrary()`, `AllocMem()`, `Forbid()` and `Permit()` retain their expected semantics;
- existing AROS libraries can initially remain largely unchanged;
- the current Exec scheduler may continue to schedule tasks internally.

Outside a cell:

- no legacy pointer is trusted;
- no cell can directly modify Nexus memory;
- no cell owns raw interrupt controllers or unrestricted DMA;
- communication crosses a validated Nexus boundary.

A catastrophic failure inside a Legacy Cell may kill the cell, but must not corrupt Nexus, native applications or isolated driver domains.

## 5. Scheduling model

The first implementation uses hierarchical scheduling.

Nexus schedules:

- protected native threads;
- driver-service threads;
- one or more Legacy Cell vCPUs.

Inside the Legacy Cell, the current Exec scheduler continues to schedule ABI v1 tasks.

This deliberately avoids rewriting Exec during the first architecture milestone.

Later, Exec may acquire a Nexus scheduler backend, but that is not required for the MVP.

## 6. IPC and capabilities

Protected-domain communication uses opaque capabilities.

A capability grants authority to a specific kernel object. A process cannot manufacture one by guessing an integer value.

Initial object classes:

- endpoint
- memory object
- process/thread
- file/service handle
- device channel
- IRQ subscription
- DMA object

Capabilities are transferable only when the sender owns transfer rights.

The public ABI must not expose Nexus kernel pointers.

## 7. Shared memory without global memory

Large data transfers must not require copies.

Nexus therefore provides MemoryObjects. A MemoryObject represents pages that may be mapped into one or more AddressSpaces with independently controlled permissions.

A transfer describes:

- object capability
- offset
- length
- rights

not a raw virtual address.

Expected users include:

- graphics surfaces
- audio buffers
- network packet rings
- filesystem caches
- video buffers
- DMA buffers

## 8. Hardware ownership

Nexus owns privileged hardware resources.

The long-term driver model is:

```
AROS service/library
        |
        v
     HIDD proxy
        |
        | Nexus IPC
        v
 isolated driver domain
        |
        v
     hardware
```

This lets AROS retain HIDD as the compatibility and object-model boundary while moving actual hardware access out of the Legacy Cell.

## 9. DMA and IOMMU

CPU memory protection is incomplete if a device can DMA anywhere in physical RAM.

On IOMMU-capable platforms, Nexus must:

- own IOMMU configuration;
- create DMA objects;
- map only authorised physical pages;
- prevent drivers from programming unrestricted DMA targets.

On hardware without an IOMMU, affected drivers are explicitly classified as trusted and the reduced isolation level must be visible to diagnostics.

## 10. ABI strategy

### ABI v1

ABI v1 is the historical AROS/Amiga compatibility ABI.

It is frozen for compatibility and lives primarily inside Legacy Cells.

### ABI v2

ABI v2 is the protected Nexus-native ABI.

It is:

- handle-based;
- 64-bit clean;
- SMP-safe;
- address-space-safe;
- capability-aware;
- designed for W^X and ASLR;
- independent of shared kernel structures.

ABI v2 should preserve the conceptual elegance of Exec without copying unsafe implementation assumptions.

## 11. POSIX

POSIX is a compatibility personality, not the kernel architecture.

Where possible, POSIX APIs are implemented over Nexus/ABI v2 primitives.

Nexus does not adopt Unix process semantics merely to make POSIX easier.

## 12. Desktop unification

Legacy and native applications must appear in one desktop.

The long-term display model uses surfaces delivered to a compositor. The compositor does not need to know whether a surface originated from:

- legacy Intuition;
- ABI v2 native UI;
- POSIX software;
- m68k compatibility.

This allows HiDPI, multiple displays, compositing and GPU acceleration without requiring legacy applications to understand them.

## 13. Failure model

The target containment hierarchy is:

```
application crash      -> terminate application
legacy application     -> at worst terminate Legacy Cell
network stack crash    -> restart network service
driver crash           -> restart driver domain
desktop crash          -> restart desktop service
Nexus crash            -> system failure
```

The project should continually reduce the amount of code whose failure can reach the final line.

## 14. First implementation target

The first architecture target is x86-64 under QEMU.

The first proof is not a new desktop or a new API.

The proof is:

> Boot the current x86-64 AROS world as a non-privileged Legacy Cell above Nexus-owned page tables, CPU state and interrupt control, while preserving observable ABI v1 behaviour.

Only after that boundary works should hardware services and ABI v2 be expanded.

## 15. Architectural prohibition list

Until an explicit ADR changes these rules:

- do not break ABI v1 to make Nexus easier;
- do not expose raw Nexus pointers to userland;
- do not make POSIX the native kernel API;
- do not move GUI policy into the Nexus core;
- do not require a complete Exec rewrite for the MVP;
- do not give untrusted driver domains unrestricted physical-memory access;
- do not make legacy compatibility code privileged merely because it historically was;
- do not merge a milestone that cannot be exercised by an automated or reproducible test.
