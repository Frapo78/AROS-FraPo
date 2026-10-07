# Nexus Address-Space Model

> Status: implementation design baseline
>
> Initial target: x86-64 / QEMU

## 1. Purpose

`NexusAddressSpace` is the first Nexus primitive because address-space ownership is the minimum mechanism required to make the protection boundary real.

The first implementation must not redesign Exec.

Its job is to move AROS from:

> one implicit runtime page-table root

toward:

> explicit address-space objects owned and activated by Nexus.

## 2. Current x86-64 AROS state

The current native x86-64 path already provides useful MMU machinery, but it is built around a shared-address-space model.

Important properties observed in the current source:

- bootstrap creates a large identity mapping before long-mode entry;
- runtime setup constructs another broad identity map;
- the runtime root is reached through `__KernBootPrivate->MMU`;
- `KrnMapGlobal()` modifies that implicit root;
- mapping helpers can elevate through legacy supervisor mechanisms;
- page-table pages may be allocated through Exec memory allocation;
- page-table updates flush the local TLB;
- selected ranges are later tightened through `core_ProtKernelArea()`;
- upper-level and large-page entries are commonly user-accessible;
- x86-64 mappings currently leave NX clear;
- `KrnSetProtection()` expresses readable/writable/executable attributes at the API level but the examined native backend does not yet enforce executable permission through NX.

These mechanisms are reusable implementation material, not yet a protected multi-address-space architecture.

## 3. First invariant

After Nexus address-space ownership is established:

> No code outside the Nexus architecture backend may write CR3 directly as part of ordinary runtime address-space switching.

Legacy compatibility code requests an operation.

Nexus decides which hardware translation context becomes active.

## 4. Object model

The architecture-neutral object is conceptually:

```c
struct NexusAddressSpace {
    NexusObjectHeader   object;
    NexusSpinLock       lock;
    NexusAddressSpaceID id;
    NexusASFlags        flags;

    /* architecture-private translation root */
    void               *arch_state;

    /* CPUs currently executing this address space */
    NexusCpuMask        active_cpus;

    /* invalidation generation */
    uint64_t            tlb_generation;
};
```

The exact C representation is not frozen by this document.

The architecture-neutral layer must not contain x86 PML4/PDP/PDE/PTE types.

Those belong in the x86-64 backend.

## 5. Address-space classes

### Nexus kernel address space

Contains:

- Nexus executable/data mappings;
- Nexus stacks;
- Nexus page-table management data;
- interrupt/trap structures;
- physical-memory-management metadata;
- explicitly required kernel device mappings.

It is never writable by an untrusted domain.

### Protected process address space

Contains:

- process code;
- data;
- stacks;
- mapped MemoryObjects;
- controlled shared libraries/runtime pages;
- explicit device/service mappings where granted.

It does not implicitly inherit arbitrary Nexus mappings as user-accessible memory.

### AROS compatibility address space

The initial convergent system may keep the normal ABI v1 AROS shared-memory world in its existing runtime address space while low-level ownership is extracted.

This is a Compatibility Trust Domain, not automatically a security boundary.

### Selective Legacy Cell address space

When a Legacy Cell is used, it contains the ABI v1 shared-memory world assigned to that Cell and explicitly granted shared/service buffers.

All tasks inside one conventional Legacy Cell share that address space.

## 6. Initial virtual-layout policy

The MVP should avoid an unnecessary full relink of AROS.

Therefore AS0/AS1 preserve the existing ABI-visible virtual layout of the normal AROS runtime.

A later protected process or selective Legacy Cell may preserve compatible virtual addresses where necessary.

That does **not** imply that Nexus must grant the same protection or authority to every address space.

The first target is:

```
same virtual address
    !=
same physical mapping or same protection authority
```

Nexus-only pages should be:

- absent from the Cell; or
- mapped supervisor-only only where an unavoidable transition mechanism requires it.

A future high-half or otherwise redesigned Nexus virtual layout is possible, but is not a prerequisite for proving the architecture.

## 7. Page-table memory ownership

Page tables that enforce a protected Nexus boundary must not remain controllable by the ordinary AROS Compatibility Trust Domain allocator.

Long-term rule:

