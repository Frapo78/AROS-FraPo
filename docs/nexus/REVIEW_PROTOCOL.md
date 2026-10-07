# Nexus Review Protocol

> Status: mandatory engineering process
>
> Applies to non-trivial code, architecture, ABI, privilege, build-system and security-claim changes.

## 1. Principle

Nexus is deliberately developed slowly.

The project prefers a smaller verified step over a larger speculative change.

No code or architectural concept advances merely because it:

- looks plausible;
- compiles;
- passes syntax checks;
- receives agreement from several AI agents.

Evidence must be capable of contradicting the implementation.

See `VERIFICATION_MODEL.md`.

## 2. Minimum three-review rule

Every non-trivial modification or new concept completes at least **three distinct review passes**.

The same person or agent may perform more than one pass during early development, but the passes must remain different in purpose and evidence.

A meaningful correction resets the affected review scope.

## 3. Review 1 — Construction

Purpose:

> Is this the smallest correct implementation of the requested change?

Check:

- issue goal and non-goals;
- scope creep;
- ownership/lifetime;
- error paths;
- ABI compatibility;
- architecture-specific leakage;
- hidden assumptions;
- unnecessary abstractions;
- U/A/N ownership;
- documentation/code consistency.

Output:

- defects found;
- corrections made;
- unresolved assumptions;
- exact diff reviewed.

A meaningful correction requires another Construction pass over the corrected area.

## 4. Review 2 — Integration

Purpose:

> Does this change remain correct inside current AROS/Nexus rather than only in isolation?

Check:

- existing AROS regressions;
- ABI impact;
- SMP/concurrency;
- memory ordering;
- TLB/IRQ/fault/scheduler interaction;
- portability;
- current tested baseline;
- latest upstream AROS;
- U/A/N classification;
- upstream mergeability;
- cleanup/partial initialization;
- affected build and regression tests.

Review against:

- current feature branch;
- current `nexus/main`;
- recorded tested baseline;
- latest upstream AROS when relevant.

Output:

- upstream SHA reviewed;
- regression matrix;
- tests/evidence;
- integration concerns;
- residual portability gaps.

A feature branch must not silently revert unrelated current upstream code.

## 5. Review 3 — Evidence Red Team

Purpose:

> What observable result would prove this change wrong?

Assume the implementation is wrong until external evidence supports it.

Try to create or run evidence such as:

- negative test;
- regression test;
- malformed input;
- fault injection;
- capability abuse;
- stale-handle case;
- permission violation;
- TLB invalidation case;
- race/stress test;
- direct/isolated conformance failure;
- generator fail-open input;
- evidence/provenance tampering;
- DMA/hardware bypass scenario.

For a bug fix, prefer when practical:

1. test fails before the fix;
2. fix is applied;
3. test passes;
4. relevant regressions still pass.

For a refactor/extraction where failing-before is not meaningful, use semantic-equivalence/regression evidence.

### Mandatory rule

> **NO TEST, EXPLAIN WHY.**

If Review 3 cannot create or execute an adversarial test, the review must record:

- why such a test is not technically possible yet;
- current evidence class;
- strongest concrete counterexample/failure scenario considered;
- prerequisite required to make the test executable later.

"Another agent agrees" is not red-team evidence.

### Output

- falsification hypothesis;
- tests/attacks attempted;
- evidence class;
- findings;
- residual risks;
- decision: accept, revise, postpone or reject.

A red-team finding that changes a trust or architecture assumption returns the work to earlier review and may require an ADR.

## 6. Architecture concepts

Architecture documents are not exempt.

Before a concept becomes an implementation dependency:

1. internal consistency review;
2. source-reality/upstream review;
3. adversarial counterexample review.

Executable evidence may not yet exist for a pure design concept.

In that case Review 3 follows **NO TEST, EXPLAIN WHY** and records the future falsifiable proof.

A concept may be downgraded, split, postponed or rejected without being treated as project failure.

## 7. Acceptance criteria before implementation

A non-trivial issue should define:

- Goal;
- Non-goals;
- Preconditions;
- U/A/N ownership;
- Bridgeability B0-B3 if applicable;
- Acceptance criteria;
- Negative/red-team criteria;
- Required automated evidence;
- Required human evidence;
- Required hardware evidence;
- Affected L0-L5 claim;
- Stop conditions.

If the task cannot be meaningfully falsified, refine the task before autonomous implementation.

