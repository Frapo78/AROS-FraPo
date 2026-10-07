# Nexus / Exec Split

> Status: architectural classification draft
>
> This document prevents a critical design mistake: treating the current `kernel.resource` API as though it were already the Nexus kernel API.

## 1. Current reality

AROS already has a useful low-level boundary in `kernel.resource`.

It contains or fronts mechanisms for:

- scheduling;
- CPU contexts;
- interrupts;
- MMU mappings;
- page allocation;
- CPU discovery;
- spinlocks;
- timers;
- diagnostics.

That makes it the best extraction seam available.

It is **not**, however, a clean protection-kernel boundary today.

Current native implementations still know about or call into:

- `SysBase`;
- `struct Task`;
- Exec ready/running/wait lists;
- Exec soft interrupts;
- Exec scheduler state;
- ABI v1 supervisor semantics.

Nexus must therefore be extracted *through* this seam, not equated with it.

## 2. Target layering

The intended layering is:

```
ABI v1 applications
       |
       v
exec.library / dos.library
       |
       v
Legacy kernel compatibility layer
       |
       | narrow privileged ABI
       v
---------------- protection boundary ----------------
       |
       v
Nexus
  CPU / Thread / AddressSpace
  MemoryObject / Capability
  Endpoint / IRQ / Timer
  Device / DMA / IOMMU
       |
       v
hardware
```

For ABI v2:

```
ABI v2 runtime
       |
       v
Nexus native interface
```

## 3. Scheduling ownership

### Legacy side owns

- Exec `Task`;
- task priorities as ABI v1 sees them;
- Exec ready/wait/spin lists;
- `Forbid()/Permit()`;
- signals;
- message ports;
- legacy scheduling policy.

### Nexus owns

- physical CPUs;
- protected threads;
- Legacy Cell vCPU threads;
- CPU-time allocation between domains;
- preemption of a Cell regardless of `Forbid()`;
- migration/affinity at the domain/vCPU level.

Nexus must not walk Exec task lists to decide which protected domain runs next.

This is the key separation.

## 4. Current kernel.resource API classification

The table below classifies *semantics*, not necessarily final public symbol names.

| Current API family | Target classification | Notes |
| --- | --- | --- |
| `KrnDispatch/KrnSwitch/KrnSchedule` | Legacy kernel shim | Operate on Exec Tasks today; must not define Nexus scheduling |
| `KrnSetScheduler/KrnGetScheduler` | Legacy shim / policy adapter | May configure Cell scheduler, not Nexus global policy directly |
| `KrnScheduleCPU` | Split | Legacy requests vCPU attention; Nexus owns physical reschedule/IPI |
| `KrnCause` | Legacy event shim | Soft-int semantics remain Cell-side |
| `KrnCli/KrnSti` | Legacy virtual privilege | Must not expose physical IF control to an untrusted Cell |
| `KrnIsSuper` | Legacy virtual privilege | Must report Cell-visible privilege, not unrestricted Nexus privilege |
| IRQ add/remove/modify/allocate | Nexus-backed capability service | Ownership and routing must be validated |
| `KrnGetBootInfo` | Read-only compatibility view | Do not expose mutable Nexus boot internals |
| `KrnMapGlobal/KrnUnmapGlobal` | Split / restricted | Replace implicit global mapping with AddressSpace-targeted mapping |
| `KrnSetProtection` | Nexus AddressSpace operation | Must include real R/W/X enforcement |
| `KrnVirtualToPhysical` | Restricted compatibility operation | Physical addresses must not become general authority |
| `KrnAllocPages/KrnFreePages` | Nexus memory primitive behind shim | Distinguish physical allocation from virtual mapping |
| `KrnCreateContext/KrnDeleteContext` | Legacy CPU-context shim | Current context represents Exec Tasks; Nexus needs its own Thread object |
| CPU count/number/mask APIs | Read-only or scheduler bridge | Physical topology belongs to Nexus; Cell may receive a virtual topology |
| spinlock APIs | Utility / compatibility | Useful implementation primitive, not a security boundary |
| clock-source registration | Nexus internal/service registration | Physical timer ownership is privileged |
| `KrnExitInterrupt` | Nexus/arch internal | Must not be an ordinary Cell authority |
| system/CPU attributes | Read-only capability-safe query | Filter privileged addresses/details where required |
| debug/backtrace/format APIs | Diagnostic service | Must validate cross-domain memory access |

