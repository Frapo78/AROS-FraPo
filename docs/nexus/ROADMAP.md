# Nexus Roadmap

> This roadmap is ordered by architectural dependency, not by visibility to end users.

The roadmap is deliberately incremental. Nexus should never depend on a distant "big rewrite" moment before it becomes useful or testable.

Each major phase should produce something the AROS community can inspect, run, measure and criticise. A phase is not considered successful merely because the code compiles: it should demonstrate a concrete architectural property while preserving the agreed compatibility baseline.

## Roadmap principles

- **Keep AROS alive while changing it.** Every phase should leave a usable reference configuration.
- **Prefer proofs over promises.** A protected address space, contained fault or restartable driver is more valuable than a large speculative framework.
- **Protect compatibility with tests.** ABI v1 behaviour must be measured rather than assumed.
- **Keep upstream in sight.** Localise Nexus changes and avoid unnecessary divergence.
- **Make milestones discussable.** Important design changes should be documented in ADRs before they spread through the tree.
- **Do not confuse modernisation with expansion of scope.** The roadmap should solve architectural blockers first, then broaden hardware and user-facing capabilities.

## Phase 0 — Baseline and guardrails

Goal: make regressions measurable before changing low-level behaviour.

Deliverables:

- freeze the ABI v1 compatibility contract;
- identify the x86-64 boot path from firmware/loader to Exec and Wanderer;
- inventory privileged operations currently performed by Exec, kernel.resource and drivers;
- establish reproducible QEMU boot images;
- capture boot logs and basic performance baselines;
- identify existing SMP, memory, DOS and HIDD tests relevant to Nexus;
- add Nexus-specific CI documentation.

Exit criteria:

- current `pc-x86_64` or `pc-x86_64-smp` can be built reproducibly;
- current system reaches Wanderer in the reference VM;
- baseline tests and boot artefacts are documented.

## Phase 1 — Nexus substrate

Goal: introduce protected primitives without yet moving AROS into a separate cell.

Implement minimal objects:

- AddressSpace
- MemoryObject
- Thread
- Endpoint
- Capability table
- IRQ object
- Timer object

Initial platform: x86-64/QEMU.

Exit criteria:

- create and destroy an isolated address space;
- map/unmap pages with R/W/X permissions;
- enforce W^X for protected mappings;
- create two protected execution contexts;
- send a validated IPC message between them;
- transfer a MemoryObject capability and map the same pages with different permissions;
- invalid capability use fails without corrupting Nexus.

## Phase 2 — Legacy Cell prototype

Goal: move the existing AROS ABI v1 environment behind a protection boundary.

Work:

- define the Legacy Cell bootstrap descriptor;
- assign a private address space to the cell;
- map the memory layout expected by current AROS;
- provide controlled entry points for kernel operations;
- virtualise or proxy privileged CPU operations;
- keep the current Exec scheduler inside the cell for the first implementation.

Exit criteria:

- ABI v1 Exec initializes inside the cell;
- DOS starts;
- existing libraries initialize;
- Wanderer reaches a usable desktop;
- a deliberate invalid access in the cell cannot overwrite Nexus memory;
- cell termination leaves the Nexus kernel alive.

This is the first major architecture milestone.

## Phase 3 — Service boundary and HIDD transport

Goal: make selected system services live outside the Legacy Cell.

Start with services that are easier to virtualise before moving complex physical drivers.

Candidates:

1. monotonic timer/time service;
2. logging/debug service;
3. block-device proxy;
4. simple input channel;
5. framebuffer/surface transport.

Define:

- HIDD proxy transport;
- request/reply format;
- asynchronous completion model;
- shared-memory ring format;
- cancellation and timeout semantics.

Exit criteria:

- at least one unmodified or minimally modified ABI v1 subsystem talks through an HIDD proxy;
- service restart does not require restarting Nexus.

## Phase 4 — Storage isolation

Goal: Nexus owns storage hardware and exposes block services to AROS.

Order:

1. reference virtual block driver under QEMU;
2. AHCI;
3. NVMe.

Work includes:

- DMA MemoryObjects;
- interrupt routing;
- IOMMU abstraction;
- queue ownership;
- block-service protocol;
- legacy device bridge.

