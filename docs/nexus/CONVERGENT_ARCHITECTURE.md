# Convergent Architecture

> Status: architectural baseline
>
> Decision: ADR-0002

## 1. Purpose

The convergent architecture is the current Nexus direction.

Its goal is to make AROS materially more modern without creating a second operating system beside it.

The architecture therefore has one central rule:

> **AROS remains the system runtime. Nexus becomes the small privileged executive beneath it.**

This is intentionally different from both:

- a full AROS-in-a-VM/Legacy-Cell model;
- a clean-room Nexus kernel with AROS reduced to a compatibility personality.

The project instead evolves the existing AROS stack around one stable protection boundary.

## 2. Three planes, not a layer cake

Nexus is organized into three major planes.

### Application plane

Contains:

- native AROS applications;
- classic Amiga m68k applications through upstream compatibility;
- future protected applications;
- POSIX applications;
- future automation/AI clients.

### AROS runtime plane

Contains the identity and most semantics of the operating system:

- Exec;
- DOS;
- Intuition;
- Zune;
- Wanderer;
- graphics;
- AHI;
- Poseidon;
- AROSTCP;
- OOP/HIDD;
- m68kemu;
- libraries, devices and resources.

### Nexus executive plane

Contains only machine-level protection mechanisms:

- CPU;
- Thread;
- AddressSpace;
- MemoryObject;
- Endpoint;
- Capability;
- IRQ;
- Timer;
- Device authority;
- DMA/IOMMU authority;
- domain-aware fault handling.

The hardware sits directly beneath Nexus.

## 3. Stable boundary: mechanism below, policy above

The most important long-term separation is not "legacy versus new".

It is:

### Nexus mechanism

Examples:

- activate an AddressSpace;
- schedule a protected Thread;
- map a MemoryObject;
- deliver an IRQ;
- create a DMA mapping;
- revoke a Capability;
- classify a fault.

### AROS policy

Examples:

- choose which Exec Task runs;
- implement Forbid/Permit;
- define DOS process semantics;
- decide library/device lifecycle;
- expose Intuition and Wanderer behaviour;
- manage application-level resources.

This separation allows AROS policy to evolve upstream without forcing the low-level Nexus substrate to follow every internal representation change.

## 4. Exec remains central

The project does not create a mandatory parallel ExecNG runtime.

Exec remains the central AROS programming model.

New protected capabilities should appear through:

- additive APIs;
- versioned interfaces;
- protected variants;
- internal Nexus adapters.

The strongest Amiga ideas remain first-class:

- asynchronous message passing;
- signals/events;
- libraries;
- devices;
- resources;
- lightweight tasks;
- explicit I/O;
- low conceptual overhead.

Historical implementation assumptions are preserved only where they remain useful.

## 5. Extraction strategy

Nexus is built by extraction, not wholesale replacement.

For every subsystem:

1. identify machine mechanism;
2. identify AROS/Exec policy;
3. separate them behind the smallest useful internal contract;
4. keep current behaviour unchanged;
5. add stronger protection only after the seam is proven.

Example:

```
current code:
Exec Task + scheduler + IPI + context switch

target:
Exec scheduler policy
        |
   thin adapter
        |
Nexus Thread / CPU mechanism
```

The same method applies to:

- MMU;
- IRQ;
- timers;
- hardware ownership;
- DMA;
- fault handling.

## 6. U / A / N ownership model

Every significant area should be classified before deep modification.

### U — Upstream-owned

Prefer to consume almost unchanged.

Typical candidates:

- DOS;
- Intuition;
- Zune;
- Wanderer;
- m68kemu;
- applications;
- many HIDD implementations;
- AROSTCP.

### A — Adapted

Upstream code with a deliberately narrow Nexus seam.

Typical candidates:

- selected Exec internals;
- kernel.resource;
- architecture startup;
- selected HIDD entry points;
- selected driver glue.

### N — Nexus-owned

New substrate mechanisms.

Typical candidates:

- AddressSpace;
- Capability;
- MemoryObject;
- Endpoint;
- domain fault ownership;
- DMA/IOMMU authority.

The classification is stored in design/review notes and may change as upstream evolves.

## 7. Service fabric

AROS already uses interfaces, libraries, devices and HIDD/OOP.

Nexus should turn those existing descriptions into a transport-neutral service fabric rather than invent another unrelated API universe.

A semantic service contract may support two execution paths:

### Direct path

```
caller -> direct implementation
```

Used when:

- latency matters;
- the code is trusted;
- isolation adds little value.

### Isolated path

```
caller -> generated proxy -> Nexus Endpoint -> service domain
```

Used when:

- fault containment matters;
- authority must be restricted;
- restartability matters;
- the driver/parser is high risk.

The API contract should remain as similar as possible across both modes.

## 8. Generator-first interfaces

Bridge drift is one of the largest long-term risks.

Nexus therefore prefers extending existing AROS generators before creating hand-maintained adapters.

Inputs may include:

- `.conf` module/interface descriptions;
- FD files;
- NDK prototypes;
- HIDD/OOP interface metadata;
- structure-layout metadata.

Potential generated outputs:

- direct stubs;
- validation metadata;
- Nexus proxy stubs;
- Nexus service dispatch;
- ABI conversion thunks;
- documentation/tests.

Generation does not eliminate security checks.

A generated boundary must still reject:

- invalid capabilities;
- untrusted raw pointers;
- out-of-range buffers;
- malformed structures.

## 9. Compatibility architecture

