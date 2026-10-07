# Nexus Bootstrap MVP

## Objective

Prove the Nexus protection substrate independently, then use it to run the existing AROS x86-64 ABI v1 environment as a Legacy Cell.

The MVP is intentionally staged.

It must not begin by redesigning:

- Exec;
- DOS;
- Intuition;
- Wanderer;
- POSIX.

The first job is to establish machine ownership and a measurable protection boundary.

## Reference environment

Initial target:

- architecture: x86-64;
- machine: QEMU;
- firmware/boot: simplest current AROS x86-64 path;
- CPU: one Nexus CPU first, SMP later;
- storage: reference virtual storage before physical-driver isolation;
- graphics: existing AROS path during early compatibility work.

QEMU is the reference because repeatability matters more than hardware breadth during architecture proof.

The exact upstream source baseline is recorded in `BASELINE.md`.

## Pre-implementation gates

Before the first MMU refactor:

1. current x86-64 AROS must build reproducibly;
2. the reference VM must reach Wanderer;
3. privilege paths must be classified;
4. kernel.resource / Exec coupling must be inventoried;
5. NX/W^X/page-table/TLB behaviour must be known;
6. a low-level test/boot gate must exist.

These are Phase 0 requirements, not optional documentation work.

## Step A — map the current boot chain

Document exact control and ownership flow for:

1. loader/bootstrap;
2. page-table ownership;
3. `kernel.resource`;
4. `exec.library` initialization;
5. resident/module initialization;
6. DOS startup;
7. graphics/Intuition startup;
8. Wanderer launch.

Deliverable:

`docs/nexus/X86_64_BOOT_MAP.md`

## Step B — AddressSpace representation with no behaviour change

Introduce only the first clean Nexus primitive:

- `NexusAddressSpace`.

Initially it represents the current runtime MMU root.

Requirements:

- existing AROS virtual layout remains unchanged;
- existing ABI v1 behaviour remains unchanged;
- current boot still reaches Wanderer;
- CR3 ownership becomes explicit internally;
- map/unmap/protect code receives an explicit AddressSpace target internally.

This is **AS0/AS1** from `ADDRESS_SPACE_MODEL.md`.

It does not yet prove isolation.

## Step C — real executable protection and fault ownership

Before running a second protected address space:

- enable/use real x86-64 NX where supported;
- make EXECUTE an enforced mapping right;
- default protected writable memory to NX;
- introduce domain-aware fault classification;
- distinguish Nexus faults from protected-domain faults.

Mandatory test:

A deliberate protected-domain protection fault produces diagnostics and returns control to Nexus instead of halting the entire machine.

## Step D — second protected address space

Create a tiny controlled test payload with:

- private code;
- private data;
- private stack;
- separate hardware page-table root.

Nexus must:

- activate the root through its own CR3 path;
- return safely to the original address space;
- prevent cross-space private-memory access;
- perform correct TLB invalidation.

Success means:

> **L1 CPU memory isolation has been demonstrated.**

It does not yet mean hardware or DMA isolation.

## Step E — explicit sharing and IPC

Only after private memory works, introduce the minimum additional primitives needed for a meaningful protected-domain test:

- `NexusMemoryObject`;
- `NexusEndpoint`;
- `NexusCapability`;
- minimum `NexusThread` state required by protected execution.

Two protected contexts must:

- exchange a validated message;
- explicitly share one MemoryObject;
- map it with different permissions;
- fail to access each other's non-shared pages;
- reject invalid/fabricated authority.

This proves that isolation does not require abandoning efficient shared memory.

## Step F — Legacy Cell bootstrap contract

Define a descriptor describing:

- Cell entry point;
- ABI v1 virtual-memory layout;
- boot arguments;
- Legacy vCPU count;
- granted MemoryObjects;
- service endpoints;
- virtual IRQ channels;
- permitted compatibility operations.

The Cell is not allowed to convert descriptor contents into arbitrary Nexus authority.

## Step G — legacy privilege virtualization

Before calling the Cell privilege-isolated, implement the required semantics from `LEGACY_PRIVILEGE_MODEL.md`.

At minimum:

- arbitrary `Supervisor()` cannot jump into Nexus ring 0;
- `SuperState()/UserState()` expose only Cell-compatible state;
- `Disable()/Enable()` operate on virtual interrupt delivery;
- `Forbid()/Permit()` remain Exec-local;
- CR3/IDT/APIC ownership remains Nexus-only.

Success target:

