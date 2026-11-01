# x86-64 Boot Map for Nexus

> Status: Phase 0 source inventory; historical topology sections reconciled with ADR-0002 on 2026-11-01
>
> Reference source: current AROS upstream used by the fork at the start of Nexus work.

This document maps the native x86-64 source path from Multiboot entry to Wanderer and identifies candidate Nexus seams. **The boot chain is a source inventory, not proof that the current `nexus/main` reaches Wanderer.** PR #24 demonstrated an early serial marker only. All proposed seams below follow ADR-0002: normal AROS stays the primary runtime; a full Legacy Cell is not a prerequisite.

## 1. Boot chain summary

```
GRUB / Multiboot 1 or 2
        |
        v
kernel_bootstrap                 arch/all-pc/bootstrap/bootstrap.c
        |
        v
__bootstrap()
  parse Multiboot
  collect modules/memory map
  setup_mmu()
        |
        v
32-bit bootstrap identity map   arch/x86_64-pc/bootstrap/cpu.c
        |
        v
LoadKernel()
        |
        v
kick()
  load GDT
  CR4.PAE
  CR3 = bootstrap PML4
  EFER.LME
  CR0.PG|PE
  long-mode far jump
        |
        v
start64()                       arch/x86_64-pc/kernel/kernel_startup.c
        |
        v
core_Kick()
        |
        v
kernel_cstart()
  relocate boot data
  build GDT/TSS/IDT/TLS
  rebuild/load MMU
  create memory headers
  create ExecBase
  protect selected pages
  InitCode(RTF_SINGLETASK)
  PlatformPostInit()
  leave supervisor ring
  InitCode(RTF_COLDSTART)
        |
        v
exec.library second init        rom/exec/exec_init.c
  complete bootstrap Task
  create CPU context
  install Exec interrupt servers
  Permit()
  Enable()
  multitasking starts
        |
        v
dosboot resident                rom/dosboot/*
        |
        v
dosboot_BootStrap()
        |
        v
InitResident("dos.library")     rom/dos/dos_init.c
        |
        v
CliInit()
        |
        v
Boot Mount / initial CLI        rom/dos/cliinit.c + rom/dos/boot.c
        |
        v
S:Startup-Sequence              workbench/s/Startup-Sequence
        |
        v
SYS:System/Wanderer/Wanderer
```

## 2. Multiboot entry and 32-bit bootstrap

Primary file:

- `arch/all-pc/bootstrap/bootstrap.c`

The Multiboot entry is `kernel_bootstrap`.

Before entering C code it:

- establishes a temporary stack;
- clears direction state;
- executes `cli`;
- masks the legacy PIC;
- jumps to `__bootstrap()`.

`__bootstrap()` then:

- parses Multiboot v1 or v2;
- discovers kickstart modules;
- builds the boot taglist;
- invokes `setup_mmu()`;
- calculates kickstart placement;
- loads/links the kernel modules with `LoadKernel()`;
- completes the boot taglist;
- calls `kick(kentry, km)`.

### Nexus relevance

This layer is still a loader/bootstrap environment. It should remain as small as possible.

For the first Nexus implementation it can remain responsible for reaching long mode, while authoritative runtime address-space ownership moves into Nexus immediately after kernel entry.

## 3. Bootstrap MMU and transition to long mode

Primary file:

- `arch/x86_64-pc/bootstrap/cpu.c`

`setup_mmu()` creates:

- GDT;
- PML4;
- PDP;
- 2 MiB PDE identity mappings.

The current bootstrap creates a very broad identity map, up to 512 GiB, partly to cope with firmware framebuffers and high MMIO placement.

Important current property:

- bootstrap PML4/PDP/PDE entries are writable;
- they are also marked user-accessible;
- executable access is broadly allowed.

This is suitable for bootstrapping, not for the final Nexus protection model.

`kick()` performs the actual architectural transition:

1. validates long-mode support;
2. loads GDT;
3. enables PAE;
4. writes bootstrap PML4 to CR3;
5. sets EFER.LME;
6. enables paging/protected mode;
7. far-jumps into the 64-bit kernel entry.

### Nexus seam N0

The first hard architectural seam is immediately after long-mode entry.

Nexus should eventually take ownership of:

- CR3 and page-table roots;
- user/supervisor page permissions;
- executable permissions;
- kernel mapping lifetime.

