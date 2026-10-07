# Nexus Verification Model

> Status: mandatory engineering policy
>
> Purpose: make evidence, rather than code volume or agent consensus, the main source of confidence.

## 1. Why this exists

AI-assisted engineering changes the economics of Nexus.

Generating:

- source inventories;
- patches;
- tests;
- documentation;
- interface glue;

can become much cheaper.

Verification does not become cheap automatically.

In low-level operating-system work, plausible code can still be wrong because of:

- stale state;
- hidden privilege;
- SMP races;
- undefined ABI assumptions;
- hardware behavior;
- incomplete fault paths;
- misleading test harnesses.

Therefore Nexus treats **verification capacity** as the limiting resource.

## 2. Core rule

> No amount of agent agreement upgrades a claim to a higher evidence class by itself.

Independent evidence should come from behavior that can contradict the implementation.

Examples:

- compiler/static-analysis failure;
- regression test;
- malformed-input rejection;
- protection fault;
- QEMU trace;
- hardware observation;
- independent human review.

## 3. Evidence classes

### E0 — reasoning

Examples:

- source reading;
- design argument;
- agent review;
- architecture comparison.

Useful for choosing what to test.

Insufficient alone for runtime/security claims.

### E1 — static/mechanical validation

Examples:

- syntax check;
- schema validation;
- linters;
- link checks;
- static analyzers;
- generated-code consistency checks.

Can prove certain structural properties.

Cannot prove runtime semantics.

### E2 — focused executable test

Examples:

- unit test;
- negative test;
- malformed-input test;
- generator golden test;
- capability rejection test.

Preferred minimum evidence for local behavioral changes when practical.

### E3 — integration/regression test

Examples:

- AROS component tests;
- boot-stage tests;
- direct-versus-isolated conformance;
- multi-component failure/recovery test.

### E4 — deterministic virtual-machine evidence

Examples:

- fixed QEMU configuration;
- reproducible boot marker;
- controlled protection fault;
- repeatable context-switch test.

QEMU evidence is still virtual-hardware evidence.

### E5 — cross-architecture evidence

The same semantic contract is tested on more than one architecture class.

Useful for detecting accidental x86-only abstractions.

### E6 — physical-hardware evidence

Required where device/firmware/timing/physical DMA behavior materially determines correctness.

### E7 — independent expert review

A competent reviewer who was not the primary implementer validates the relevant invariants/evidence.

Particularly important before strong public security claims.

## 4. Review 3 is Evidence Red Team

Review 3 does not ask:

> Does another agent agree with the patch?

It asks:

> What observable result would prove this patch wrong?

The reviewer should attempt to create that observation.

Preferred outputs include:

- test that fails before the fix and passes after;
- invalid input that bypasses a check;
- race/stress case;
- forced fault;
- stale handle/capability case;
- permission downgrade/revocation case;
- comparison showing semantic drift;
- provenance tampering case.

## 5. NO TEST, EXPLAIN WHY

When Review 3 does not add or run an executable adversarial test, it must include:

- why a test is not yet technically possible;
- which evidence class is currently available;
- the strongest concrete counterexample/failure scenario considered;
- what future prerequisite would make the test possible.

"Too difficult" is not enough.

## 6. Test-first preference for risky code

For kernel/protection work, prefer this order when practical:

1. define invariant;
2. define expected failure;
3. create or specify the negative test;
4. observe failure on current implementation when feasible;
5. implement smallest change;
6. rerun;
7. attack the changed implementation;
8. repeat relevant regression tests.

Not every extraction/refactor permits a failing-before test.

When it does not, use semantic equivalence/regression evidence.

## 7. Task acceptance contract

A non-trivial task should state before implementation:

### Goal

One concrete result.

### Non-goals

Explicitly excluded scope.

### Preconditions

What must already be true.

### Ownership

U/A/N classification.

### Acceptance criteria

Observable PASS conditions.

### Negative criteria

Observable outcomes that must fail or remain impossible.

### Required evidence

Minimum E-class and exact tests.

### Human gate

H0/H1/H2/H3.

### Security claim