Compatibility should be attached to AROS, not placed between AROS and Nexus as a permanent global layer.

### Native AROS ABI v1

Continues to run through the normal AROS runtime.

Where legacy shared-pointer semantics prevent strong isolation, Nexus may use selective containment.

### m68k Amiga software

Primary path:

`m68kemu.library` from upstream AROS.

Nexus should preserve its transparent launch model and help strengthen:

- generated thunk coverage;
- shadow structure translation;
- containment;
- optional future JIT/DBT;
- test coverage.

Nexus should not create a competing translator by default.

### Hardware-dependent classic software

May still require a stronger sandbox/emulation environment.

That is a specialized fallback, not the normal compatibility path.

## 10. Legacy Cells are optional containment units

Legacy Cells remain part of the toolbox.

Possible uses:

- software requiring dangerous historical privilege;
- risky legacy components;
- compatibility test environments;
- failure containment;
- per-application legacy sandboxing.

The normal AROS runtime does not have to live permanently inside one.

This reduces:

- permanent IPC cost;
- duplicate scheduler hierarchy;
- bridge count;
- upstream maintenance burden.

## 11. Protected execution evolves inside AROS

Protected processes should be introduced as an AROS capability.

A future protected application should still be recognizably an AROS application.

The long-term system may support both:

- classic shared AROS execution;
- protected AROS execution.

The exact API is intentionally not frozen yet.

The architecture only fixes the safety rule:

> a protected boundary cannot depend on arbitrary cross-domain raw pointers.

## 12. Performance model

Nexus follows several performance rules.

### No mandatory IPC for trusted local paths

Do not pay a protection-boundary cost where no useful boundary exists.

### Zero-copy for large data

Use MemoryObjects for:

- graphics;
- audio;
- network buffers;
- storage;
- compute;
- AI tensors.

### Batch where possible

Boundary crossings should support:

- batched I/O;
- ring buffers;
- shared queues;
- asynchronous completion.

### Keep the TCB small

Smaller privileged code means:

- fewer locks;
- fewer attack surfaces;
- easier review;
- easier architecture ports.

## 13. Portability

The Nexus object model must remain architecture-neutral.

Architecture backends implement:

- x86-64;
- ARM64;
- RISC-V;
- future targets.

AROS platform work should continue to flow upstream.

Nexus should avoid putting x86-specific assumptions into the generic contract.

## 14. Upstream change flow

The intended loop is:

```
upstream AROS changes
        |
        v
impact classification
   |       |       |
   U       A       N
   |       |       |
import   inspect   usually unaffected
        adapter
```

See `UPSTREAM_INTEGRATION.md`.

This is a fundamental architectural requirement, not merely a repository-management preference.

## 15. AI and automation readiness

AI support is not part of the kernel TCB.

The architecture prepares for it through normal system mechanisms:

- message-based services;
- scoped capabilities;
- MemoryObjects;
- generic compute acceleration;
- automation/service discovery.

See `AI_FOUNDATIONS.md`.

## 16. Evolution policy

The architecture is intentionally strong in principles and flexible in mechanics.

Stable principles include:

- AROS remains primary;
- Nexus stays small;
- machine mechanism is separated from AROS policy;
- protected boundaries reject implicit raw-pointer authority;
- upstream reuse is preferred;
- generated bridges are preferred over duplicated manual glue.

Open questions include:

- exact protected application API;
- exact service transport;
- which drivers should be isolated first;
- whether a future JIT backend belongs in upstream m68kemu;
- final compute/AI service APIs;
- final scheduler integration.

Those questions should be answered by evidence, not prematurely frozen.

## 17. Success criteria

The architecture is working if:

- upstream AROS changes remain routinely integrable;
- most user-visible AROS code remains upstream-owned;
- Nexus-specific divergence concentrates in low-level mechanisms;
- protection can be added selectively without duplicating APIs;
- m68k compatibility follows upstream improvements;
- new hardware and CPU targets do not require redesigning the whole runtime;
- AI/automation can be added as services without enlarging the kernel TCB;
- the system remains fast enough to preserve the Amiga expectation of responsiveness.


## 18. Trust ratchet

Convergence must reduce privileged authority over time rather than merely add abstractions.

For each machine authority, the migration should move from:

```
legacy-owned
    ↓
shared/adapted
    ↓
Nexus-owned for protected modes
```

Once a protected deployment relies on Nexus ownership of an authority, that deployment must not silently regain a direct legacy bypass.

The normal ABI v1 Compatibility Trust Domain may remain less protected during migration; its actual trust level must be stated honestly.

## 19. Bridgeability

Not every AROS interface can cross a protection boundary transparently.

Interfaces are classified as:

- **B0** — direct-only legacy;
- **B1** — generated value/handle bridge;
- **B2** — explicit manual bridge;
- **B3** — protected-native contract.

Pointer-rich/callback-heavy APIs must not be forced into a generated IPC form simply to preserve superficial transparency.

See `CONVERGENCE_RISKS.md`.

## 20. Known-risk discipline

ADR-0002 is not treated as risk-free.

The project maintains `CONVERGENCE_RISKS.md` as a living adversarial register covering:

- transitional compatibility privilege;
- direct/isolated semantic drift;
- unsafe generation;
- adapter growth;
- upstream bypasses;
- m68kemu security assumptions;
- protected/legacy API crossing;
- portability;
- AI scope;
- selective-isolation failure modes.

A new red-team finding may change the architecture through a later ADR.