## 5. APIs that must not cross unchanged

Some current semantics are structurally incompatible with the protected model.

### KrnMapGlobal

"Global" currently means the shared runtime address space.

Nexus requires an explicit target:

```
Map(AddressSpaceHandle,
    VirtualAddress,
    MemoryObjectHandle,
    Offset,
    Length,
    Rights)
```

Legacy `KrnMapGlobal()` may remain as a compatibility wrapper that maps only into the Cell's permitted address space.

### KrnVirtualToPhysical

A raw physical address is dangerous authority when combined with DMA or device programming.

ABI v2 should normally use MemoryObjects and DMA handles instead.

### KrnCreateContext

The current CPU context is tightly connected to Exec task dispatch.

Nexus Thread state must be independent of `struct Task`.

### KrnCli/KrnSti

These cannot mean physical CPU interrupt flag manipulation when called by a protected Cell.

## 6. Proposed internal Nexus object vocabulary

Nexus should converge around a small architecture-neutral object set.

### NexusCPU

Represents a physical logical CPU known to Nexus.

### NexusThread

A schedulable protected execution context.

Examples:

- ABI v2 thread;
- driver-service thread;
- Legacy Cell vCPU.

It contains CPU register state but no Exec `Task` semantics.

### NexusAddressSpace

Owns a hardware translation context and its mapping metadata.

### NexusMemoryObject

Represents pages independent of any one virtual address.

### NexusEndpoint

Kernel-mediated IPC endpoint.

### NexusCapability

Authority to operate on another Nexus object.

### NexusIRQ

Validated ownership/subscription to an interrupt source.

### NexusTimer

Kernel timer object independent of Exec timer.device semantics.

### NexusDevice

Authority over a device/function or a controlled portion of it.

### NexusDMA

DMA mapping/grant object backed by permitted MemoryObjects.

## 7. What remains in legacy kernel compatibility

Initially this layer may be substantial.

It is allowed to know:

- `SysBase`;
- `struct Task`;
- ETask;
- Exec scheduler lists;
- legacy nesting counts;
- legacy interrupt-server structures;
- ABI v1 CPU context format.

Its job is to translate legacy intent into a much smaller Nexus interface.

This layer is part of the Legacy Cell, not the Nexus TCB.

## 8. Boot-time complication

Current native AROS constructs `ExecBase` only after low-level MMU, GDT, TSS and IDT setup.

This is favourable for Nexus extraction.

The target order is:

```
bootstrap
  |
  v
Nexus early init
  |
  +-- physical memory
  +-- Nexus kernel AddressSpace
  +-- traps/IRQ ownership
  +-- first NexusThread
  |
  v
create Legacy Cell
  |
  v
legacy compatibility kernel
  |
  v
krnPrepareExecBase()
  |
  v
Exec
```

The difficult part is not creating Exec later; it is ensuring that code used before Exec no longer depends on Exec-owned abstractions.

## 9. Extraction rule

When touching current kernel code, classify every dependency.

### Keep in Nexus

Only if the code needs no ABI v1 concept to do its job.

### Move/retain in legacy layer

If the code fundamentally reasons about Exec Tasks, lists, signals, softints or ABI v1 scheduler semantics.

### Split

If the mechanism is privileged but the policy/representation is legacy-specific.

Example:

- Nexus: deliver virtual event to Legacy vCPU;
- legacy layer: interpret that event as an Exec interrupt/softint.

## 10. First implementation consequence

The first Nexus code should **not** begin by replacing `KrnSchedule()`.

The first safe extraction is:

1. architecture-neutral `NexusAddressSpace` object;
2. x86-64 page-table backend;
3. explicit activation/CR3 ownership;
4. protected fault classification;
5. tiny NexusThread/payload;
6. only then a Legacy Cell bootstrap.

That gives Nexus a real primitive that is not defined in terms of Exec.

## 11. Definition of a clean Nexus primitive

A primitive is considered Nexus-clean only if its implementation and public contract can be explained without referencing:

- `struct Task`;
- `ExecBase`;
- DOS Process;
- message ports;
- signals;
- Intuition;
- BOOPSI;
- legacy library bases.

A compatibility wrapper may reference those concepts.

The primitive beneath it may not.