## 8. Evidence hierarchy

Use the detailed model in `VERIFICATION_MODEL.md`.

Roughly:

- E0 reasoning;
- E1 static/mechanical validation;
- E2 focused executable test;
- E3 integration/regression;
- E4 deterministic QEMU evidence;
- E5 cross-architecture evidence;
- E6 physical hardware;
- E7 independent expert review.

More AI reviewers do not automatically increase evidence level.

## 9. Human and hardware gates

### H0 — automated evidence can be sufficient

Typical for:

- documentation;
- project tooling;
- simple non-critical generators/tests.

### H1 — mandatory human technical review

Required before merge for changes affecting:

- kernel;
- scheduler;
- MMU;
- fault handling;
- privilege;
- capability/IPC authority;
- ABI/protection boundary.

AI may analyze, implement and red-team such work.

AI-only review is not sufficient for final acceptance.

### H2 — mandatory physical-hardware evidence

Required when VM/emulation cannot establish the property, including material claims involving:

- IOMMU/DMA;
- PCIe/NVMe;
- interrupt remapping;
- firmware/UEFI/chipset;
- USB/xHCI timing;
- GPU;
- power/resume.

H2 blocks dependent work.

### H3 — independent expert review

Required before strong release-level L2-L5 security/isolation claims.

H3 is not required for every experimental commit.

It is a claim/release gate.

## 10. Upstream review is continuous

Before starting work on a subsystem and again before merge:

1. inspect latest upstream AROS;
2. identify commits affecting the same area;
3. decide whether upstream work:
   - should be integrated first;
   - solves part of the problem;
   - invalidates an assumption;
   - conflicts with the proposed seam;
4. record the conclusion.

Nexus must not knowingly replace current community work with a stale local design.

## 11. One logical integrator

Each non-trivial feature branch has one logical integrator responsible for:

- scope coherence;
- conflict resolution;
- evidence completeness;
- upstream comparison;
- review-log coherence;
- merge readiness.

Multiple agents may contribute:

- source analysis;
- implementation;
- tests;
- review;
- red-team work.

Their output does not become unowned patch accumulation.

## 12. Required PR evidence

A non-trivial PR should record:

```
Review 1 — Construction: PASS
Findings:
Corrections:

Review 2 — Integration: PASS
Upstream checked at:
Regression evidence:

Review 3 — Evidence Red Team: PASS / PASS WITH RISKS
Falsification hypothesis:
Adversarial test:
Evidence class:
NO TEST explanation (only if needed):
Residual risks:

Human gate: H0/H1/H2/H3
Required human/hardware evidence:
```

"PASS" means the documented gate occurred.

It does not mean the code is proven bug-free.

## 13. Isolation claims

No L1-L5 claim is accepted solely from:

- source inspection;
- architecture documentation;
- AI review;
- number of reviewers.

The claim must cite executable/environmental evidence appropriate to the level.

CPU-MMU evidence does not prove DMA isolation.

Contained m68k memory does not prove a Nexus sandbox.

A process boundary does not prove restartability or hardware containment.

## 14. Hardware stop rule

When the required property materially depends on physical hardware and QEMU cannot validate it:

1. stop dependent implementation;
2. mark the task blocked;
3. prepare exact commit/artifact;
4. document hardware requirements;
5. document procedure and expected result;
6. document recovery/risk;
7. request real-hardware execution;
8. record evidence before resuming dependent work.

Never convert "not tested on hardware" into "probably works".

## 15. Pace rule

A productive cycle may end with:

- analysis;
- a failing test;
- a rejected approach;
- documentation;
- upstream integration;
- reduced scope;
- red-team finding;
- hardware stop;
- no commit.

Verified reduction of uncertainty is progress.

Commit count is not.

## 16. Branch enforcement

The expected repository enforcement is defined in `BRANCH_POLICY.md`.

For non-trivial implementation, use pull requests and required checks rather than maintainer discipline alone.

## 17. Definition of ready

A change is ready for integration only when:

- scope and non-goals are clear;
- acceptance/negative criteria are satisfied;
- upstream was rechecked;
- required tests pass;
- all three reviews are documented;
- Review 3 contains evidence or a valid NO TEST explanation;
- red-team findings are resolved or explicitly accepted;
- H1/H2/H3 requirements are satisfied when applicable;
- claimed L0-L5 level matches the evidence;
- documentation/issue state is updated.
