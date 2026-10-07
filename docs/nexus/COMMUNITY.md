# Nexus and the AROS Community

Nexus is meant to be discussed in public.

A project that touches the execution model, memory protection, drivers, ABI compatibility and the long-term direction of AROS should not be developed as a private redesign and presented only after the important decisions are already fixed.

The purpose of this fork is to create a place where those ideas can be made concrete, tested and challenged.

## What kind of feedback is useful

The most useful feedback is specific and technical.

Examples:

- a compatibility assumption that the architecture has missed;
- an AmigaOS or AROS behaviour that a Legacy Cell would break;
- an existing AROS mechanism that can solve a problem more cleanly;
- a security boundary that is too weak;
- an IPC design that would add too much latency;
- an SMP assumption that will not scale;
- a driver/HIDD interaction that cannot be proxied as proposed;
- a simpler route to the same result;
- a measurable regression;
- a test case that should become part of the compatibility corpus.

Strong disagreement is welcome when it helps make the design better.

## What Nexus is not asking the community to accept on faith

The project does not assume that:

- every architectural proposal is correct;
- Legacy Cells are the final implementation in every detail;
- every driver should immediately become a separate process;
- a new ABI should replace ABI v1;
- existing AROS development should stop while Nexus is explored;
- a large rewrite is justified merely because modern operating systems do something differently.

Every major architectural decision should be supported by code, tests or a clear technical argument.

## Development style

The project aims to work in small, reviewable steps.

A good Nexus change should ideally:

1. solve one architectural problem;
2. minimise unrelated changes;
3. preserve upstream compatibility where practical;
4. include a reproducible test or observable checkpoint;
5. state which compatibility level it affects;
6. update the relevant ADR when it changes architecture.

The project deliberately rejects a multi-year "everything will work when the rewrite is finished" approach.

AROS should remain bootable and understandable throughout the work.

## Areas where contributors can help

Nexus will need more than kernel code.

Useful areas include:

### AROS and Amiga compatibility

- Exec semantics;
- DOS;
- Intuition;
- BOOPSI;
- Zune/MUI;
- legacy software behaviour;
- m68k compatibility;
- device and library ABI details.

### Kernel and architecture

- x86-64 MMU;
- ARM64;
- RISC-V;
- SMP;
- scheduling;
- exception handling;
- page-table design;
- capability systems;
- IPC;
- IOMMU.

### Hardware and drivers

- PCI/PCIe;
- NVMe;
- AHCI;
- USB/xHCI;
- audio;
- Ethernet/Wi-Fi;
- graphics;
- DMA;
- firmware and UEFI.

### Tooling and quality

- QEMU automation;
- CI;
- regression testing;
- fuzzing;
- static analysis;
- performance tracing;
- compiler/runtime work;
- documentation.

## How to participate

For now:

- use GitHub Issues for concrete technical topics;
- keep broad architecture discussion linked to the relevant Nexus document or ADR;
- open small pull requests where possible;
- include reproduction steps for regressions;
- distinguish observed behaviour from proposed behaviour.

If a discussion changes an architectural invariant, it should result in a new or superseding ADR rather than silently changing assumptions in code.

## Upstream respect

The AROS Development Team and contributors have already solved an enormous number of portability and compatibility problems over many years.

Nexus should build on that knowledge, not behave as though the project is starting from zero.

When the fork discovers a fix that is useful independently of Nexus, upstreaming it should be considered.

When upstream changes improve the same area, Nexus should prefer integrating them rather than maintaining a competing implementation without reason.

## Personal motivation

I am pursuing this because I care deeply about Amiga and about the ideas that made it different.

That passion is the reason to be ambitious, not the reason to be careless.

If Nexus succeeds, it should succeed because the architecture proves that Amiga-like ideas can still be technically strong on modern hardware — not because we lower the standard by which the system is judged.

## A useful standard for every proposal

When evaluating a Nexus change, ask four questions:

1. **Does it preserve something valuable about AROS/Amiga?**
2. **Does it remove a real limitation on modern hardware or software?**
3. **Can it be tested rather than merely argued?**
4. **Can the system remain usable while we get there?**

If the answer to those questions is yes, the idea is probably worth exploring.
