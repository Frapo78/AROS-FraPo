# Nexus CI and Validation Strategy

> Status: Phase 0 design
>
> Tracking issue: #15

## Purpose

Nexus changes will touch code where a successful compile is not sufficient evidence.

The validation strategy is staged and deliberately conservative.

## Gate G0 — repository sanity

Cheap checks that should run on every Nexus push and pull request:

- required architecture documents exist;
- local Markdown links in `docs/nexus` resolve;
- project metadata files remain internally consistent;
- inherited source-hygiene checks continue to run.

Workflow:

`.github/workflows/nexus-project-sanity.yml`

This gate is intentionally independent of the AROS toolchain.

## Gate G1 — reference x86-64 build

Before P1.1 implementation is merged, establish a reproducible build for the recorded baseline.

The build record must include:

- host distribution/version;
- dependency list;
- configure command;
- compiler/toolchain version;
- build command;
- resulting boot artifacts.

Target:

`pc-x86_64`

Do not expand to a target matrix until this gate is reliable.

## Gate G2 — QEMU boot smoke

The first runtime gate boots the generated image under a fixed QEMU configuration.

Capture:

- QEMU version;
- machine type;
- CPU model/count;
- RAM;
- firmware/BIOS choice;
- disk/ISO arguments;
- serial/debug output.

The smoke test needs deterministic milestones.

Initial markers should correspond to existing boot stages:

1. kernel entry;
2. Exec initialization;
3. DOS/Initial CLI;
4. Startup-Sequence;
5. Wanderer usable.

Prefer existing diagnostic output over permanent Nexus-only logging added purely for CI.

## Gate G3 — protection tests

Once P1 begins, add targeted runtime tests for:

- read/write protection;
- NX execution fault;
- address-space separation;
- controlled CR3 activation;
- domain-aware page fault handling;
- MemoryObject rights;
- invalid capability use.

A test is successful only if the expected protection failure is contained and Nexus remains responsive.

## Gate G4 — SMP correctness

After single-CPU correctness is stable:

- run the reference image with multiple vCPUs;
- exercise AddressSpace activation on more than one CPU;
- validate remote TLB shootdown;
- validate scheduler/interrupt interaction;
- rerun protection-fault tests under SMP.

Performance tuning comes after correctness.

## Gate G5 — hardware validation

Some claims cannot be established safely in QEMU alone.

Examples:

- real IOMMU behaviour;
- PCIe/NVMe DMA isolation;
- interrupt-remapping behaviour;
- chipset-specific APIC/IOMMU behaviour;
- real USB/xHCI timing;
- graphics hardware;
- firmware-specific UEFI behaviour.

When a roadmap step reaches this point, automated development must stop before claiming completion.

The project should then produce a hardware-validation checklist containing:

- exact commit SHA;
- build artifact;
- hardware requirements;
- test steps;
- expected output;
- recovery procedure;
- risks.

Work resumes only after the real-hardware result is recorded.

## Review gate

CI success never replaces review.

Every code or architecture change follows the mandatory review protocol in `REVIEW_PROTOCOL.md`.

In particular, a change may not be treated as ready merely because G0-G4 pass.

## Upstream comparison gate

Before modifying a subsystem:

1. inspect the current upstream AROS version of that subsystem;
2. compare it with the Nexus baseline;
3. identify relevant upstream commits since the recorded baseline;
4. integrate or account for community changes before building a competing solution.

This check is repeated before merge if upstream changed during development.

## Failure policy

A failing protection test is not fixed by weakening the expected security property without an architectural review.

A failing compatibility test is not fixed by silently redefining ABI v1 behaviour.

A hardware-dependent uncertainty is not resolved by assuming QEMU behaviour matches physical hardware.

When evidence is insufficient, the milestone remains open.
