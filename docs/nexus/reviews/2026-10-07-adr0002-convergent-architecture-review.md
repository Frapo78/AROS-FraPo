# ADR-0002 Convergent Architecture Review — 2026-10-07

> Scope: architectural transition from mandatory Legacy-Cell-first Nexus to convergent AROS / Nexus architecture.
>
> Tracking: issue #18, PR #19
>
> Result: **ACCEPT AS CURRENT DIRECTION, WITH EXPLICIT RESIDUAL RISKS**

## Reviewed decision

ADR-0002 establishes that:

- AROS remains the primary system runtime;
- Nexus becomes the small privileged executive beneath it;
- machine mechanism is separated from AROS policy;
- Legacy Cells become selective containment tools;
- no mandatory parallel ExecNG ecosystem is created;
- upstream `m68kemu.library` remains the primary m68k compatibility path;
- existing AROS interface-generation infrastructure is preferred over parallel schemas;
- direct and isolated service paths may share one semantic contract;
- AI/LLM support remains outside the kernel TCB and is deferred.

No AROS operating-system source code is modified by this architectural PR.

## Review 1 — correctness and internal consistency

### Questions

- Does the new direction contradict existing Nexus documents?
- Does it preserve the valid safety invariant from ADR-0001?
- Does it accidentally promise protections that are not implemented?
- Does it make Legacy Cells mandatory in any remaining core document?
- Does it freeze a new public ABI prematurely?

### Findings

#### R1-F1 — stale mandatory Legacy-Cell assumptions

`TRUST_MODEL.md`, `ADDRESS_SPACE_MODEL.md`, `ABI_V1_COMPAT.md`, `BOOTSTRAP_MVP.md` and `NEXUS_EXEC_SPLIT.md` still contained assumptions from the earlier topology.

### Correction

Introduced the **Compatibility Trust Domain (CTD)** concept and revised the documents so that:

- ordinary ABI v1 AROS can remain the normal shared runtime during convergence;
- it is not falsely described as untrusted/contained while historical privilege remains;
- Legacy Cells are selective tools;
- protected AROS execution is additive rather than a separate OS personality.

#### R1-F2 — stale ABI-v2 wording

The AddressSpace document still described WX policy in terms of "ABI v2 software".

### Correction

Replaced that assumption with the more general "protected AROS software". The public protected API remains intentionally unfrozen.

#### R1-F3 — project index numbering error

The revised Nexus reading order contained duplicate item number 5.

### Correction

Renumbered the project reading map and clarified the ADR-0001/ADR-0002 relationship.

### Review 1 result

**PASS after corrections and repeat consistency scan.**

## Review 2 — regression, upstream and maintainability

### Upstream state checked

Current upstream head at review time:

`aros-development-team/AROS@6c1e40647f1bc58cd6986a5050563f2112c17329`

Fork `master` was fast-forwarded to that commit and merged into `nexus/main` before ADR-0002 work began.

The reproducible implementation baseline remains intentionally pinned to:

`2edd46536d08e3b54ecd1315f337a9b7de896f3a`

until G1/G2 build/boot evidence is repeated.

### Upstream evidence supporting convergence

Current upstream AROS actively develops mechanisms Nexus can reuse.

In particular, `rom/m68kemu` currently provides:

- transparent m68k Hunk routing from DOS;
- contained m68k memory;
- Moira CPU emulation;
- native AROS API forwarding;
- generated thunks from FD/prototype information;
- generated structure/shadow layouts;
- ongoing fixes for pointer translation, portability and ABI details.

Recent m68kemu commits were reviewed, including fixes for argument translation and generator portability.

This supports the decision to consume and strengthen upstream m68k compatibility instead of creating a fork-only translator.

Current HIDD/storage work also demonstrates that upstream interfaces continue to evolve, strengthening the case for narrow/generated adapters rather than copied interfaces.

### Fork-delta review

The ADR-0002 feature branch modifies only:

- Nexus documentation;
- project README metadata;
- the Nexus project-sanity workflow.

It does not modify AROS OS implementation source.

### Maintainability conclusion

The U/A/N ownership model is a stronger upstream-maintenance strategy than:

- permanent full-AROS Legacy Cell;
- clean-room NexusOS + AROS personality;
- parallel ExecNG runtime.

