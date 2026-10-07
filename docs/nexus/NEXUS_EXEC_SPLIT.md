# Nexus / Exec Split

> Status: architectural classification baseline
>
> Current direction: ADR-0002 convergent architecture

## 1. Purpose

This document prevents two opposite mistakes:

1. treating current `kernel.resource` as if it were already Nexus;
2. creating a completely separate ExecNG/kernel stack and duplicating AROS.

The target is a narrow mechanism/policy split inside the evolving AROS system.

## 2. Current reality

AROS already concentrates important low-level mechanisms in and around `kernel.resource`:

- CPU contexts;
- interrupts;
- MMU mappings;
- page allocation;
- CPU discovery;
- spinlocks;
- timers;
- SMP/IPI support;
- diagnostics.

That is valuable.

The same code also still depends on AROS/Exec concepts such as:

- `SysBase`;
- `struct Task`;
- Exec ready/wait/running lists;
- soft interrupts;
- scheduler policy;
- legacy privilege semantics.

Nexus must therefore be extracted *through* this area, not equated with it.

## 3. Target relationship

The intended long-term shape is:

```
AROS applications
       |
       v
Exec / DOS / AROS runtime
       |
       | AROS policy + compatibility
       v
thin Nexus adapters
       |
------- stable mechanism boundary -------
       |
       v
Nexus Executive
CPU / Thread / AddressSpace
MemoryObject / Capability
Endpoint / IRQ / Timer
Device / DMA / IOMMU
       |
       v
hardware
```

This is not a permanent compatibility personality stack.

Exec remains the normal AROS runtime.

## 4. Scheduling ownership

### Exec owns policy

Exec continues to define:

- `struct Task`;
- task priorities;
- ready/wait/running lists;
- signals;
- message ports;
- `Forbid()/Permit()`;
- ABI-visible scheduling semantics.

### Nexus owns machine scheduling mechanisms

Nexus eventually owns:

- physical CPUs;
- protected execution contexts;
- address-space activation;
- timer/preemption mechanism;
- cross-domain scheduling authority;
- CPU affinity/migration mechanisms required by protected contexts.

Nexus should not need to walk Exec lists to understand its own protection objects.

The integration may initially preserve existing Exec scheduling code while extracting the lower-level CPU/context-switch machinery beneath it.

## 5. Current kernel.resource API classification

The table classifies semantics, not final symbol names.

| Current API family | Convergent target | Notes |
| --- | --- | --- |
| `KrnDispatch/KrnSwitch/KrnSchedule` | A-class adapter | Exec policy remains AROS-owned; low-level context/CPU mechanism may be extracted |
| `KrnSetScheduler/KrnGetScheduler` | AROS policy | Do not turn legacy scheduler policy into Nexus global policy |
| `KrnScheduleCPU` | Split | physical IPI/reschedule mechanism may be Nexus-owned; Exec intent remains AROS policy |
| `KrnCause` | AROS event semantics | may later use Nexus event delivery underneath |
| `KrnCli/KrnSti` | A-class privilege seam | direct physical IF control cannot cross into protected contexts |
| `KrnIsSuper` | A-class privilege seam | protected execution needs explicit privilege ownership |
| IRQ add/remove/modify/allocate | Split toward Nexus authority | AROS-facing semantics may remain while physical routing becomes Nexus-owned |
| `KrnGetBootInfo` | Read-only AROS view | keep mutable Nexus internals private |
| `KrnMapGlobal/KrnUnmapGlobal` | A-class MMU seam | converge toward explicit AddressSpace target internally |
| `KrnSetProtection` | Nexus mechanism behind adapter | real R/W/X enforcement belongs below AROS policy |
| `KrnVirtualToPhysical` | Restricted compatibility API | raw physical addresses must not become general authority |
| `KrnAllocPages/KrnFreePages` | Split | distinguish physical-page authority from AROS allocation policy |
| `KrnCreateContext/KrnDeleteContext` | A-class seam | separate CPU execution context from `struct Task` semantics |
| CPU topology queries | Shared read-only service | physical topology comes from Nexus mechanism; AROS decides exposure/policy |
| spinlock APIs | Shared implementation utility | not a security boundary |
| clock-source registration | Split | physical timer mechanism versus AROS timer policy |
| `KrnExitInterrupt` | architecture/Nexus internal | should not become ordinary application authority |
| diagnostics/backtrace | Shared diagnostic facility | must validate cross-domain access when protection exists |

