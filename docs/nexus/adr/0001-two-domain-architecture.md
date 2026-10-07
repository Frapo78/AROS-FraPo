# ADR-0001: Two-domain architecture

- Status: Accepted
- Date: 2026-10-07
- Scope: Nexus architecture

## Context

AROS inherits an Amiga-style execution model in which tasks may share an address space, exchange pointers and rely on system structures that are globally visible.

Modern operating-system requirements include:

- per-process memory isolation;
- multicore scalability;
- driver fault containment;
- IOMMU-controlled DMA;
- restartable services;
- W^X;
- ASLR;
- support for current x86-64, ARM64 and RISC-V systems.

Trying to impose all of those requirements directly on the ABI v1 execution model creates an irreducible conflict: a raw pointer cannot simultaneously be freely meaningful across tasks and be invalid across protected address spaces.

## Decision

Nexus adopts two execution domains:

1. a Legacy Domain in which ABI v1 semantics remain valid;
2. a Protected Domain using isolated address spaces, capabilities and explicit memory sharing.

The Legacy Domain executes inside one or more Legacy Cells.

A Legacy Cell is unprivileged relative to Nexus.

Communication across protection boundaries uses validated IPC, capabilities and MemoryObjects, never untrusted raw pointers.

## Consequences

Positive:

- ABI v1 can remain compatible;
- Nexus can provide real process isolation;
- legacy failure can be contained at cell level;
- driver isolation can be introduced incrementally;
- ABI v2 can evolve without rewriting legacy applications;
- POSIX can be layered above protected primitives rather than dictating the kernel design.

Costs:

- bridge code is required at domain boundaries;
- some operations gain IPC overhead when crossing domains;
- debugging spans two execution models;
- hierarchical scheduling is initially more complex;
- a Legacy Cell can still suffer internal corruption because its shared-memory semantics are intentionally preserved.

## Rejected alternatives

### Protect every existing Exec task independently

Rejected because ABI v1 permits pointer sharing and depends on globally visible structures.

### Keep one global address space and add permissions

Rejected as insufficient for strong fault isolation and modern security.

### Rewrite AROS as a Unix-like kernel

Rejected because it abandons the core architectural identity Nexus is intended to preserve.

### Run all of AROS as a conventional virtual machine

Rejected as the final architecture because it treats AROS as a guest rather than an integrated operating-system personality and complicates unified services. Virtualisation remains useful as a development technique and reference model.

## Invariant

No future optimization may collapse the Legacy and Protected memory-safety contracts into one implicit shared-address-space contract.

Changing this decision requires a superseding ADR with a demonstrably equivalent solution for both binary compatibility and hardware-enforced isolation.
