# Nexus Bootstrap MVP

## Objective

Prove that Nexus mechanisms can be extracted beneath the existing AROS runtime without first moving AROS into a permanent compatibility container.

The MVP is intentionally conservative:

- keep AROS booting normally;
- preserve ABI v1 behaviour;
- extract one machine mechanism at a time;
- add protection only after the seam is reproducible.

The governing direction is ADR-0002.

## Reference environment

Initial target:

- architecture: x86-64;
- machine: QEMU;
- one CPU first, SMP later;
- normal AROS boot/runtime path;
- current upstream-compatible graphics/storage path.

The exact reproducible source baseline is recorded in `BASELINE.md`.

## Pre-implementation gates

Before the first MMU refactor:

1. x86-64 AROS builds reproducibly;
2. the reference VM reaches Wanderer;
3. privilege paths are classified;
4. kernel.resource / Exec coupling is inventoried;
5. NX/W^X/page-table/TLB behaviour is known;
6. G1/G2 build and QEMU gates exist;
7. the touched subsystem has been compared with current upstream;
8. its U/A/N ownership is understood.

## Step A — map existing ownership

Maintain the x86-64 boot map from loader through Wanderer.

For each low-level step distinguish:

- AROS policy;
- machine mechanism;
- current shared implementation.

## Step B — AddressSpace representation with no behaviour change

Introduce `NexusAddressSpace` around the current runtime MMU root.

Requirements:

- existing AROS virtual layout unchanged;
- current ABI unchanged;
- normal AROS boot reaches Wanderer;
- ordinary runtime CR3 ownership becomes explicit;
- internal map/protect operations gain an explicit AddressSpace target.

This proves a seam, not isolation.

## Step C — real page protection

Add separately reviewable protection semantics:

- NX where supported;
- supervisor write protection where compatible;
- explicit R/W/X;
- observable failure when protection cannot be applied.

Do not combine this with a large scheduler or Exec rewrite.

## Step D — domain-aware faults

Classify faults before forwarding them into higher-level AROS semantics.

A controlled protected-context fault must produce diagnostics without halting Nexus/the whole machine.

## Step E — second protected context

Create a tiny test execution context with:

- private AddressSpace;
- private code/data/stack;
- Nexus-owned activation path.

Prove:

- private memory is inaccessible from the wrong space;
- the fault is contained;
- L1 CPU memory isolation is real for the tested configuration.

## Step F — explicit shared memory

Introduce the minimum `MemoryObject` mechanism.

Map the same object intentionally into two protected contexts with different rights.

This proves that protection and zero-copy sharing can coexist.

## Step G — first generated contract experiment

Before building a broad IPC/service framework, select one small AROS interface and test the generator-first strategy.

Goal:

```
existing AROS interface description
        |
        +--> direct stub
        +--> validation metadata
        +--> optional Nexus proxy
```

Avoid complex graphics/storage callback interfaces for the first proof.

## Step H — protected AROS application proof

Add protected execution as an AROS capability.

A small AROS program should be able to:

- run in a protected AddressSpace;
- call selected AROS services through validated adapters;
- coexist with normal ABI v1 software;
- appear as part of the same AROS system.

The exact public ABI remains experimental until this proof exists.

## Step I — selective service isolation

Choose a component where isolation has measurable value.

Prove:

- direct path remains available;
- isolated path uses the same semantic contract;
- failure can be contained/restarted;
- overhead is measured.

## Legacy Cell rule

A full Legacy Cell is **not** a prerequisite for the normal MVP.

Use one only when a concrete compatibility case requires containing a shared-pointer/legacy-privilege environment as a unit.

If introduced, its own privilege and isolation requirements remain governed by:

- `LEGACY_PRIVILEGE_MODEL.md`;
- `TRUST_MODEL.md`;
- ADR-0001 invariants as refined by ADR-0002.

## m68k rule

Do not build a parallel Nexus m68k translator during the MVP.

Use upstream `m68kemu.library` as the primary compatibility path.

Changes should preferably improve or extend that contract rather than create a second launcher/runtime.

## Performance rule

Do not introduce an IPC crossing merely because Nexus has an Endpoint primitive.

Prefer direct execution until a protection boundary gives a measurable benefit.

Use MemoryObjects and batching for large/high-frequency data.

## Hardware stop rule

When the next claim depends on real:

- IOMMU/DMA;
- PCIe/NVMe;
- interrupt remapping;
- USB/xHCI;
- firmware/chipset;
- GPU;

stop the dependent roadmap chain and prepare a real-hardware validation package.

## Substrate MVP definition of done

The first convergent Nexus substrate is proven when:

- current AROS still boots normally;
- AddressSpace ownership is explicit;
- R/W/X protection is real;
- a protected fault is contained;
- a second AddressSpace works;
- explicit shared MemoryObject mapping works;
- all results are reproducible under reference QEMU;
- upstream remains integrable with narrow A-class diffs.

## Convergence MVP definition of done

The first architecture-level convergence proof is complete when:

- one protected AROS application coexists with normal ABI v1 software;
- one interface has demonstrated generated direct/validated transport forms;
- no duplicate Exec/runtime ecosystem is required;
- m68k compatibility remains upstream-owned;
- performance and compatibility results are documented.
