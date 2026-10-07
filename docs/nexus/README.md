# Nexus

> **An experimental architecture for evolving AROS without erasing its Amiga identity.**

Nexus is the protected architecture workstream inside AROS-FraPo.

It starts from a simple conviction: AROS should be able to preserve the elegance, responsiveness and programming culture inherited from Amiga while gaining the protection, scalability and hardware model expected from a modern operating system.

This project is motivated by a deep personal passion for Amiga and by respect for the work already done by the AROS community.

Nexus is not an attempt to replace AROS with a Unix-like system. It is an attempt to let AROS grow further as AROS.

## Start here

If you are new to the project, read these in order:

1. [Vision](VISION.md) — why Nexus exists, what it wants to preserve, and the long-term goal.
2. [Architecture](ARCHITECTURE.md) — the convergent AROS/Nexus model and technical invariants.
3. [Convergent Architecture](CONVERGENT_ARCHITECTURE.md) — the detailed three-plane model, U/A/N ownership, service fabric and evolution rules.
4. [ADR-0002](adr/0002-convergent-aros-nexus-architecture.md) — why AROS remains the primary runtime and Nexus becomes the small executive beneath it.
5. [Convergence Risks](CONVERGENCE_RISKS.md) — red-team risk register, trust ratchet and bridgeability failure modes.
5. [Trust and Fault Model](TRUST_MODEL.md) — what Nexus protects and the explicit isolation levels.
6. [Legacy Privilege Model](LEGACY_PRIVILEGE_MODEL.md) — how Supervisor, Disable/Enable and machine privilege must change at the Cell boundary.
7. [Nexus / Exec Split](NEXUS_EXEC_SPLIT.md) — why current kernel.resource is an extraction seam rather than the final Nexus API.
8. [Address-Space Model](ADDRESS_SPACE_MODEL.md) — the first implementation primitive, including NX/W^X, CR3, faults and SMP TLB rules.
9. [Roadmap](ROADMAP.md) — how the work is divided into demonstrable phases.
10. [Baseline](BASELINE.md) — the exact upstream reference state and synchronization policy.
11. [x86-64 Boot Map](X86_64_BOOT_MAP.md) — where the current AROS boot path gives us practical insertion points.
12. [Bootstrap MVP](BOOTSTRAP_MVP.md) — the first implementation proof.
13. [ABI v1 Compatibility Contract](ABI_V1_COMPAT.md) — what Nexus must not casually break.
14. [ADR-0001](adr/0001-two-domain-architecture.md) — why the two-domain decision exists.
15. [Upstream Integration](UPSTREAM_INTEGRATION.md) — U/A/N ownership and continuous upstream intake.
16. [AI and Automation Foundations](AI_FOUNDATIONS.md) — future-ready service/capability foundations without putting AI in the kernel.
17. [Community and participation](COMMUNITY.md) — how to discuss, review and contribute.
18. [CI and validation](CI_STRATEGY.md) — staged build, QEMU and hardware gates.
19. [Review Protocol](REVIEW_PROTOCOL.md) — mandatory three-pass review and red-team process.
20. [Governance](GOVERNANCE.md) — project direction, decision model and contact.
21. [Branch Policy](BRANCH_POLICY.md) — required branch roles and GitHub protection rules.
22. [Tasks](TASKS.md) — current phase status and issue links.

## The idea in one paragraph

AROS remains the primary operating-system runtime. Nexus progressively extracts the small set of privileged machine mechanisms that need modern protection: address spaces, low-level threads, memory objects, capabilities, IRQ/timer ownership, device authority, DMA/IOMMU and fault domains.

Legacy shared-pointer semantics may continue inside ordinary AROS compatibility scope. Protected boundaries are introduced selectively where they provide real value. Legacy Cells remain available as a containment tool, not as the mandatory home of the whole AROS runtime.

## What Nexus is trying to preserve

Nexus explicitly values:

- Exec-style asynchronous messaging;
- Tasks, signals and message ports;
- libraries, devices and resources;
- Intuition;
- BOOPSI/Zune;
- Wanderer;
- asynchronous I/O;
- small system components;
- low conceptual overhead;
- fast startup and responsiveness.

Protected AROS capabilities should evolve those ideas rather than create a parallel Unix-like or ExecNG ecosystem.

## What Nexus is trying to add

The long-term architecture targets:

- x86-64 SMP;
- ARM64;
- RISC-V;
- UEFI;
- NVMe/AHCI;
- USB/xHCI;
- IPv6;
- modern graphics;
- isolated address spaces;
- protected driver domains;
- IOMMU-controlled DMA;
- W^X and ASLR;
- restartable services;
- fault containment.

## Current status

**Stage:** Phase 0 — architectural baseline and guardrails.

Nexus is not yet an implemented execution model.

The current work is intentionally conservative:

- keep an exact upstream baseline;
- map the real AROS boot path;
- establish a reproducible x86-64/QEMU baseline;
- classify privilege and trust boundaries;
- separate current kernel.resource mechanisms from Exec-specific policy;
- audit NX/W^X, page-table ownership and SMP TLB behaviour;
- protect ABI v1 behaviour with tests;
- introduce architectural seams before changing semantics.

The first implementation target is not a new desktop or a new API.

It is a minimal `NexusAddressSpace` abstraction around the current x86-64 MMU path, with **no intended observable change to AROS**.

## Project direction

Nexus is directed by **Francesco Poltero**.

Project contact: **info@francescopoltero.com**

The direction of the project is independent from the official AROS Development Team while remaining intentionally respectful of and continuously informed by upstream AROS work.

See [GOVERNANCE.md](GOVERNANCE.md).

## Engineering pace

Nexus deliberately optimizes for correctness rather than speed.

Every non-trivial code or architecture change requires at least three review passes:

1. correctness and scope;
2. regression/concurrency/upstream integration;
3. adversarial red-team.

Physical-hardware validation is a hard stop when QEMU cannot establish the required property.

See [REVIEW_PROTOCOL.md](REVIEW_PROTOCOL.md) and [CI_STRATEGY.md](CI_STRATEGY.md).

## Branches

- `master` — kept close to upstream AROS for synchronisation.
- `nexus/main` — primary Nexus architecture branch.
- `nexus/bootstrap-x86_64` — historical/bootstrap prototyping line; new substantial work should use focused feature branches from `nexus/main`.

## Relationship with upstream

AROS-FraPo is an experimental fork. Nexus is not presented as an official AROS roadmap.

The fork exists so that a deep architectural direction can be tested without destabilising upstream work.

The intended relationship with the AROS community is constructive:

- keep changes as mergeable as practical;
- reuse existing AROS work;
- avoid gratuitous rewrites;
- publish architectural decisions;
- invite technical criticism;
- upstream generally useful fixes where appropriate;
- let working code and tests decide which ideas survive.

## Project rule

> **AROS remains the system. Nexus modernizes the machine mechanisms beneath it.**

Compatibility remains an AROS contract.

Protection is introduced at explicit boundaries.

The long-term goal is convergence: upstream AROS improvements should flow naturally into Nexus, while Nexus gives AROS stronger low-level capabilities.