Exit criteria:

- AROS boots from storage served across the Nexus boundary;
- storage driver failure is contained;
- on IOMMU hardware, the device cannot DMA outside granted buffers.

## Phase 5 — ABI v2 / ExecNG foundations

Goal: enable genuinely protected native AROS applications.

Initial concepts:

- Process
- Thread
- Port/Endpoint
- Event/Signal
- Library service
- MemoryObject
- Handle
- WaitSet

Design requirement:

The API should feel recognisably Exec-like while never requiring global shared pointers.

Exit criteria:

- native hello-world process;
- two isolated processes exchanging messages;
- shared-memory zero-copy example;
- process crash containment;
- basic debugger/introspection support.

## Phase 6 — DOS NG and unified namespace

Goal: legacy and protected applications see one coherent filesystem and service namespace.

Implement:

- VFS/service broker;
- file handles as capabilities;
- credentials and access checks;
- legacy DOS bridge;
- asynchronous I/O support.

Exit criteria:

- a legacy application and ABI v2 application can operate on the same file;
- neither gains arbitrary access to the other's address space;
- file permissions and credentials are enforced at the service boundary.

## Phase 7 — Network service

Goal: move network ownership outside the Legacy Cell.

Work:

- NIC driver domain;
- packet-buffer MemoryObjects;
- network-stack service;
- ABI v1 bsdsocket bridge;
- ABI v2 socket API;
- IPv4/IPv6 tests.

Exit criteria:

- legacy and native applications can share the network stack;
- stack restart does not restart the desktop;
- malformed remote traffic cannot directly corrupt the Legacy Cell or Nexus.

## Phase 8 — Unified compositor

Goal: preserve Intuition compatibility while enabling a modern display architecture.

Work:

- compositor service;
- surface MemoryObjects;
- damage tracking;
- input routing;
- legacy Intuition surface bridge;
- ABI v2 surface API.

Later capabilities:

- HiDPI;
- multiple displays;
- GPU acceleration;
- animation;
- remote display.

Exit criteria:

- legacy and native windows coexist on one desktop;
- legacy applications require no awareness of the compositor architecture.

## Phase 9 — Driver-domain expansion

Move progressively:

- USB/xHCI;
- audio/AHI backend;
- GPU;
- Wi-Fi/Ethernet;
- additional storage and platform devices.

Every migration must include a crash-containment test.

## Phase 10 — ARM64

Port the Nexus primitive layer, not the Legacy Cell architecture.

Required parity:

- address spaces;
- capabilities;
- IPC;
- IRQ;
- SMP scheduler;
- timers;
- DMA;
- IOMMU where available;
- Legacy Cell boot.

## Phase 11 — RISC-V

Target OpenSBI/UEFI environments already relevant to AROS.

Reach the same kernel primitive contract as x86-64 and ARM64 before adding platform-specific features.

## Phase 12 — Hardening

Required areas:

- ASLR;
- W^X everywhere possible;
- guard pages;
- stack protection;
- capability-generation protection;
- syscall/IPC validation;
- fuzzing;
- fault injection;
- driver restart testing;
- Legacy Cell escape testing;
- IOMMU verification;
- resource exhaustion controls.

## Phase 13 — Migration SDK

Developer-facing tools:

- ABI v1 compatibility analyzer;
- dangerous-pattern scanner;
- ABI v2 headers;
- bridge libraries;
- porting guide;
- examples;
- automated classification of applications as:
  - NG safe
  - NG compatible
  - legacy required
  - privileged legacy

## Development rules

Each phase must:

1. build independently;
2. preserve a usable reference configuration;
3. include a rollback path;
4. include reproducible tests;
5. avoid unrelated refactors;
6. document ABI and security changes through an ADR.

The project must not disappear into a multi-year rewrite branch. The system should remain demonstrably alive after every architectural step.

## Community checkpoints

At the end of each major phase, the project should publish a short checkpoint covering:

- what was demonstrated;
- what changed in the architecture;
- what remained compatible;
- known regressions or limitations;
- benchmark or diagnostic evidence where relevant;
- unresolved questions;
- the next decision that needs community review.

The intention is to make Nexus easy to evaluate from evidence rather than from enthusiasm alone.