> Nexus page-table pages come from Nexus-owned physical memory.

The early prototype may wrap current allocation code while bootstrapping the split, but this dependency must be removed before L1 isolation is claimed.

Otherwise corruption in the compatibility allocator could corrupt the very structures enforcing a protected boundary.

## 8. Mapping API

The internal Nexus operation should be target-explicit.

Conceptually:

```c
nx_map(
    AddressSpaceHandle as,
    uintptr_t virtual_address,
    MemoryObjectHandle memory,
    uint64_t offset,
    size_t length,
    NexusMapRights rights,
    NexusCacheMode cache_mode
);
```

Rights include at least:

- READ;
- WRITE;
- EXECUTE;
- USER/SUPERVISOR eligibility.

No "current global MMU" is implied.

## 9. MemoryObject relationship

An AddressSpace does not own physical pages merely because they are mapped into it.

Physical/shared memory is represented independently by `NexusMemoryObject`.

This enables:

- same pages at different virtual addresses;
- different rights in different processes;
- zero-copy IPC;
- DMA grants;
- graphics surfaces;
- shared buffers.

Example:

```
MemoryObject M
   |
   +-- process A: 0x400000, read/write
   +-- process B: 0x900000, read-only
   +-- DMA object: device-write
```

## 10. W^X and NX on x86-64

Nexus treats executable permission as real hardware state, not documentation.

### Required work

The x86-64 backend must:

1. detect NX support;
2. enable the architectural NX mechanism before protected domains execute;
3. represent NX in 4 KiB and large-page entries;
4. make `EXECUTE` an explicit mapping right;
5. reject writable+executable mappings by default.

### Default policy

- code: RX;
- mutable data: RW + NX;
- stacks: RW + NX;
- IPC/shared buffers: NX unless explicitly executable;
- page tables: non-user and NX as appropriate.

### Compatibility escape hatch

A Legacy Cell may need selected WX mappings for genuinely incompatible software.

Such mappings must be:

- Cell-local;
- explicit;
- diagnosable;
- excluded from claims of strict W^X for that Cell.

Protected AROS software should not receive WX by default.

## 11. Bootstrap mappings

The current broad bootstrap identity map is treated as temporary bootstrap authority.

It is not the protected runtime policy.

Before an untrusted protected domain starts, Nexus must establish a runtime root with known permissions.

The intended sequence is:

```
firmware/loader
    |
temporary bootstrap mappings
    |
long mode
    |
Nexus early init
    |
construct/activate Nexus runtime AddressSpace
    |
only then start protected domains
```

## 12. CR3 activation

Only the x86-64 Nexus backend performs ordinary runtime CR3 activation.

Conceptual operation:

```c
nx_arch_activate_address_space(as);
```

Responsibilities:

- ensure root is valid;
- update per-CPU current-address-space state;
- update active CPU masks;
- handle pending TLB generation;
- load CR3;
- restore architecture-specific per-domain state where required.

Legacy Exec task switches inside one Legacy Cell do **not** need a CR3 change.

A Nexus switch between different protected AddressSpaces may require one.

Examples include:

- protected AROS process;
- selective Legacy Cell;
- isolated driver/service domain.

Normal Exec Task switches inside one shared compatibility AddressSpace need not change CR3.

## 13. TLB model

The current single-root design can often flush only the local CPU.

That is insufficient when the same AddressSpace is active on multiple Nexus CPUs.

### MVP

For correctness first:

- track which CPUs may be executing an AddressSpace;
- on a mapping/protection change, invalidate locally;
- send a Nexus IPI to other active CPUs;
- wait for acknowledgement where immediate revocation is required.

### Generation model

Each AddressSpace carries a monotonically increasing TLB generation.

Each CPU records the generation it has observed for its current AddressSpace.

This permits deferred flushes where safe and mandatory synchronous shootdown where permissions are being revoked.

### Later optimisation

Possible later work:

- PCID;
- INVPCID;
- batching;
- lazy shootdown;
- large-page optimisation.

None are MVP requirements.

Correctness is.

## 14. SMP rule

Page-table metadata and active-CPU state require Nexus-owned locking.

Exec `Forbid()` or Cell-local spinlocks may not protect Nexus page tables.

