# Nexus Bootstrap MVP

## Objective

Prove that the existing AROS x86-64 environment can eventually execute as an unprivileged Legacy Cell above a minimal Nexus substrate.

The MVP is intentionally narrow. It must not start by redesigning the desktop, DOS, Intuition or Exec.

## Reference environment

Initial target:

- architecture: x86-64
- machine: QEMU
- firmware/boot: use the simplest existing AROS x86-64 path first
- CPU: start with one Nexus CPU, then enable SMP
- storage: virtual reference device before physical-driver extraction
- graphics: existing AROS path until a surface proxy is introduced

QEMU is the reference because repeatability matters more than hardware breadth during the architecture proof.

## Step A — map the current boot chain

Document exact call/ownership flow for:

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

No code restructuring should begin until this map identifies which component currently owns privileged CPU state at each step.

## Step B — introduce Nexus types without behavioural change

Create an internal experimental namespace for:

- `NexusAddressSpace`
- `NexusMemoryObject`
- `NexusThread`
- `NexusEndpoint`
- `NexusCapability`

At this stage, wrappers may map onto existing primitives.

Requirement:

The normal AROS boot must remain unchanged.

Purpose:

Create seams before moving ownership.

## Step C — page-table ownership

Move authoritative page-table manipulation behind Nexus functions.

Required primitives:

- create address space;
- destroy address space;
- map pages;
- unmap pages;
- change page protection;
- activate address space;
- query mapping for diagnostics.

Tests:

- RW page;
- RO page;
- NX page;
- deliberate write to RO;
- deliberate execute from NX;
- address-space separation.

## Step D — protected test payload

Before putting Exec inside a cell, run a tiny protected payload.

Payload A and B must:

- have separate page tables;
- communicate through a Nexus endpoint;
- share one MemoryObject explicitly;
- fail to access each other's private memory.

This isolates Nexus bugs from AROS compatibility bugs.

## Step E — Legacy Cell bootstrap descriptor

Define a structure describing:

- cell entry point;
- virtual-memory layout;
- boot arguments;
- vCPU count;
- granted MemoryObjects;
- service endpoints;
- allowed privileged operations.

The descriptor is consumed by Nexus, not trusted as arbitrary executable authority.

## Step F — bootstrap existing AROS inside the cell

Initial strategy:

- keep ABI v1 memory layout where required;
- keep Exec and DOS largely unchanged;
- proxy the minimum privileged operations necessary to boot;
- retain the existing Exec scheduler inside the cell;
- allocate one Nexus thread per Legacy vCPU.

The first success point is not Wanderer.

Success ladder:

1. Exec init message;
2. Exec task switching;
3. DOS init;
4. filesystem available;
5. graphics init;
6. Intuition init;
7. Wanderer desktop.

Each rung must have a stable checkpoint.

## Step G — prove containment

Mandatory destructive tests:

1. write outside a cell mapping;
2. execute an invalid privileged operation;
3. corrupt a sacrificial cell-owned page;
4. kill the Legacy Cell;
5. restart or relaunch a cell where feasible.

Pass condition:

Nexus remains responsive and can emit diagnostics after cell failure.

## Step H — SMP

Only after the single-vCPU Legacy Cell is stable:

- create multiple Legacy vCPUs;
- bind them to Nexus threads;
- allow the current Exec SMP scheduler to use them;
- validate signalling, scheduler locks and task migration.

Nexus must remain able to schedule native protected threads concurrently.

## Initial code-location rule

Do not create a second unrelated kernel tree until the boot map proves it necessary.

Prefer initially:

- extending the existing x86-64 kernel/resource boundary;
- isolating Nexus-specific code under clearly named files/directories;
- avoiding invasive changes to `rom/exec`.

The first implementation should maximize the amount of upstream AROS code that remains mergeable.

## Upstream-sync rule

The fork must remain capable of ingesting upstream AROS changes.

Therefore:

- Nexus-specific changes should be localized;
- avoid formatting churn;
- do not rename large existing trees without a concrete architectural need;
- prefer adapters over wholesale rewrites;
- record every intentional divergence in an ADR.

## MVP definition of done

The bootstrap MVP is complete when all are true:

- Nexus owns the relevant x86-64 protection state;
- an isolated test payload works;
- AROS ABI v1 boots as a Legacy Cell;
- Wanderer becomes usable;
- deliberate Legacy Cell memory failure does not overwrite Nexus;
- the same branch can still be rebased or merged against upstream with manageable conflicts;
- the boot procedure and tests are reproducible.