The bootstrap may create temporary mappings. Phase 1 should first make the current AROS runtime address-space root explicit without moving AROS into a Legacy Cell.

## 4. 64-bit kernel entry

Primary file:

- `arch/x86_64-pc/kernel/kernel_startup.c`

Entry sequence:

`start64()` -> `core_Kick()` -> `boot_start()` -> `kernel_cstart()`.

`core_Kick()`:

- enables the x86-64 SSE state required by the ABI;
- clears kernel BSS;
- switches to a kernel boot stack;
- calls the target C routine.

`boot_start()` initializes the early console and enters `kernel_cstart()`.

## 5. kernel_cstart(): current ownership centre

`kernel_cstart()` is the most important current Nexus insertion point.

Before Exec is operational it already owns or constructs:

- boot-memory allocator state;
- boot tag relocation;
- APIC base discovery;
- BSP TLS;
- GDT;
- TSS;
- supervisor stacks;
- IDT;
- MMU page tables;
- physical-memory discovery;
- MemHeaders.

The current flow then calls:

`core_SetupMMU(&__KernBootPrivate->MMU, memtop, maptop)`.

## 6. Current x86-64 runtime MMU model

Primary file:

- `arch/x86_64-pc/kernel/mmu.c`

The current runtime setup constructs another large identity map using:

- one PML4 root;
- PDP entries;
- 2 MiB PDEs;
- a small pool of 4 KiB PTE tables for page splitting.

The initial identity mappings are intentionally broad:

- present;
- read/write;
- user-accessible;
- executable.

Later, selected areas are tightened by `core_ProtKernelArea()`.

Current examples in `kernel_cstart()`:

- page zero is blocked from user access;
- kickstart code is made read-only.

This means AROS already has useful page-protection machinery, but the dominant runtime model is still one shared address space.

### Nexus seam N1

Do not initially replace every MMU helper.

First introduce an ownership layer around the existing machinery:

```
bootstrap temporary MMU
        |
        v
Nexus address-space manager
        |
        +-- current AROS runtime address space (AS0)
        |
        +-- later: explicit protected test address space (AS1)
        |
        +-- optional selective Legacy Cell only if justified
```

The first Nexus prototype should reuse low-level x86 page-table encoding where practical while removing the assumption that one PML4 is the system's only runtime context.

## 7. ExecBase creation

Files:

- `rom/kernel/prepareexecbase.c`
- `rom/exec/exec_init.c`

`kernel_cstart()` creates MemHeaders and calls:

`krnPrepareExecBase(ranges, mh, BootMsg)`.

That function:

1. scans ROMTags;
2. finds `exec.library`;
3. directly invokes its early init entry;
4. receives the initial `ExecBase`;
5. publishes the resident-module list in `SysBase->ResModules`.

The first invocation of Exec init is special: when `origSysBase == NULL`, it only constructs the initial ExecBase.

### Nexus seam N2 — preserve Exec initialization

This is a critical **compatibility boundary**, not a mandatory Legacy Cell
creation point. Under ADR-0002, the initial implementation preserves
`krnPrepareExecBase()`, its ordering and the ordinary AROS runtime memory
layout. First make MMU-root ownership explicit beneath AROS (AS0); only later
introduce separately tested protected contexts. Selective Legacy Cells are
optional and require a concrete compatibility justification.

## 8. Resident initialization and privilege transition

After initial ExecBase construction the current kernel:

- builds the ROM header;
- creates SMP scheduling data when enabled;
- transfers remaining MemHeaders to Exec;
- calls `InitCode(RTF_SINGLETASK, 0)` while still privileged;
- runs `PlatformPostInit()`;
- explicitly drops to user mode with `krnLeaveSupervisorRing()`;
- calls `InitCode(RTF_COLDSTART, 0)`.

This is important because the code already contains a conceptual privilege transition before normal Exec startup.

### Nexus seam N3

Nexus should preserve the visible ordering but redefine the authority model.

RTF_SINGLETASK code must be audited because some residents currently rely on supervisor-level access. Each such dependency must eventually be classified as:

- Nexus core functionality;
- driver/service-domain functionality;
- an explicitly audited legacy privilege dependency;
- obsolete historical assumption.

## 9. Exec becomes a scheduler

On the second invocation of `exec.library` initialization:

- a bootstrap `Task` is allocated;
- `KrnCreateContext()` creates CPU context storage;
- an ETask is attached;
- Exec interrupt servers are allocated and installed;
- nesting counts are initialized;
- `Permit()` is called;
- `Enable()` enables Exec interrupts;
- platform-specific init runs.

At this point classic Exec multitasking is operational.

### Nexus initial scheduling strategy

Do not rewrite this path for the MVP.

Exec continues scheduling normal AROS Tasks in the unchanged runtime for the first extraction. Any future protected execution or selective Legacy Cell must be separately justified and tested; neither is required for the initial AS0 seam.

## 10. DOS bootstrap

Important files:

- `rom/dosboot/dosboot_init.c`
- `rom/dosboot/bootstrap.c`
- `rom/dos/dos_init.c`

`dosboot.resource`:

- opens expansion.library;
- scans bootable media;
- selects a boot node;
- optionally displays the boot menu;
- loops until a boot succeeds.

The direct DOS path finds `dos.library` as a resident and calls `InitResident()`.

`DosInit()`:

- creates `dos.library` if needed;
- initializes RootNode and DOS structures;
- opens required libraries/devices;
- initializes filesystem support;
- calls `CliInit(NULL)`.

On successful boot, `RemTask(NULL)` removes the bootstrap caller and scheduling continues.

## 11. Initial CLI and Startup-Sequence

Files:

- `rom/dos/cliinit.c`
- `rom/dos/boot.c`

`CliInit()` creates the "Boot Mount" process and runs the boot handler.

The generic DOS boot sequence eventually opens:

- `S:Startup-Sequence`

and runs the initial shell synchronously with that script as its input.

This gives Nexus a clean higher-level checkpoint:

> DOS is operational when the Initial CLI can execute S:Startup-Sequence.

## 12. Wanderer launch

Primary file:

- `workbench/s/Startup-Sequence`

The standard script performs system assigns, loads classes and stacks, mounts drivers, configures preferences and executes user startup.

Near the end it checks:

`WANDERER:Wanderer`

where:

`WANDERER:` is assigned to `SYS:System/Wanderer`.

It then starts Wanderer directly.

Therefore the initial Nexus compatibility success ladder is:

1. long-mode entry;
2. explicit AS0 ownership seam (future, not yet implemented);
3. initial ExecBase;
4. Exec task switching;
5. dosboot;
6. dos.library;
7. Initial CLI;
8. S:Startup-Sequence;
9. Intuition/graphics usable;
10. Wanderer desktop.

## 13. First implementation boundary

The strongest first implementation point is between current x86-64 kernel setup and initial ExecBase creation.

We should avoid starting by modifying:

- Wanderer;
- Intuition;
- DOS APIs;
- message ports;
- existing application ABI.

Instead, Phase 1 should make this possible:

```
current bootstrap
      |
      v
64-bit entry
      |
      v
Nexus initialization
      |
      +--> AS0: unchanged AROS runtime
      |         Exec/DOS/Intuition/Wanderer
      |
      +--> later AS1: minimal protected test context
```

## 14. Immediate technical work derived from this map

### N1. Address-space root abstraction

Replace direct assumptions around the single `__KernBootPrivate->MMU` runtime root with an internal object representing a page-table context.

No ABI-visible behaviour changes yet.

### N2. Explicit CR3 ownership

All runtime CR3 switches must have one owner/API.

### N3. Mapping API split

Separate:

- kernel-global mappings;
- protected-process mappings;
- optional selective Legacy Cell mappings, only if introduced;
- device/MMIO mappings.

### N4. Privilege audit

Audit every RTF_SINGLETASK resident and every path that assumes ring-0 access.

### N5. Protected context without relocating Exec

After AS0, protection and fault gates, run a minimal second protected context while normal Exec stays in place. Do not require or imply a wholesale Exec relocation into a Legacy Cell.

## 15. Key finding

The present code already contains more of the required separation machinery than a clean-room redesign would suggest:

- an explicit 32-bit bootstrap versus 64-bit kernel boundary;
- boot-time versus runtime page tables;
- GDT user/supervisor segments;
- a deliberate transition out of supervisor mode before COLDSTART;
- page-level protection helpers;
- kernel.resource as the low-level API boundary;
- Exec initialization occurring only after low-level memory/platform setup.

For Nexus this means the safest strategy is **extraction and ownership hardening**, not wholesale replacement.
