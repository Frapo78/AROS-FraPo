# Upstream Integration Model

> Status: architectural process
>
> Decision: ADR-0002

## 1. Purpose

Nexus must evolve with AROS rather than beside it.

The fork is therefore designed around continuous upstream intake.

The goal is not merely to "merge upstream often". The goal is to minimize the amount of Nexus code that must be manually reconciled when AROS changes.

## 2. Ownership classes

Every major area touched by Nexus should be classified before deep modification.

### U — Upstream-owned

AROS is the source of truth.

Nexus should avoid fork-specific divergence unless a temporary experiment requires it.

Typical candidates:

- DOS;
- Intuition;
- Zune;
- Wanderer;
- m68kemu;
- applications and tools;
- AROSTCP;
- many HIDD implementations.

### A — Adapted

AROS remains the source, but Nexus introduces a deliberately narrow seam.

Typical candidates:

- selected Exec internals;
- kernel.resource;
- architecture startup;
- selected HIDD boundaries;
- selected device glue.

The adapter must be small enough that upstream changes can be reviewed mechanically and conceptually.

### N — Nexus-owned

The implementation belongs to Nexus because it defines the new protection substrate.

Typical candidates:

- AddressSpace;
- Capability;
- MemoryObject;
- protected Endpoint;
- domain-aware fault ownership;
- IOMMU/DMA authority.

Nexus-owned code should still follow AROS coding/build conventions where practical.

## 3. Change intake loop

Before beginning work on an area:

1. read current upstream code;
2. compare upstream head with the recorded Nexus baseline;
3. identify relevant new commits;
4. classify each change by U/A/N impact;
5. integrate or account for it before developing a conflicting local solution.

Before merge:

1. repeat the upstream check;
2. re-evaluate touched A-class adapters;
3. rerun affected compatibility/regression tests;
4. record the upstream SHA reviewed.

## 4. Baseline versus upstream head

Nexus keeps two distinct concepts.

### Recorded baseline

A known upstream commit against which a build/test result is reproducible.

### Current upstream head

The latest AROS state that must be monitored continuously.

The baseline should not move accidentally every time upstream commits.

The fork `master` may advance continuously while the recorded implementation baseline moves only after:

- review;
- successful baseline build;
- known regression status.

This preserves reproducibility without becoming stale.

## 5. U-class update policy

When a U-class subsystem changes upstream:

- prefer importing the change unchanged;
- do not maintain a parallel Nexus version without strong reason;
- update Nexus docs only if the upstream change affects an architectural assumption;
- treat upstream tests as part of the compatibility corpus.

If Nexus needs a generally useful fix in a U-class area, consider upstreaming it.

## 6. A-class update policy

A-class code is the highest maintenance risk.

Every A-class adapter should have:

- a narrow documented purpose;
- a minimal diff from upstream;
- explicit tests;
- a named Nexus contract it implements.

When upstream changes the same code:

1. read the upstream intent;
2. check whether the Nexus seam is still necessary;
3. prefer moving the seam rather than freezing an old implementation;
4. avoid copying large functions merely to insert a small hook.

## 7. N-class update policy

N-class code is expected to be Nexus-specific.

Upstream changes may still affect it indirectly through:

- architecture headers;
- allocators;
- scheduler assumptions;
- build conventions;
- interfaces.

N-class code must not use Nexus ownership as an excuse to ignore upstream improvements.

## 8. Generated compatibility and service bridges

One of the best ways to reduce A-class maintenance is generation.

AROS already has:

- FD files;
- `genmodule`;
- HIDD/OOP interface descriptions;
- m68k thunk generation;
- structure-layout generation.

Nexus should extend these sources rather than create parallel manually maintained interface declarations.

The ideal flow is:

```
AROS interface source
        |
        +--> native direct interface
        +--> compatibility thunk
        +--> Nexus validation metadata
        +--> Nexus proxy/service stub
```

This is a direction, not a requirement that every interface be converted immediately.

## 9. m68k compatibility policy

`rom/m68kemu` is upstream-owned.

Nexus should:

- track it closely;
- consume its generated thunk/shadow work;
- contribute generally useful improvements upstream where possible;
- avoid a fork-only m68k compatibility stack.

If Nexus later experiments with a JIT/DBT backend, the preferred design is an engine behind the same m68kemu contract rather than a competing launcher/runtime.

## 10. HIDD policy

HIDD interfaces remain upstream-defined service semantics.

Nexus may add generated/adapted transports where isolation is useful.

It must not silently fork the conceptual HIDD API merely to fit an IPC mechanism.

Pointer-rich HIDD methods require explicit bridge design.

## 11. Daily impact report

A future automation may maintain a generated report such as:

`docs/nexus/generated/UPSTREAM_IMPACT_REPORT.md`

It may include:

- upstream commits since baseline;
- touched U/A/N areas;
- Nexus-adapted files changed upstream;
- likely review priority;
- tests to repeat.

Such a report is advisory.

A human/agent review is still required before integration.

## 12. Conflict policy

When upstream and Nexus solve the same problem differently, do not automatically prefer local code.

Evaluate:

1. correctness;
2. compatibility;
3. security/containment;
4. maintainability;
5. portability;
6. performance;
7. amount of divergence.

If upstream now provides a sufficient mechanism, deleting a Nexus workaround is a success.

## 13. Success metric

The integration model succeeds when:

- `master` stays easy to fast-forward;
- U-class code remains close to upstream;
- A-class diffs stay small;
- N-class code remains isolated behind stable contracts;
- major upstream features can be adopted without architectural surgery.