Highest affected L0-L5 level.

### Stop conditions

Conditions that suspend dependent work.

A task without meaningful acceptance criteria is not ready for autonomous implementation.

## 8. Human/hardware gates

### H0 — automated evidence is sufficient for integration

Typical for:

- documentation;
- project metadata;
- simple tooling;
- non-critical generator/test changes.

This does not mean "no human may review". It means no special mandatory human security gate is imposed.

### H1 — mandatory human technical review

Required for changes affecting core:

- kernel;
- MMU;
- scheduler;
- privilege;
- fault handling;
- capability/IPC authority;
- ABI/protection boundary.

The reviewer must inspect actual diff and evidence.

### H2 — mandatory physical-hardware evidence

Required when VM/emulation cannot establish the property.

H2 blocks dependent work.

### H3 — independent expert/security review

Required before strong release-level L2-L5 claims or similarly consequential security assertions.

H3 is not required for every experimental commit.

It is a release/claim gate.

## 9. Global versus task-specific gates

Do not run every expensive gate for every file change mechanically.

Use:

`global prerequisites + affected-subsystem gates + task-specific evidence`

Examples:

### Documentation

- G0;
- task-specific link/process checks.

### Baseline tooling

- G0;
- harness self-test.

### MMU extraction

- G0;
- G1;
- G2;
- MMU regression/protection tests;
- H1.

### IOMMU/DMA claim

- G0/G1/G2;
- IOMMU-specific tests;
- H1;
- H2;
- eventually H3 for strong release claims.

## 10. Agent independence limitation

Different agents can share:

- training data;
- common heuristics;
- similar blind spots;
- the same incorrect premise.

Therefore "three models reviewed it" is not equivalent to three independent experimental results.

Use additional agents to:

- broaden hypotheses;
- generate attacks;
- inspect different dimensions;
- create tests.

Use external evidence to decide.

## 11. One integrator

Each non-trivial feature branch has one logical integrator.

The integrator owns:

- final scope;
- conflict resolution;
- evidence completeness;
- upstream comparison;
- review-log coherence;
- decision to request merge.

This prevents multi-agent output from becoming unowned patch accumulation.

The integrator may be Francesco Poltero or an explicitly designated maintainer.

## 12. Kernel/security rule

For H1 changes:

AI may:

- analyze;
- implement;
- write tests;
- perform red-team review;
- prepare evidence.

AI-only review is not sufficient for final acceptance.

Until the required human review occurs, the PR remains experimental/blocked for integration according to the task gate.

## 13. Real-hardware rule

Never extrapolate from QEMU to claims requiring physical behavior.

Examples:

- IOMMU isolation;
- bus-master DMA;
- interrupt remapping;
- PCIe/NVMe quirks;
- USB timing;
- firmware;
- GPU;
- power/resume.

Prepare a hardware test package and stop dependent implementation.

## 14. Security claims

A security claim should cite:

- invariant;
- evidence class;
- exact test/environment;
- affected architecture/hardware;
- known exclusions;
- residual risk.

"L1 passed" means only the tested L1 invariant passed in the stated environment.

It is not a synonym for "Nexus is secure".

## 15. Upstream contribution and AI assistance

At the time this policy was written, current upstream AROS `CONTRIBUTING.md` contains no explicit blanket rule forbidding AI-assisted contributions.

That absence is not a permanent policy guarantee.

Before submitting significant Nexus-originated work upstream:

1. re-read current CONTRIBUTING/policies;
2. discuss the change with the AROS core team when required;
3. ask whether AI-assistance disclosure is expected;
4. disclose assistance transparently where relevant;
5. ensure the human submitter owns the decision to submit and can explain the code/tests;
6. verify license/provenance independently of model output.

## 16. Success criterion

The process is working when:

- agents can produce more candidate work;
- CI/tests reject more wrong work before merge;
- red-team review creates executable evidence;
- security claims become narrower and more defensible;
- human attention is reserved for the boundaries where it adds the most value.

The goal is not to maximize automated commits.

The goal is to maximize **verified progress per unit of human attention**.
