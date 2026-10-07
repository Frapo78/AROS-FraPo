# Convergence Risks and Guardrails

> Status: architecture red-team register
>
> Applies to ADR-0002

## Purpose

The convergent architecture deliberately avoids both a clean-room rewrite and a permanent mandatory Legacy Cell.

That choice reduces duplication but introduces its own failure modes.

This document records those risks so that "staying close to AROS" cannot become an excuse for weak boundaries or uncontrolled technical debt.

## R1 — the Compatibility Trust Domain may remain too powerful

### Risk

During convergence, normal ABI v1 AROS may still share writable system structures and retain historical supervisor/hardware authority.

A protected application can be isolated from another protected application while the broader ABI v1 world is still capable of compromising the machine.

### Guardrail: authority trust ratchet

For every machine authority, track the migration state:

1. **legacy-owned** — current AROS controls it directly;
2. **shared/adapted** — Nexus mechanism exists but trusted AROS compatibility code can still invoke it;
3. **Nexus-owned** — protected/untrusted domains can only request it through a validated Nexus contract.

Once an authority reaches state 3 for a protected deployment mode, that mode must not silently regain a direct legacy bypass.

Examples of authority:

- CR3/page-table mutation;
- physical interrupt flag/control;
- IDT/APIC programming;
- physical-memory mapping;
- PCI configuration;
- MMIO ownership;
- DMA/IOMMU mapping.

The normal compatibility mode may remain less protected, but its active trust level must be visible.

## R2 — direct and isolated implementations can diverge

### Risk

One semantic service with both:

- direct implementation;
- isolated proxy/service implementation;

can become two subtly different APIs.

### Guardrail

Both paths must share:

- one source interface contract where practical;
- one conformance test corpus;
- one versioning policy;
- equivalent error semantics where the boundary permits it.

An isolated path that cannot preserve important semantics should expose that incompatibility explicitly rather than pretend transparency.

## R3 — not every AROS interface is bridgeable

### Risk

AROS APIs may contain:

- arbitrary pointers;
- callbacks/Hooks;
- pointers to pointers;
- shared mutable structures;
- implicit global state;
- lifetime assumptions;
- physical addresses.

Automatically serializing such interfaces would be unsafe.

### Bridgeability classes

Classify interfaces before isolation:

### B0 — direct-only legacy

The interface fundamentally depends on shared pointers/global state and has no safe transparent bridge yet.

### B1 — generated value/handle bridge

Arguments can be represented safely using scalar values, bounded buffers, handles or MemoryObjects.

Good candidate for generator-first proxying.

### B2 — explicit manual bridge

The semantic operation can cross a boundary, but callbacks, structures or lifetime rules need hand-designed translation.

### B3 — protected-native contract

The interface was designed for explicit capabilities/MemoryObjects and is safe as a protected service contract.

Do not force B0/B2 APIs into B1 merely to claim automation.

## R4 — generator infrastructure can become a security vulnerability

### Risk

A code generator can consistently generate the same unsafe mistake across hundreds of interfaces.

### Guardrail

For protected-boundary generation:

- unknown pointer-like types fail closed;
- pointer-to-pointer defaults to unsupported unless explicitly modeled;
- generated buffer lengths require validation;
- capability types are explicit;
- generated code is tested from schema-level negative cases;
- generator source changes receive the same three-pass review as kernel boundary code.

Generated does not mean trusted automatically.

## R5 — U/A/N classification can decay into permanent fork drift

### Risk

Too many files become A-class, with local patches that make each upstream merge harder.

### Guardrail

For each A-class area:

- document the exact seam;
- keep the diff narrow;
- track why U-class is insufficient;
- periodically ask whether upstream changes allow deleting the adapter.

Deletion of obsolete Nexus glue is considered progress.

A future machine-readable ownership manifest may be introduced if manual tracking becomes unreliable.

## R6 — upstream can add a new privilege bypass

### Risk

AROS evolves continuously. A new upstream API or driver path could directly manipulate hardware that Nexus had already begun to control.

### Guardrail

Before merge and during daily upstream review, pay special attention to:

- `rom/kernel`;
- `rom/exec`;
- architecture kernel/exec paths;
- PCI/device/resource APIs;
- DMA;
- MMU;
- interrupt code;
- new HIDD methods carrying physical pointers/authority.

If an upstream feature conflicts with the trust ratchet, adapt the Nexus seam rather than silently accepting a bypass.

## R7 — m68kemu containment is not automatically a security sandbox

### Risk

Upstream `m68kemu.library` uses contained m68k memory, but it forwards many calls into native AROS libraries and implements compatibility behaviours such as Supervisor semantics.

"Contained memory" must not be interpreted as L1-L4 Nexus isolation.

### Guardrail

Treat m68kemu primarily as a compatibility mechanism.

If hostile-m68k containment becomes a goal, measure it separately and place the emulator/native bridge inside an explicit protected domain or Legacy Cell as required.

Do not advertise security properties that upstream m68kemu does not claim.

## R8 — protected AROS applications cannot transparently call every legacy library

### Risk

A protected application may call an ABI v1 library whose API expects shared pointers or writable global structures.

Trying to make this transparent can recreate the shared-address-space problem.

### Guardrail

Protected applications use only:

- B1/B2 bridges that have been validated;
- B3 protected-native services;
- explicitly trusted direct libraries mapped into the same trust domain.

Unsupported crossings fail explicitly.

The protected AROS API should grow from proven bridgeable services rather than promise universal compatibility on day one.

## R9 — Nexus generic abstractions may be accidentally x86-shaped

### Risk

AddressSpace, IRQ or Thread APIs designed only from x86-64 may later fit ARM64/RISC-V poorly.

### Guardrail

Do not freeze public Nexus ABI from the first x86 implementation.

Keep early Nexus contracts internal and versionable until:

- x86-64 proof exists;
- at least one second architecture is reviewed;
- architecture-specific concepts are clearly separated.

## R10 — AI scope can distract from the operating-system core

### Risk

"AI-native" language can drive premature work on models, brokers or accelerator APIs before memory protection and service contracts work.

### Guardrail

AI remains a later optional consumer of general mechanisms.

No Phase 0-5 milestone is blocked by AI features.

The system must remain fully functional with no AI subsystem installed.

## R11 — selective isolation can become selective security theatre

### Risk

The project may isolate easy components while leaving the most dangerous machine authority in the compatibility world.

### Guardrail

Track security progress by extracted authority and L0-L5 evidence, not by number of services moved out of process.

A tiny isolated utility does not compensate for unrestricted DMA or supervisor access elsewhere.

## R12 — convergence can become architectural ambiguity

### Risk

If every subsystem is allowed to choose arbitrary direct/isolated/legacy behaviour, the system may become impossible to reason about.

### Guardrail

Each boundary decision must state:

- trust domain;
- U/A/N ownership;
- bridgeability class;
- direct versus isolated deployment;
- authority granted;
- isolation level claimed;
- tests proving the claim.

The number of deployment modes should be kept as small as compatibility and hardware diversity permit.

## Review rule

This risk register is living documentation.

A red-team finding that reveals a new architecture-level failure mode should be added here or supersede the relevant ADR.

The purpose is not to prove ADR-0002 perfect.

It is to make its failure modes visible early enough to change direction.
