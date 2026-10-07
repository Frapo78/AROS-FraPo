# Nexus ABI v1 Compatibility Contract

This document defines what Nexus must preserve while introducing modern protection.

## Purpose

ABI v1 is not an implementation detail.

It is a compatibility contract carried by the normal AROS runtime.

Nexus may change how low-level machine mechanisms are implemented, but it must not silently invalidate semantics that existing AROS software reasonably depends on.

ADR-0002 changes one earlier assumption:

> ABI v1 is no longer defined as living primarily inside a mandatory Legacy Cell.

The ordinary AROS runtime remains the primary ABI v1 environment.

Legacy Cells remain available selectively when stronger containment is worth the compatibility cost.

## Preserved concepts

AROS ABI v1 should continue to preserve, within its supported compatibility scope:

- Exec Task behaviour;
- DOS Process behaviour;
- message ports and ownership rules;
- signal allocation and delivery;
- library/device/resource lookup;
- library bases and calling conventions;
- TagItem conventions;
- IORequest asynchronous I/O;
- BOOPSI semantics;
- Intuition application-visible behaviour;
- Zune/MUI application-visible behaviour;
- shared-memory assumptions required by supported software;
- `Forbid()/Permit()` application-visible semantics;
- historical library/device ABI layout where binary compatibility requires it.

## Shared memory is compatibility, not global authority

ABI v1 may continue to use raw pointers inside the normal shared AROS execution environment.

That does not mean a raw pointer gains authority across a protected Nexus boundary.

When crossing into:

- a protected process;
- an isolated service;
- an isolated driver;
- a Legacy Cell;
- Nexus itself;

the bridge must use a safe representation such as:

- handle/capability;
- MemoryObject;
- copied/validated value;
- generated ABI bridge.

## Explicitly not guaranteed across protected boundaries

The following do not cross a Nexus protection boundary as implicit authority:

- arbitrary virtual pointers;
- private Exec structures;
- raw kernel structures;
- page-table pointers;
- unrestricted physical addresses;
- unrestricted MMIO;
- unrestricted PCI configuration;
- unrestricted DMA targets;
- arbitrary supervisor entry points.

## Compatibility modes

The architecture recognizes several practical modes.

### Mode A — normal ABI v1

Existing AROS software runs in the ordinary AROS runtime.

This remains the default compatibility path.

### Mode B — adapted service boundary

Software remains ABI v1, but selected calls are implemented through a Nexus adapter or isolated service.

The semantic API remains as compatible as practical.

### Mode C — selective Legacy Cell

A risky or unusually privileged legacy component runs in a contained shared-pointer environment.

The Cell preserves the historical assumptions internally while limiting machine authority externally.

### Mode D — protected AROS application

Software adopts protected execution APIs while remaining part of AROS.

The exact public protected ABI is intentionally not frozen yet.

### Mode E — m68k compatibility

Classic Amiga m68k software runs through upstream `m68kemu.library` or its future upstream-compatible evolution.

## Compatibility levels

Separately from execution mode, changes can be classified by compatibility result.

### Level A — binary compatible

Runs without recompilation in the relevant supported environment.

### Level B — source compatible

Recompiles without architectural redesign.

### Level C — bridge compatible

The public concept remains compatible while selected operations cross a generated/validated bridge.

### Level D — migration required

Software must adopt a new protected or service API to gain a property that cannot coexist with the old contract.

## Forbidden shortcuts

Nexus development must not:

- change legacy structure layout merely to simplify Nexus;
- renumber LVOs as a Nexus convenience;
- reinterpret an ABI v1 pointer as a globally trusted Nexus pointer;
- require every legacy application to adopt handles;
- grant real Nexus privilege merely to preserve a historical API;
- fork a large upstream compatibility subsystem when a narrow adapter would work;
- create a parallel m68k compatibility stack without strong evidence.

## m68k compatibility

Upstream AROS `m68kemu.library` is part of the compatibility strategy.

Its current design already demonstrates useful principles:

- contained m68k address space;
- fake Amiga library bases;
- LVO interception;
- generated thunk coverage;
- generated structure-layout translation;
- forwarding to native AROS libraries.

Nexus should consume and strengthen this work rather than duplicate it.

## Compatibility testing

The corpus should cover:

- Exec task/message/signal behaviour;
- DOS process and filesystem behaviour;
- Intuition;
- Zune/MUI;
- Wanderer startup;
- AHI;
- network applications;
- storage I/O;
- pointer-sharing legacy applications;
- m68k applications through upstream m68kemu;
- direct versus adapted service paths where both exist.

Every protection milestone compares against the recorded AROS baseline.

## Compatibility versus containment

Compatibility and containment remain different properties.

The project may preserve shared-pointer ABI v1 semantics while adding protected boundaries elsewhere.

When a Legacy Cell is used, corruption inside that Cell need not be recoverable.

When normal ABI v1 runs outside a Cell, its historical shared-memory risks remain part of that execution mode until stronger protection is introduced.

The project must state the actual isolation level rather than imply that ABI compatibility alone provides containment.

## Core rule

> Preserve ABI v1 where compatibility requires it; introduce protection around explicit boundaries instead of pretending shared pointers are safe everywhere.
