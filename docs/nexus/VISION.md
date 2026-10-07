# Nexus Vision

## Why I am doing this

Nexus starts from a personal motivation: a deep and long-standing passion for Amiga.

What made Amiga special was never only the hardware, Workbench, or nostalgia. It was the coherence of the whole system: small, responsive, understandable, message-driven and unusually direct.

AROS has kept much of that culture alive while doing something even harder: making the model open, portable and capable of evolving across very different hardware.

I believe that work deserves to go further.

Nexus is not an attempt to replace AROS with Linux, BSD, Windows, macOS or a new unrelated hobby operating system.

The goal is to help AROS become a stronger modern operating system while remaining recognizably AROS.

## The central question

> Can the strongest Amiga and AROS ideas remain first-class system concepts while the operating system gains modern protection, multicore scalability, current hardware support and room for future computing models?

Nexus exists to test whether the answer can be yes.

## The refined thesis

The project began by separating a Legacy Domain from a Protected Domain.

That distinction remains useful as a **safety contract**, but further analysis changed an important conclusion:

> AROS itself should not be trapped permanently behind a compatibility layer.

AROS should remain the primary runtime.

Nexus should become the small privileged executive beneath it.

That means:

- preserve and evolve Exec rather than replace it with a parallel ecosystem;
- reuse DOS, Intuition, Zune, Wanderer, HIDD, AHI, Poseidon, AROSTCP and other AROS work;
- extract modern machine mechanisms from current low-level AROS code rather than rewrite the system from zero;
- introduce protection selectively where it produces real value;
- keep compatibility mechanisms close to upstream AROS so they improve as AROS improves.

This is the convergent architecture defined by ADR-0002.

## What should remain unmistakably Amiga/AROS

Nexus explicitly values:

- asynchronous message passing;
- Tasks and lightweight execution;
- signals/events;
- message ports;
- libraries;
- devices;
- resources;
- asynchronous I/O;
- Intuition;
- BOOPSI/Zune;
- Wanderer;
- fast startup;
- small components;
- low conceptual overhead;
- application interoperability.

These are not cosmetic compatibility features.

They are design ideas worth carrying forward.

## What must change

Some historical assumptions are no longer acceptable as system-wide invariants:

- unrestricted shared kernel-visible pointers;
- arbitrary supervisor entry;
- global interrupt control by applications;
- unrestricted physical-memory access;
- unrestricted DMA;
- one implicit address space;
- weak fault containment;
- security depending on every component behaving correctly.

Nexus isolates those assumptions without declaring the Amiga programming model obsolete.

## AROS first, Nexus underneath

The intended relationship is:

```
applications
    |
AROS runtime
Exec / DOS / Intuition / HIDD / m68kemu / ...
    |
stable Nexus contracts
    |
Nexus Executive
CPU / memory / protection / IRQ / DMA / capabilities
    |
hardware
```

This is deliberately not a deep stack of compatibility personalities.

Most of the operating system remains AROS.

Nexus concentrates only the mechanisms that need stronger ownership and protection.

## Compatibility should improve with upstream

Current upstream AROS already contains an important example of the direction Nexus should follow.

`m68kemu.library` transparently executes classic m68k software using:

- contained m68k memory;
- CPU emulation;
- fake Amiga library bases;
- LVO interception;
- generated thunks;
- generated shadow-structure translation;
- forwarding to native AROS libraries.

Nexus should not duplicate this with a fork-specific "Rosetta".

It should help that upstream mechanism become faster, safer and more complete.

The ideal long-term property is:

> when AROS compatibility improves upstream, Nexus benefits automatically.

## Generated adaptation instead of permanent glue

AROS already has strong interface-generation traditions:

- FD files;
- `genmodule`;
- module `.conf` files;
- HIDD/OOP interface definitions;
- m68k thunk generation;
- structure-layout generation.

Nexus should build on those.

Where possible, one semantic interface description should drive:

- direct native calls;
- compatibility thunks;
- validated service stubs;
- optional isolated transports.

This reduces the risk that Nexus becomes a second implementation that slowly drifts away from AROS.

## Modernity without cultural erasure

Nexus aims to give AROS native mechanisms for:

- x86-64 SMP;
- ARM64;
- RISC-V;
- UEFI;
- modern storage;
- USB/xHCI;
- IPv6;
- current graphics stacks;
- isolated address spaces;
- W^X and ASLR;
- controlled device authority;
- IOMMU-mediated DMA;
- restartable services;
- fault containment.

Those mechanisms should belong to AROS as capabilities of the system, not as a foreign kernel hidden underneath a themed desktop.

## Selective isolation, not isolation theatre

Not every function call needs IPC.

Not every driver needs to be moved out of process immediately.

Nexus should be:

> local where trust and performance justify it; isolated where containment materially helps.

A service may use a direct path today and an isolated path tomorrow while preserving one semantic contract.

Claims about security remain evidence-based through the L0-L5 isolation model.

## A future-ready system

Nexus should also avoid making today's workload assumptions permanent.

AI and agent systems are one example.

The project will not put an LLM in the kernel.

Instead it should provide general mechanisms that are useful whether AI is important or not:

- asynchronous services;
- scoped capabilities;
- shared MemoryObjects;
- service discovery;
- generic compute acceleration;
- structured application automation.

This can eventually support AI agents safely while also strengthening normal scripting and application interoperability.

The spiritual precedent is closer to message ports and ARexx than to embedding a chatbot into the desktop.

## Relationship with upstream AROS

AROS-FraPo is an experimental fork.

Nexus is not an official AROS roadmap.

The project should remain constructive toward the AROS Development Team:

- continuously inspect upstream;
- keep `master` close to upstream;
- prefer upstream code;
- keep adapted diffs narrow;
- contribute generally useful fixes upstream where practical;
- avoid duplicate compatibility stacks;
- revise Nexus when upstream provides a better solution.

If Nexus becomes difficult to update from AROS, that is an architectural warning, not merely a Git problem.

## What success looks like

A successful Nexus should eventually make all of these statements true:

- current AROS keeps evolving rather than being frozen as a guest;
- classic Amiga software continues to become more compatible;
- Exec remains central;
- protected applications become possible;
- faults can be contained selectively;
- drivers can be isolated where worthwhile;
- modern storage/network/graphics remain native AROS citizens;
- x86-64, ARM64 and RISC-V share the same protection concepts;
- large transfers remain efficient;
- upstream updates remain manageable;
- future automation and AI services can use explicit authority rather than global access;
- the system remains small enough to reason about.

The goal is not simply "AROS with memory protection".

The goal is:

> **an AROS architecture capable of another generation of growth without losing the engineering culture that made Amiga systems distinctive.**

## Architecture must remain revisable

This vision is a direction, not a demand that every mechanism imagined in 2026 survive unchanged.

Fine tuning is expected.

Larger changes are acceptable when evidence requires them.

The project should be willing to:

- move a boundary;
- remove an abstraction;
- replace a mechanism;
- adopt better upstream work;
- reject an earlier Nexus idea.

What should remain stable is the intent:

> **Preserve the strongest Amiga/AROS ideas. Modernize the mechanisms that limit them. Stay close enough to upstream that AROS and Nexus can grow together.**
