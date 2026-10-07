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

Goal: make regressions and protection assumptions measurable before changing low-level behaviour.

Deliverables:

- freeze the ABI v1 compatibility contract;
- record the exact upstream implementation baseline;
- identify the x86-64 boot path from firmware/loader to Exec and Wanderer;
- inventory privileged operations currently performed by Exec, kernel.resource and drivers;
- define the trust/fault model and isolation levels;
- define how legacy privilege is virtualised;
- classify the current kernel.resource / Exec coupling;
- audit x86-64 NX/W^X, page-table ownership, CR3 and SMP TLB semantics;
- establish reproducible QEMU boot images;
- capture boot logs and basic performance baselines;
- identify existing SMP, memory, DOS and HIDD tests relevant to Nexus;
- establish the minimum Nexus CI/QEMU implementation gate.

Exit criteria:

- current `pc-x86_64` can be built reproducibly from the recorded baseline;
- current system reaches Wanderer in the reference VM;
- privilege paths are classified;
- the first Nexus primitive can be implemented without importing undefined Exec policy;
- x86-64 MMU gaps are explicitly known;
- baseline tests and boot artefacts are documented;
- a low-level Nexus change cannot be accepted on compilation alone.

## Phase 1 — Nexus substrate

Goal: introduce protection primitives without yet moving AROS into a Legacy Cell.

Initial platform: x86-64/QEMU.

### Phase 1A — Address-space seam

- introduce an architecture-neutral `NexusAddressSpace`;
- wrap the current runtime MMU root without intended behaviour change;
- make runtime CR3 ownership explicit;
- route mapping/protection changes through an explicit target internally.

Gate:

- existing AROS reaches Wanderer unchanged.

### Phase 1B — Executable permission and faults

- implement real x86-64 NX handling;
- enforce W^X by default for protected mappings;
- classify faults by Nexus domain;
- keep Nexus alive after an expected protected-domain fault.

Gate:

- deliberate write/execute protection violations produce controlled domain failure.

### Phase 1C — Multiple address spaces

- create a second runtime root;
- map private code/data/stack;
- switch through Nexus-owned CR3 activation;
- implement correct local/remote TLB invalidation semantics.

Gate:

- private pages are inaccessible across spaces;
- **L1 CPU memory isolation** is demonstrated.

### Phase 1D — Explicit sharing and IPC

Introduce the minimum additional objects:

- MemoryObject;
- Endpoint;
- Capability;
- minimal NexusThread representation required by the test payload.

Gate:

- two protected execution contexts exchange a validated message;
- the same MemoryObject is mapped with different rights;
- fabricated/invalid authority does not expose unrelated memory.

IRQ, Timer, Device and DMA objects follow only when required by the next boundary rather than being created speculatively.

## Phase 2 — Legacy Cell prototype

Goal: move the existing AROS ABI v1 environment behind a real CPU/privilege boundary while preserving its internal shared-memory model.

Work:

- define the Legacy Cell bootstrap descriptor;
- assign a private address space to the Cell;
- map the memory layout expected by current AROS;
- provide a Legacy kernel compatibility layer above Nexus;
- virtualise `Supervisor()`, `SuperState()/UserState()` and `Disable()/Enable()`;
- retain `Forbid()/Permit()` and the current Exec scheduler inside the Cell;
- provide controlled virtual IRQ/event delivery;
- keep physical CR3/IDT/APIC ownership in Nexus.

Exit criteria:

- ABI v1 Exec initializes inside the Cell;
- DOS starts;
- privilege virtualization cannot enter unrestricted Nexus supervisor state;
- a deliberate CPU memory violation in the Cell cannot overwrite Nexus memory;
- a fatal Cell fault does not halt Nexus;
- the highest demonstrated isolation level is reported explicitly.

### Transitional Wanderer milestone

Reaching Wanderer inside the Legacy Cell is a major compatibility proof, but **not automatically a full hardware-isolation proof**.

If legacy drivers still directly control MMIO, PCI or unrestricted DMA, the milestone must be labelled with the actual isolation level (for example L1/L2).

This prevents desktop success from being confused with completion of the security architecture.

## Phase 3 — Service boundary and HIDD transport

Goal: begin reaching **L3 hardware isolation** by moving selected machine-facing services outside the Legacy Cell.

HIDD remains a strategic compatibility seam, but existing HIDD calls are not treated as IPC wire formats. Proxies translate pointer-rich legacy interfaces into explicit Nexus protocols.

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
