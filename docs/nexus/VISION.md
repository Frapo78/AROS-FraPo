# Nexus Vision

## Why I am doing this

Nexus starts from a very personal motivation: a deep and long-standing passion for the Amiga.

What made the Amiga special was never just nostalgia, custom chips, or the look of Workbench. It was the feeling that the whole machine had been designed as a coherent system: small, responsive, understandable, message-driven, and remarkably elegant for its time.

AROS has kept a large part of that architectural culture alive while doing something even more ambitious: making it portable, open, maintainable and capable of evolving beyond the original hardware.

I believe that work deserves to go further.

My goal with Nexus is not to turn AROS into Linux, BSD, Windows or macOS. It is to explore whether the strongest ideas of the Amiga model can survive as first-class ideas in a genuinely modern operating system.

That means taking the Amiga philosophy seriously enough to preserve it — and taking modern hardware seriously enough not to pretend that the constraints of the late 1980s are still acceptable system-wide.

## The central question

Nexus is built around one question:

> Can we preserve one of the leanest and most elegant desktop operating-system architectures of the 1980s and 1990s, while making it work sensibly on x86-64 multicore, ARM64, RISC-V, UEFI, NVMe, modern USB, IPv6, current graphics hardware and modern security expectations?

I believe the answer can be yes, but only if compatibility and protection stop being forced into the same memory model.

## The thesis

Classic Amiga/AROS software expects a world built around:

- Exec Tasks;
- shared structures;
- message ports;
- signals;
- libraries;
- devices;
- resources;
- direct pointer exchange;
- Intuition;
- BOOPSI/Zune;
- DOS processes.

Those assumptions are valuable for compatibility and simplicity, but some of them conflict directly with:

- per-process address spaces;
- fault isolation;
- driver isolation;
- IOMMU-controlled DMA;
- modern privilege separation;
- W^X;
- ASLR;
- scalable multicore execution.

Nexus does not try to make one model pretend to be the other.

Instead it proposes two execution domains inside one coherent operating system:

1. a **Legacy Domain**, where AROS/Amiga ABI v1 semantics remain valid;
2. a **Protected Domain**, where new software can use isolated address spaces, capabilities, explicit shared memory and restartable services.

The user should still see one system.

## Preserve the Amiga character

Nexus is not an excuse to discard what makes AROS recognisably Amiga-like.

The project explicitly wants to preserve and evolve concepts such as:

- Exec-style tasks and asynchronous messaging;
- message ports as a first-class abstraction;
- signals/events;
- the library/device/resource model;
- asynchronous I/O;
- Intuition;
- BOOPSI and Zune;
- Wanderer;
- lightweight system services;
- fast startup;
- directness and low conceptual overhead.

Where a new protected ABI is required, it should remain recognisably inspired by Exec rather than merely wrapping a Unix process model.

POSIX compatibility is useful. It should not define the identity of the system.

## Modernity without cultural erasure

Modernising AROS should not mean hiding Linux underneath a Workbench-like desktop.

For Nexus, modernity means giving AROS native mechanisms for:

- x86-64 SMP;
- ARM64;
- RISC-V;
- UEFI;
- NVMe;
- AHCI;
- USB/xHCI;
- IPv6;
- modern graphics stacks;
- isolated address spaces;
- protected drivers;
- controlled DMA through IOMMU;
- W^X;
- ASLR;
- recoverable services;
- fault containment.

The important part is that these mechanisms belong to AROS as architectural capabilities, not as an imported identity.

## Compatibility is a feature, not an obstacle

The historical ABI is not something Nexus intends to "clean up" until old software stops working.

It is a compatibility contract.

Legacy software should be able to run inside a Legacy Cell with the semantics it expects. The surrounding Nexus system then limits the consequences of failures or unsafe assumptions.

This lets us say both:

> old software can keep behaving like old Amiga/AROS software

and:

> new software does not have to inherit every historical limitation.

That distinction is the foundation of the project.

## Evolution, not a clean-room replacement

Nexus is deliberately being developed inside an AROS fork.

That is important.

The intention is to reuse and strengthen existing AROS work wherever practical:

- kernel.resource;
- Exec;
- DOS;
- HIDD;
- Intuition;
- Zune;
- Wanderer;
- AHI;
- Poseidon;
- AROSTCP;
- current storage drivers;
- current graphics work;
- the existing toolchain and build system;
- current x86-64, ARM64 and RISC-V work.

The first question for every subsystem should be:

> What can be preserved, wrapped, isolated or evolved?

not:

> What can be rewritten?

## Relationship with upstream AROS

AROS-FraPo is currently an experimental fork.

Nexus is not presented as an official AROS roadmap, and it is not intended to compete with or diminish the work of the AROS Development Team.

The purpose of the fork is to provide enough freedom to test a deep architectural direction without destabilising upstream development.

The desired long-term relationship is constructive:

- keep the fork synchronisable with upstream;
- avoid gratuitous code churn;
- isolate experimental changes;
- document architectural decisions;
- measure compatibility;
- contribute generally useful fixes upstream where appropriate;
- invite technical criticism early.

If parts of Nexus prove useful to upstream AROS, that would be a success.

If some ideas are rejected after serious testing, documenting why they failed would also be useful.

## What success would look like

A successful Nexus would eventually allow all of these statements to be true at the same time:

- classic AROS applications still run;
- Wanderer still feels like AROS;
- Exec concepts remain central;
- one bad legacy application cannot destroy the whole machine;
- one bad driver does not require a reboot;
- native applications can have protected address spaces;
- large data can still move zero-copy through explicit shared MemoryObjects;
- SMP scales without redefining the whole OS as Unix;
- modern storage and networking are native citizens;
- x86-64, ARM64 and RISC-V share the same architectural model;
- the system remains small enough to understand.

The final goal is not merely "AROS with memory protection".

The goal is an AROS that can grow for another generation without losing the reason people cared about Amiga-like systems in the first place.

## A project open to disagreement

This is an architectural proposal, not a declaration that every design decision is already correct.

Nexus should earn its place through:

- working code;
- reproducible tests;
- measurable compatibility;
- small demonstrable milestones;
- technical review;
- willingness to revise assumptions.

I would especially welcome discussion from people with experience in:

- AROS internals;
- AmigaOS internals;
- Exec and DOS;
- MMU and x86-64;
- ARM64 or RISC-V;
- SMP;
- device-driver architecture;
- HIDD;
- PCI/PCIe;
- IOMMU and DMA;
- graphics;
- security;
- compiler/runtime work.

The project exists because of enthusiasm for Amiga, but enthusiasm alone is not enough. The engineering has to stand up to scrutiny.

## The principle I want to protect

The simplest summary of Nexus is:

> **Preserve the Amiga programming culture where it is valuable. Isolate the historical assumptions where they are dangerous. Build modern capabilities around both without turning AROS into something else.**

That is the direction I intend to pursue.