### Review 2 result

**PASS.**

## Review 3 — adversarial red-team

The red-team assumed the convergent architecture could fail by becoming an excuse to preserve unsafe privilege or accumulate hidden complexity.

Findings are recorded in `CONVERGENCE_RISKS.md`.

### R3-F1 — convergence could preserve a permanently privileged ABI v1 world

If "AROS remains primary" meant "AROS keeps all machine authority forever", Nexus would add abstractions without establishing a meaningful protection boundary.

### Correction: trust ratchet

Machine authorities now have an explicit migration direction:

1. legacy-owned;
2. shared/adapted;
3. Nexus-owned for protected modes.

A protected mode must not silently regain a direct legacy bypass after authority is extracted.

### R3-F2 — direct and isolated paths may become two incompatible implementations

### Correction

Both paths must share one semantic contract and conformance tests where practical.

Isolation is not considered transparent if important semantics differ.

### R3-F3 — generator-first bridges may mass-produce unsafe code

Unknown pointers, callbacks and pointer-to-pointer semantics cannot be treated as automatically serializable.

### Correction

Introduced bridgeability classes:

- B0 direct-only legacy;
- B1 generated value/handle bridge;
- B2 explicit manual bridge;
- B3 protected-native contract.

Protected generators must fail closed on unknown unsafe types.

### R3-F4 — U/A/N classification may decay into permanent adapter debt

### Correction

A-class adapters require a narrow documented seam and periodic deletion review.

Removing a Nexus workaround because upstream improved is defined as progress.

### R3-F5 — upstream may introduce new machine-privilege bypasses

### Correction

Continuous upstream review must specifically inspect MMU, IRQ, PCI, DMA, kernel/exec and hardware-interface changes against the trust ratchet.

### R3-F6 — m68kemu contained memory may be mistaken for a security sandbox

Current m68kemu forwards substantial functionality into native AROS and implements compatibility Supervisor behaviour.

### Correction

Nexus treats m68kemu primarily as a compatibility mechanism.

Hostile-m68k containment requires a separate explicit protection proof/domain.

### R3-F7 — a protected AROS application cannot transparently call every legacy library

Some APIs fundamentally require shared pointers/global state.

### Correction

Protected software can use only validated B1/B2 bridges, B3 contracts, or explicitly trusted direct libraries.

Universal transparent compatibility is not promised.

### R3-F8 — early generic Nexus objects may become x86-shaped

### Correction

Early Nexus contracts remain internal/versionable until at least a second architecture has been reviewed.

### R3-F9 — AI could become scope creep

### Correction

AI remains a later optional consumer of general mechanisms.

No early Nexus milestone depends on AI.

### Review 3 result

**PASS WITH RESIDUAL RISKS.**

## Residual risks deliberately accepted

The following are not solved by this ADR and must remain visible:

- the normal ABI v1 CTD is not yet strongly isolated;
- actual machine authority has not yet been moved into Nexus;
- generator-first service transport is still an architectural hypothesis;
- direct/isolated conformance has not yet been demonstrated;
- protected AROS public APIs are intentionally not frozen;
- m68kemu is not yet a Nexus security sandbox;
- the U/A/N model is currently documentation-driven rather than machine-readable;
- the current work proves architecture coherence, not runtime correctness.

## CI evidence

The feature branch has passed the existing G0 checks during the review cycle:

- Nexus project sanity;
- source line-ending validation;
- Windows filename validation.

The final head must pass the same checks before merge.

## Decision

**Accept ADR-0002 as the current Nexus architectural direction.**

This acceptance does not freeze every mechanism.

Fine tuning and substantial future changes remain allowed through reviewed ADRs when justified by:

- upstream AROS evolution;
- implementation evidence;
- performance measurements;
- compatibility results;
- security findings;
- real-hardware validation.

## Next smallest safe work

After merge:

1. resume Phase 0 source audits under the convergent assumptions;
2. finish G1/G2 reproducible x86-64 build/QEMU baseline;
3. retain #14 MMU audit findings;
4. add U/A/N classification to the first implementation area;
5. do **not** write broad service/AI/ExecNG code;
6. keep P1.1 limited to the smallest AddressSpace extraction with unchanged AROS behaviour.
