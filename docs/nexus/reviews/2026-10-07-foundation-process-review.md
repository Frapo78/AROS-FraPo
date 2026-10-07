# Foundation Process Review — 2026-10-07

> Scope: Phase 0 architecture/process hardening performed before the first Nexus kernel implementation.
>
> Result: **accepted with one external repository-setting action still required**.

## Reviewed material

The review covered the new or materially revised Nexus foundation:

- trust/fault model;
- legacy privilege model;
- Nexus/Exec split;
- address-space model;
- upstream baseline policy;
- CI/validation strategy;
- review protocol;
- governance;
- branch policy;
- root/Nexus README changes;
- contribution and issue/PR templates;
- Nexus project sanity workflow.

No AROS operating-system source code was changed during this review cycle.

## Review 1 — correctness and scope

### Objective

Verify that the process/documentation additions:

- match the actual project state;
- do not claim implementation that does not exist;
- remain focused on pre-implementation guardrails;
- are internally linkable and mechanically checkable.

### Findings

**R1-F1 — incomplete G0 trigger coverage**

The initial `nexus-project-sanity.yml` watched Nexus docs, CONTRIBUTING and issue templates but did not trigger when:

- the root `README.md` changed;
- `.github/pull_request_template.md` changed.

That meant public project metadata could drift without re-running the Nexus sanity gate.

### Correction

The workflow path filters were expanded to cover:

- `README.md`;
- `.github/pull_request_template.md`.

### Verification

The Nexus project sanity workflow subsequently completed successfully on the corrected branch state.

### Review 1 result

**PASS after correction and repeat review.**

No OS implementation scope was introduced accidentally.

## Review 2 — regression, integration and upstream

### Objective

Check that the foundation work does not create unnecessary source divergence and is still based on current upstream AROS.

### Upstream state checked

Repository:

`aros-development-team/AROS`

Upstream head at review time:

`2edd46536d08e3b54ecd1315f337a9b7de896f3a`

This is the same commit recorded as the current Nexus implementation baseline.

Fork `master`:

- aligned to the upstream head;
- intended to remain upstream-only.

`nexus/main`:

- **0 commits behind** fork `master` at the review point;
- Nexus differences are concentrated in documentation and repository metadata;
- no AROS OS source file is modified by the Nexus foundation work.

### Integration findings

- root README changes are additive and retain upstream AROS material;
- CONTRIBUTING preserves upstream guidance below a Nexus-specific section;
- Nexus-specific documentation lives under `docs/nexus`;
- no current upstream kernel implementation has been replaced;
- upstream synchronization remains manageable.

### Review 2 result

**PASS.**

The project is ready to continue Phase 0 source analysis without carrying a stale upstream base.

## Review 3 — adversarial red-team

### Objective

Assume the newly created development discipline can be bypassed or can give false confidence.

### Finding R3-F1 — review protocol was socially enforceable only

At review time, GitHub reported:

`nexus/main protected: false`

Therefore a direct push could bypass:

- pull-request evidence;
- the three-review record;
- status-check requirements.

### Correction

Added:

`docs/nexus/BRANCH_POLICY.md`

The required policy now explicitly calls for:

- PR-based integration of non-trivial implementation;
- required checks;
- conversation resolution;
- no force pushes;
- no branch deletion.

### Residual risk

The source repository cannot enable GitHub branch protection by itself.

**GitHub branch protection/ruleset still needs to be enabled in repository settings.**

Until that is done, the control remains partly procedural.

### Finding R3-F2 — mutable third-party action reference

The first G0 workflow used:

`actions/checkout@v4`

A moving tag introduces avoidable supply-chain/reproducibility ambiguity.

### Correction

Pinned the checkout action to the reviewed commit:

`11d5960a326750d5838078e36cf38b85af677262`

with the `v4` annotation retained for readability.

### Finding R3-F3 — visible progress could pressure premature coding

A daily development cycle can accidentally turn "work every day" into "commit code every day".

### Correction

The mandatory review protocol now states that a productive cycle may end with:

- analysis;
- rejected design;
- documentation;
- upstream integration;
- test refinement;
- red-team findings;
- a deliberate pause.

Commit count is not treated as progress.

### Finding R3-F4 — QEMU could create false confidence about hardware isolation

CPU memory protection in QEMU is not proof of:

- real IOMMU behaviour;
- DMA containment;
- PCIe/NVMe behaviour;
- interrupt remapping;
- firmware/chipset behaviour.

### Correction

The CI strategy and review protocol now define a **hardware stop rule**.

When the next property depends materially on physical hardware:

- dependent code advancement stops;
- exact test instructions/artifacts are prepared;
- the project waits for real-hardware evidence;
- the claimed isolation level is not advanced.

### Review 3 result

**PASS WITH RESIDUAL GOVERNANCE RISK.**

Residual item:

- enable technical branch protection/ruleset for `nexus/main`.

## CI evidence

The `Nexus project sanity` workflow completed successfully on the reviewed sequence, including after:

- expanded path coverage;
- checkout action pinning;
- branch-policy integration;
- review-protocol integration.

## Decision

**ACCEPT the Phase 0 foundation/process hardening.**

Do not begin P1.1 kernel implementation solely because this review passed.

The remaining Phase 0 technical gates still include:

- reproducible x86-64 build;
- QEMU boot baseline;
- privileged-operation source audit;
- kernel.resource/Exec dependency inventory;
- x86-64 NX/W^X/MMU/TLB audit;
- regression/test inventory;
- baseline diagnostics.

## Next safe action

Continue Phase 0 analysis and establish G1/G2.

The first kernel modification remains blocked until the preconditions in issue #7 are satisfied.