## 6. APIs that should not become permanent protected contracts unchanged

### KrnMapGlobal

"Global" reflects the current shared-address-space design.

The internal protected form needs an explicit target AddressSpace.

Legacy/public behaviour may remain through an adapter.

### KrnVirtualToPhysical

A physical address becomes dangerous when combined with MMIO or DMA authority.

Protected APIs should prefer:

- MemoryObject;
- device resource;
- DMA mapping handle.

### KrnCreateContext

Current context creation is tied closely to Exec Task execution.

A Nexus Thread/context mechanism must be explainable without `struct Task`.

### KrnCli/KrnSti

These may remain useful internally for trusted AROS/kernel code during convergence.

They must not become unrestricted physical interrupt controls for future protected applications or isolated services.

## 7. Nexus object vocabulary

The low-level object set remains deliberately small.

### NexusCPU

Physical logical CPU.

### NexusThread

Protected/machine-level execution context independent of Exec Task policy.

An Exec Task may initially be backed by existing machinery and later by a NexusThread adapter where useful.

### NexusAddressSpace

Hardware translation/protection context.

### NexusMemoryObject

Shareable physical/logical memory object independent of one virtual address.

### NexusEndpoint

Protected asynchronous communication endpoint.

### NexusCapability

Explicit authority to operate on a Nexus object.

### NexusIRQ

Physical/virtual interrupt authority.

### NexusTimer

Machine timer object.

### NexusDevice

Authority over a device or hardware resource.

### NexusDMA

Controlled device-memory mapping.

## 8. No mandatory Legacy kernel layer

Earlier Nexus drafts treated a "Legacy kernel compatibility layer" as a permanent layer beneath all of Exec.

ADR-0002 changes that.

The convergent model prefers:

```
Exec / AROS code
      |
small local adapter where needed
      |
Nexus mechanism
```

Only code that actually crosses a protection boundary needs a strong translation boundary.

This reduces:

- layer count;
- IPC;
- duplicate scheduler logic;
- maintenance burden.

## 9. Selective Legacy Cells

A Legacy Cell is still useful when a whole shared-pointer/privilege environment needs containment.

Examples:

- unsafe historic software;
- direct-hardware legacy code;
- compatibility experiments;
- isolated legacy service bundles.

In that case, the older compatibility-kernel reasoning still applies inside the Cell.

It is now a selective deployment mode rather than the architecture of normal AROS.

## 10. Extraction rule

When touching current low-level code, classify each dependency.

### Nexus mechanism

Keep/extract it below the stable boundary if it can be explained without AROS policy objects.

### AROS policy

Keep it above the boundary if it fundamentally reasons about:

- Tasks;
- Exec lists;
- signals;
- softints;
- DOS;
- application-visible ABI behaviour.

### Adapter

Use a narrow adapter where the current function mixes both.

The adapter is successful when it is smaller and more stable than duplicating the whole function or subsystem.

## 11. U / A / N relation

This document focuses mainly on A-class areas.

- **U**: upstream-owned, little/no Nexus-specific change.
- **A**: adapted through narrow mechanism/policy seams.
- **N**: Nexus-owned substrate.

`kernel.resource` and selected Exec internals are expected to be A-class during early convergence.

See `UPSTREAM_INTEGRATION.md`.

## 12. First implementation consequence

The first Nexus code still should not begin by replacing Exec scheduling.

The smallest safe path remains:

1. explicit `NexusAddressSpace` representation around the current runtime MMU root;
2. explicit internal target for map/protect operations;
3. real protection semantics;
4. domain-aware fault classification;
5. second protected execution context;
6. MemoryObject proof.

The normal AROS runtime stays where it is.

No full Legacy Cell migration is required.

## 13. Definition of a clean Nexus mechanism

A Nexus mechanism should be explainable without requiring the public contract to contain:

- `struct Task`;
- `ExecBase`;
- DOS Process;
- message-port internals;
- BOOPSI;
- Wanderer;
- legacy library-base internals.

An AROS adapter may reference those concepts.

The mechanism beneath it should not.

## 14. Evolution rule

This split is intentionally revisable.

If upstream AROS later introduces a cleaner abstraction, Nexus should use it and remove local glue.

If extraction creates more complexity than it removes, the boundary should be reconsidered through a new ADR rather than defended for historical reasons.
