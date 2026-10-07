# Evidence-Driven Agent Process Review — 2026-10-07

> Scope: Nexus AI-assisted engineering process refinement.
>
> Tracking: issue #22, PR #23
>
> Human gate: H0
>
> Result: **ACCEPT PROCESS REFINEMENT, SUBJECT TO FINAL CI ON PR HEAD**

## Scope

This review covers:

- root `AGENTS.md`;
- `docs/nexus/VERIFICATION_MODEL.md`;
- revised `REVIEW_PROTOCOL.md`;
- revised `BRANCH_POLICY.md`;
- Nexus contribution guidance;
- Nexus engineering/architecture issue templates;
- PR template;
- agent-contract validation/self-test;
- project-sanity integration.

No AROS operating-system implementation file is modified.

ADR-0002 remains unchanged.

## Review 1 — Construction

### Goal

Make the operational rules short enough for agents to consume while keeping detailed verification policy available separately.

### Finding R1-F1 — AGENTS.md became a second manual

The first version grew to 357 lines.

That defeated its purpose as a short operational cache of project invariants.

### Correction

The file was compressed to under 300 lines.

Detailed evidence rationale remains in `VERIFICATION_MODEL.md`.

The project-sanity gate now enforces the size ceiling.

### Finding R1-F2 — rules existed but tasks could still be underspecified

The previous issue flow did not require:

- explicit non-goals;
- negative criteria;
- evidence class;
- human/hardware gate;
- stop conditions.

### Correction

Added a dedicated Nexus engineering task template with falsifiable acceptance and red-team criteria.

Architecture proposals were also updated to require a falsifiable proof or a NO TEST explanation.

### Finding R1-F3 — three reviews could still mean three opinions

The earlier protocol separated review purposes but did not require Review 3 to create independent evidence.

### Correction

Review 3 is now **Evidence Red Team**.

It follows:

> **NO TEST, EXPLAIN WHY.**

### Review 1 result

**PASS after correction.**

## Review 2 — Integration and upstream

### Upstream reviewed

Current upstream AROS head at review time:

`e2cb3acaace051317da486a5bfd574cda726540d`

No new upstream source change affects this process-only PR.

### Current upstream contribution policy

The current upstream `CONTRIBUTING.md` was re-read.

It:

- requests discussion with the AROS team for significant changes;
- requires build/test evidence;
- emphasizes portability;
- requires two core-developer sign-offs for upstream merge;
- does not currently state an explicit blanket prohibition on AI-assisted contributions.

Nexus does **not** interpret the absence of an explicit AI rule as permanent permission or policy.

The new process requires rechecking policy and asking the community about disclosure expectations before significant Nexus-originated upstream submissions.

### U/A/N impact

- AROS OS/build implementation: **U, unchanged**.
- Nexus process documentation/templates/tooling: **N**.
- No new A-class AROS seam is introduced.

### Architecture impact

ADR-0002 is unchanged.

The new rules constrain how future architecture/code work is accepted; they do not alter the architecture itself.

### Review 2 result

**PASS.**

## Review 3 — Evidence Red Team

### Falsification hypothesis

The process change is ineffective if key safety rules can be silently removed while CI remains green.

### Adversarial executable test

Added:

`scripts/nexus/verify-agent-contract.sh --selftest`

The self-test creates a valid temporary process-contract fixture and then deliberately corrupts it.

#### Attack A — remove NO TEST rule

The test deletes the mandatory `NO TEST, EXPLAIN WHY` rule.

Expected result:

- contract checker rejects the fixture.

#### Attack B — remove task acceptance criteria

The test removes `## Acceptance criteria` from the Nexus engineering task template.

Expected result:

- contract checker rejects the fixture.

#### Attack C — allow AGENTS.md to become bloated

The test appends enough padding to exceed the 300-line operational limit.

Expected result:

- contract checker rejects the fixture.

### Additional mechanical checks

The checker verifies that the process still contains:

- one logical integrator;
- no AI-only L1-L5 acceptance;
- H1 human review;
- E6 physical-hardware evidence;
- Evidence Red Team;
- negative criteria;
- human/hardware PR gate.

### Evidence class

**E2 — focused executable negative test** for the process/tooling contract.

This does not prove future engineering decisions will be correct.

It proves specific process regressions are mechanically detectable.

### Residual risks

- humans/agents can still fill templates with weak content;
- CI cannot determine whether a red-team test is meaningful;
- H1/H3 reviewer competence remains a human governance problem;
- a concise AGENTS.md can still become stale relative to architecture;
- evidence classes can be overstated unless reviewers challenge them;
- no process can eliminate model-correlated blind spots.

### Review 3 result

**PASS**, contingent on final PR-head CI executing the adversarial self-test successfully.

## Decision

Accept the evidence-driven process refinement if final CI is green.

The key behavioral changes are:

1. tasks become falsifiable before coding;
2. Review 3 tries to create evidence rather than agreement;
3. AI consensus is explicitly weaker than external evidence;
4. kernel/protection work is H1;
5. physical-hardware-dependent work is H2;
6. strong release-level L2-L5 claims are H3;
7. one integrator owns branch coherence;
8. upstream AI-assistance policy is rechecked rather than assumed.

## Next effect on roadmap

This process does not unblock P1.1 by itself.

The immediate project order remains:

1. finish/execute the x86-64 G1/G2 baseline harness;
2. complete remaining Phase 0 audits;
3. apply the new falsifiable issue contract to P1.1;
4. require H1 human review before any MMU/kernel change merges.