The address-space manager therefore uses locks that remain valid independently of ABI v1 scheduler state.

## 15. Page faults

A page fault is first a Nexus protection event.

The handler identifies:

- current Nexus CPU;
- current NexusThread;
- current NexusAddressSpace;
- faulting virtual address;
- access type;
- privilege level;
- present/not-present state.

### Nexus fault

Fault in Nexus privileged code:

- capture diagnostics;
- panic unless an explicitly recoverable kernel mechanism owns the fault.

### Protected AROS process/domain

Fault:

- build process diagnostic;
- terminate or deliver a defined protected-runtime exception;
- keep Nexus running.

### Compatibility Trust Domain / Legacy Cell

For the normal transitional AROS CTD, existing trap behaviour may remain until a stronger boundary is introduced; no containment claim is made beyond the proven level.

For a selective Legacy Cell, the handler distinguishes compatible legacy traps from boundary violations. A fatal Cell protection violation terminates the Cell rather than Nexus.

## 16. Legacy trap forwarding

AROS already maps selected CPU traps into Amiga-style traps.

Nexus should preserve that compatibility where it does not weaken the boundary.

The order becomes conceptually:

```
CPU exception
   |
Nexus trap classification
   |
   +-- Nexus fault -> panic
   |
   +-- protected domain -> domain policy
   |
   +-- Legacy Cell
           |
           +-- compatible legacy trap -> Cell Exec
           |
           +-- protection-boundary fault -> terminate Cell
```

The protection kernel must decide that a fault belongs to the Cell *before* invoking legacy trap semantics.

## 17. MMIO mappings

Device mappings are not ordinary anonymous memory.

A Nexus MMIO mapping carries:

- device authority;
- physical resource range;
- cache mode;
- permitted width/access policy where required;
- owning domain.

A Legacy Cell cannot convert an arbitrary physical address into an MMIO mapping merely by calling an old global-map API.

## 18. Physical-address visibility

ABI v2 should avoid exposing raw physical addresses.

Use:

- MemoryObject handles;
- DMA objects;
- device BAR handles.

Legacy compatibility APIs that return physical addresses must be audited because a physical address is harmless only while the caller lacks a path to arbitrary DMA or mapping authority.

## 19. Address-space destruction

Destroying an AddressSpace requires:

1. prevent new threads from entering it;
2. stop or migrate existing NexusThreads;
3. remove it from active CPU sets;
4. synchronise TLB invalidation as required;
5. revoke mappings/capabilities;
6. release page-table pages;
7. release references to MemoryObjects.

A dead AddressSpace ID/handle must not become valid again through simple pointer reuse.

## 20. First implementation stages

### AS0 — representation only

Wrap the current runtime MMU root in a `NexusAddressSpace` object.

Observable AROS behaviour remains identical.

### AS1 — explicit map/protect API

Route x86-64 mapping and protection changes through an explicit AddressSpace argument internally.

Legacy public APIs remain wrappers.

### AS2 — real executable permission

Implement NX and W^X policy.

### AS3 — second root

Create and activate a second AddressSpace with private code/data/stack.

### AS4 — domain-aware page faults

A fault in the second AddressSpace is contained without system halt.

### AS5 — shared MemoryObject

Map explicit shared pages into two protected spaces with different rights.

AS0-AS5 establish the substrate required for protected AROS execution. A selective Legacy Cell may be introduced later only when a concrete compatibility case justifies it.

## 21. MVP non-goals

The first AddressSpace implementation does not need:

- copy-on-write;
- fork;
- demand paging;
- swap;
- overcommit;
- NUMA policy;
- PCID optimisation;
- file-backed mmap;
- a Unix VM subsystem.

Adding those before the protection model is proven would increase complexity without solving the core Nexus problem.

## 22. Definition of done for P1.1

P1.1 is complete when:

- the existing x86-64 AROS boot uses an explicit `NexusAddressSpace` representation;
- CR3 ownership has one documented internal path;
- existing `KrnMapGlobal/KrnSetProtection` behaviour is preserved for the normal AROS runtime while internal target ownership becomes explicit;
- no ABI v1 structure layout changes;
- reference AROS reaches Wanderer;
- the change is small enough to review independently of later multi-address-space work.
