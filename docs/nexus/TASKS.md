# Nexus Tasks

GitHub Issues are currently disabled for this repository, so Phase 0 tracking lives here until issue tracking is enabled.

## Phase 0 — Baseline and guardrails

### P0.1 — x86-64 boot map
Status: **draft complete**

Deliverable: `docs/nexus/X86_64_BOOT_MAP.md`

Trace loader/bootstrap, MMU/page tables, kernel.resource, Exec, DOS, graphics/Intuition and Wanderer.

### P0.2 — Reproducible QEMU baseline
Status: **todo**

Document exact target, configure/build commands, boot artefacts, QEMU invocation and success markers.

### P0.3 — Privileged-operation inventory
Status: **todo**

Inventory CR3/page tables, APIC/IOAPIC, privileged instructions, physical mappings, PCI, DMA, timers and reboot/power paths.

### P0.4 — Regression/test inventory
Status: **todo**

Identify tests that protect ABI v1 behaviour and the low-level paths Nexus will touch.

### P0.5 — Baseline diagnostics
Status: **todo**

Capture reference serial/debug boot logs and lightweight boot/performance metrics.

## Phase 1 preparation

### P1.1 — Internal Nexus object model
Status: **blocked by Phase 0**

Specify internal interfaces for AddressSpace, MemoryObject, Thread, Endpoint and Capability.

### P1.2 — Protected payload experiment
Status: **blocked by P1.1**

Run two isolated x86-64 payloads with explicit IPC and a shared MemoryObject.

## Tracking rule

When GitHub Issues are enabled, migrate each task into an issue while keeping this file as the high-level status index.
