# Nexus Governance

> Status: initial project governance

## Project direction

**Nexus is directed by Francesco Poltero.**

Project contact:

**info@francescopoltero.com**

The project is an experimental architecture workstream inside the AROS-FraPo fork and is developed independently from the official AROS Development Team.

Nexus is intended to remain respectful of, technically compatible with and continuously informed by upstream AROS work.

## Role of the project director

The project director is responsible for:

- maintaining the long-term Nexus vision;
- protecting the architectural invariants documented in this repository;
- deciding when an experiment is mature enough to advance;
- stopping work when evidence is insufficient;
- ensuring the mandatory review protocol is followed;
- ensuring upstream AROS developments are continuously considered;
- coordinating community discussion and contributions;
- making final integration decisions for the experimental fork.

Direction does not mean that architectural decisions are exempt from technical challenge.

Nexus explicitly welcomes strong technical criticism and red-team review.

## Decision model

Decisions should be evidence-driven.

Priority order:

1. correctness;
2. compatibility;
3. containment/security;
4. maintainability;
5. upstream interoperability;
6. performance;
7. implementation speed.

A faster implementation must not win over a safer, more understandable one merely because it reaches a visible milestone sooner.

## Architecture decisions

Major architectural changes require an ADR when they alter:

- trust boundaries;
- ABI contracts;
- scheduler ownership;
- address-space ownership;
- privilege semantics;
- capability/IPC rules;
- hardware/DMA ownership;
- compatibility guarantees.

The project director may accept, reject, postpone or request redesign of a proposal after review.

## Review requirement

All non-trivial changes follow `REVIEW_PROTOCOL.md`.

At least three distinct review passes are required:

1. correctness and scope;
2. regression/concurrency/upstream integration;
3. adversarial red-team.

This applies to both implementation and architectural concepts.

## Upstream relationship

AROS-FraPo is not intended to become isolated from the AROS community.

The project should:

- regularly inspect upstream `aros-development-team/AROS`;
- keep the fork's `master` branch close to upstream;
- integrate relevant upstream fixes before creating competing local solutions;
- avoid unnecessary source divergence;
- consider upstreaming generally useful fixes that are independent of Nexus.

Nexus-specific architecture remains experimental unless adopted by upstream through its own community process.

## Community participation

Broad architectural discussion belongs in GitHub Discussions.

Concrete, testable work belongs in GitHub Issues and pull requests.

Contributors are encouraged to challenge assumptions rather than simply implement the current documents.

A well-supported argument that causes Nexus to reject an idea is a useful contribution.

## Hardware validation authority

When the review protocol identifies a dependency on physical hardware validation, roadmap work in that dependency chain must pause.

No roadmap milestone should be marked complete until the required hardware test has been performed and recorded.

The project director coordinates the decision to resume after reviewing that evidence.

## Contact

For project-level contact:

**Francesco Poltero**  
**info@francescopoltero.com**
