# Nexus ABI v1 Compatibility Contract

This document defines what Nexus must preserve while introducing modern isolation.

## Purpose

The legacy ABI is not an implementation detail. It is an explicit compatibility domain.

Nexus may change where and how ABI v1 executes, but must not silently change the semantics that existing software reasonably depends on.

## Preserved concepts

Within a Legacy Cell, preserve:

- Exec Task behaviour;
- DOS Process behaviour;
- message ports and message ownership rules;
- signal allocation and delivery semantics;
- library/device/resource lookup;
- library bases and expected ABI conventions;
- TagItem conventions;
- IORequest asynchronous I/O model;
- BOOPSI object behaviour;
- Intuition application-visible semantics;
- Zune/MUI application-visible semantics;
- legacy shared-memory assumptions required by supported software;
- `Forbid()/Permit()` semantics as observed by code inside the cell;
- `Disable()/Enable()` semantics only to the degree necessary for the legacy environment, never as authority over Nexus itself.

## Explicitly not guaranteed outside a Legacy Cell

The following do not cross a protection boundary:

- arbitrary virtual pointers;
- private Exec internal structures;
- direct kernel structures;
- direct interrupt-controller access;
- direct page-table access;
- unrestricted PCI configuration access;
- unrestricted physical addresses;
- unrestricted DMA addresses.

A bridge must convert these into a Nexus-safe representation.

## Compatibility levels

### Level A — binary compatibility

Executable runs without recompilation in an appropriate Legacy Cell.

### Level B — source compatibility

Source recompiles for ABI v1 without architectural changes.

### Level C — bridge compatibility

Source remains conceptually compatible but selected services cross a Nexus proxy.

### Level D — native migration

Application is ported to ABI v2 and gains per-process isolation.

The project must identify which level a change affects.

## Forbidden shortcuts

Nexus development must not:

- change legacy structure layout merely to simplify the protected kernel;
- change LVO numbering as part of Nexus work;
- reinterpret an existing ABI v1 pointer as a global Nexus pointer;
- require every legacy application to adopt handles;
- make a legacy application privileged merely to retain compatibility;
- expose Nexus physical-memory addresses through legacy interfaces unless an explicit, audited compatibility mechanism requires it.

## Compatibility testing

The initial test corpus should include:

- Exec task/message/signal tests;
- DOS process and file tests;
- Intuition applications;
- Zune/MUI applications;
- Wanderer startup;
- AHI;
- network applications;
- storage I/O;
- representative software that exchanges pointers through classic interfaces.

Every Legacy Cell milestone must compare behaviour against the baseline build.

## Compatibility vs containment

Compatibility applies *inside* the Legacy Cell.

Containment applies *outside* it.

If a legacy application corrupts shared structures inside its own cell, Nexus is not required to save that cell. Nexus is required to prevent that corruption from becoming arbitrary access to:

- another Legacy Cell;
- a protected process;
- an isolated driver;
- Nexus itself.

This distinction is foundational.
