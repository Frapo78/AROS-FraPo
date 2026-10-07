# Nexus

Nexus is the protected architecture workstream inside AROS-FraPo.

Its goal is to preserve AROS/Amiga ABI v1 semantics while adding a modern protected execution domain for new software and isolated system services.

## Current status

**Stage:** architecture baseline / Phase 0 preparation.

No claim is made yet that the Nexus execution model is implemented. The current branch establishes the constraints and implementation sequence that future code must follow.

## Documents

- [Architecture](ARCHITECTURE.md)
- [Roadmap](ROADMAP.md)
- [ABI v1 Compatibility Contract](ABI_V1_COMPAT.md)
- [Bootstrap MVP](BOOTSTRAP_MVP.md)
- [ADR-0001: Two-domain architecture](adr/0001-two-domain-architecture.md)

## Working branch

Primary development line:

`nexus/main`

The upstream-derived `master` branch should remain suitable for synchronisation with the original AROS repository.

## First engineering objective

The first engineering milestone is intentionally not a new UI or ABI.

It is to understand and then control the x86-64 protection boundary well enough that the current AROS environment can later boot as an unprivileged Legacy Cell while preserving ABI v1 behaviour.

## Project rule

Nexus modernizes the execution boundary, not the identity of AROS.

The project should preserve the small-message-driven, library/device/resource-oriented character of the system while removing the requirement that all software and hardware share one trust domain.