> **L2 privilege isolation** for the tested Cell configuration.

## Step H — bootstrap existing Exec/DOS inside the Cell

Initial strategy:

- retain ABI v1 shared-memory layout inside the Cell;
- keep Exec and DOS largely unchanged;
- keep the current Exec scheduler inside the Cell;
- provide one NexusThread per Legacy vCPU;
- route machine privilege through the Legacy compatibility layer.

Success ladder:

1. Cell entry;
2. ExecBase creation;
3. Exec task switching;
4. DOS initialization;
5. Initial CLI;
6. filesystem/service availability;
7. graphics/Intuition initialization;
8. Wanderer desktop.

Each rung must have a stable, diagnosable checkpoint.

## Wanderer is a compatibility proof, not a security level

A usable Wanderer inside the Cell is a major result.

It must not be described as "fully isolated" if the transitional configuration still permits legacy drivers to control:

- arbitrary MMIO;
- PCI configuration;
- physical IRQs;
- bus-master DMA.

Report the actual isolation level.

For example:

- CPU + privilege boundary working, direct legacy DMA still present → L2;
- hardware ownership mediated → L3;
- IOMMU-controlled DMA → L4.

## Step I — prove containment

Mandatory destructive tests should eventually include:

1. write outside a Cell mapping;
2. execute from an NX mapping;
3. attempt unsupported machine privilege;
4. corrupt a sacrificial Cell-owned page;
5. kill the Legacy Cell;
6. relaunch a Cell where feasible.

Pass condition:

Nexus remains responsive and can diagnose the failed Cell.

## Step J — hardware boundary

Strong containment requires progressively moving hardware authority out of the Cell.

Priorities:

1. timer/event path;
2. reference block service;
3. PCI/MMIO mediation;
4. AHCI/NVMe;
5. USB;
6. network;
7. graphics/audio.

HIDD is used as a compatibility seam, not blindly serialized as an IPC protocol.

## Step K — DMA/IOMMU

When a driver can perform bus-master DMA, CPU page tables alone are insufficient.

For L4:

- Nexus owns IOMMU configuration;
- DMA access is derived from Nexus MemoryObjects;
- drivers receive only device-specific DMA mappings;
- revocation removes device access.

Without usable IOMMU hardware, the reduced isolation level must be reported honestly.

## Step L — SMP

Only after single-vCPU Cell behaviour is stable:

- create multiple Legacy vCPUs;
- bind them to NexusThreads;
- let the existing Exec SMP scheduler schedule legacy Tasks internally;
- validate signalling, locks and task migration;
- validate Nexus TLB shootdown for AddressSpaces active on multiple CPUs.

Nexus must remain able to schedule unrelated protected threads regardless of Cell `Forbid()` state.

## Initial code-location rule

Do not create a second unrelated kernel tree simply because Nexus is conceptually a new kernel layer.

Prefer:

- extracting clean mechanisms from the current kernel/resource boundary;
- isolating Nexus-specific code under clearly named files/directories;
- leaving Exec-specific scheduling logic in the Legacy compatibility side;
- avoiding invasive changes to `rom/exec` during substrate work.

The first implementation should maximize the amount of upstream AROS code that remains mergeable.

## Upstream-sync rule

The fork must remain capable of ingesting upstream AROS changes.

Therefore:

- `master` tracks upstream only;
- Nexus changes live on `nexus/main` and feature branches;
- avoid formatting churn;
- do not rename large existing trees without architectural need;
- prefer adapters/extraction over wholesale rewrites;
- record intentional architectural divergence in ADRs.

## Substrate MVP definition of done

The Nexus substrate MVP is complete when:

- Nexus has an explicit x86-64 AddressSpace abstraction;
- executable permission is hardware-enforced for protected mappings;
- a second protected address space works;
- a deliberate domain fault does not halt Nexus;
- explicit shared MemoryObject mapping works;
- protected IPC/capability validation works;
- all results are reproducible under the reference QEMU configuration.

## Legacy Cell MVP definition of done

The first Legacy Cell MVP is complete when:

- ABI v1 Exec and DOS run inside a Cell;
- Legacy privilege cannot become unrestricted Nexus privilege;
- current Exec task scheduling remains internal to the Cell;
- fatal CPU memory corruption cannot overwrite Nexus;
- Cell failure does not halt Nexus;
- Wanderer can be reached in a documented transitional configuration;
- the milestone states its actual isolation level;
- upstream integration remains manageable.
