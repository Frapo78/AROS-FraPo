# Nexus CI and Validation Strategy

> Status: Phase 0 implementation
>
> Tracking issue: #15

## Purpose

Nexus changes touch code where compilation is not sufficient evidence.

Validation is staged, falsifiable and resource-aware.

The project deliberately separates cheap checks that should run often from expensive QEMU/hardware evidence that should run only when it answers a concrete question.

## Gate G0 — repository sanity

Cheap checks for ordinary Nexus pushes/PRs:

- required architecture/process files exist;
- local Markdown links resolve;
- shell syntax is valid;
- agent/process contract self-test passes;
- baseline harness synthetic self-test passes;
- QEMU resource-policy self-test passes;
- inherited source-hygiene checks continue to run.

Workflow:

`.github/workflows/nexus-project-sanity.yml`

G0 is intentionally independent of the full AROS cross-toolchain build.

## Gate G1 — reference x86-64 build

G1 builds:

`pc-x86_64`

through the upstream AROS build path using the Nexus baseline wrapper.

The evidence record includes:

- exact source SHA;
- clean/dirty state;
- upstream build/toolchain source identities;
- GCC/binutils versions;
- host/compiler identity;
- build configuration;
- generated cross-compiler/linker hashes;
- ISO size and SHA-256.

A successful compile is G1 evidence.

It does not by itself advance the tested Nexus baseline.

## Gate G2 — QEMU runtime evidence

QEMU is used as a controlled virtual-hardware laboratory.

It is **not** run indiscriminately.

### Resource policy

The default GitHub Actions policy is:

- no automatic `push` QEMU workflow;
- no automatic `schedule`;
- no automatic run for every PR `synchronize`;
- no broad matrix;
- one vCPU;
- one reference CPU/machine configuration;
- hard workflow timeout;
- hard guest-marker timeout;
- concurrency cancellation for obsolete runs;
- short evidence retention;
- no ISO upload by default.

Normal PR QEMU is limited to relevant low-level paths and to PR lifecycle points such as:

- opened/reopened while non-draft;
- explicitly marked ready for review.

If commits are added after an accepted QEMU run, rerun only when the task/review requires fresh runtime evidence, using `workflow_dispatch`.

The goal is to spend GitHub-hosted compute when it can falsify a meaningful claim.

Workflow:

`.github/workflows/nexus-qemu.yml`

### G2a — early x86-64 kernel serial checkpoint

Initial deterministic marker:

`AROS64 - The AROS Research OS`

This marker already exists upstream in x86-64 kernel startup.

A G2a PASS proves only:

- the G1-bound ISO was accepted;
- QEMU executed the image under the recorded configuration;
- boot reached the x86-64 kernel far enough to emit the existing kernel banner to captured serial output.

It does **not** prove:

- Exec completion;
- DOS/Initial CLI;
- Startup-Sequence;
- Wanderer;
- SMP correctness;
- memory isolation;
- privilege isolation;
- DMA isolation;
- real-hardware behavior.

Marker mode must:

- have a strict timeout;
- fail if QEMU exits before the marker;
- fail if the marker is absent;
- stop QEMU once the requested checkpoint is observed;
- record a distinct `marker-reached` final state.

This avoids burning QEMU runtime after the evidence needed by the test already exists.

### G2b — Exec/DOS checkpoint

Future, only after G2a is reliable.

Prefer existing upstream diagnostic output.

Do not add permanent Nexus-only kernel logging merely to satisfy CI unless separately justified.

### G2c — desktop/Wanderer checkpoint

Future.

A deterministic guest-side checkpoint is preferred over a human screenshot for automated CI.

Human visual evidence may remain useful for manual baseline work but is not an unattended CI oracle.

### G2d — SMP QEMU

Future and task-driven.

Only add multi-vCPU runs when an SMP/concurrency claim requires them.

Do not turn SMP counts into a default PR matrix.

### G2e — emulated-device tests

Future and selective.

Possible targets include:

- AHCI/NVMe;
- xHCI;
- NICs;
- UEFI.

Each device test must justify the extra compute by a specific acceptance criterion.

## GitHub-hosted QEMU evidence

The first GitHub Actions QEMU job:

- installs the dependency list currently used by upstream AROS Linux CI plus QEMU;
- builds a diagnostic x86-64 ISO;
- validates the build manifest/ISO provenance;
- runs one headless TCG QEMU instance;
- waits for the G2a marker;
- uploads only logs/manifests with short retention.

The ISO is not uploaded by default.

The workflow run is tied to the GitHub commit/PR identity and the run manifest records the actual QEMU binary identity.

## Gate G3 — protection tests

Once P1 begins, add targeted runtime tests for:

- read/write protection;
- NX execution fault;
- address-space separation;
- controlled CR3 activation;
- domain-aware page fault handling;
- MemoryObject rights;
- invalid capability use.

A protection test passes only if the expected violation occurs and the required containing context remains alive.

G3 does not automatically require a large QEMU matrix.

Start with the smallest configuration capable of falsifying the invariant.

## Gate G4 — SMP correctness

After single-CPU protection behavior is stable:

- exercise more than one vCPU;
- validate remote TLB shootdown;
- validate scheduler/interrupt interaction;
- repeat protection-fault tests under SMP.

Performance tuning comes after correctness.

## Gate G5 — hardware validation

Some claims cannot be established safely in QEMU alone.

Examples:

- real IOMMU behavior;
- PCIe/NVMe DMA isolation;
- interrupt remapping;
- chipset-specific APIC/IOMMU behavior;
- real USB/xHCI timing;
- graphics hardware;
- firmware-specific UEFI behavior;
- power/resume.

When a roadmap step reaches this point, dependent development stops before claiming completion.

Produce a hardware-validation package containing:

- exact commit SHA;
- build artifact;
- hardware requirements;
- test steps;
- expected output;
- recovery procedure;
- risks.

Work resumes only after real-hardware evidence is recorded.

## Evidence classification

Typical mapping:

- G0 → E1/E2;
- G1 → build evidence, not a runtime isolation level;
- G2 deterministic marker → E4 for that exact marker;
- cross-architecture repetition → E5;
- physical hardware → E6.

A higher evidence class does not broaden the scope of the claim.

For example:

> E4 evidence for `AROS64 - The AROS Research OS`

does not mean:

> E4 evidence that AROS reached Wanderer.

## Review gate

CI success never replaces review.

Every non-trivial change follows `REVIEW_PROTOCOL.md` and `VERIFICATION_MODEL.md`.

Kernel/MMU/protection changes remain H1 even when G0-G4 pass.

## Upstream comparison gate

Before modifying a subsystem:

1. inspect current upstream AROS;
2. compare it with the tested Nexus baseline;
3. identify relevant upstream changes;
4. integrate/account for them before local implementation.

Repeat before merge if upstream moved.

## Failure policy

A failing runtime test is not fixed by weakening the expected property without architectural/review justification.

A missing marker is not converted into PASS because QEMU remained alive.

A hardware-dependent uncertainty is not resolved by assuming QEMU matches physical hardware.

When evidence is insufficient, the milestone remains open.

## Compute-budget rule

GitHub-hosted QEMU usage should remain intentionally small.

Before adding a new automatic QEMU invocation ask:

1. Which falsifiable claim does this run test?
2. Can an existing run produce the same evidence?
3. Can a cheaper E1-E3 test reject the bug first?
4. Does this need to run for every relevant PR or only on demand?
5. Can the VM stop earlier once the required marker is observed?

If those questions do not justify the cost, do not add the run.
