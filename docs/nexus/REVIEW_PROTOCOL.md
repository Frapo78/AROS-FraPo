# Nexus Review Protocol

> Status: mandatory engineering process
>
> Applies to code, architecture, ABI changes, privilege changes, build-system changes and new security claims.

## 1. Principle

Nexus is deliberately developed slowly.

The project must prefer a smaller verified step over a larger speculative change.

No code or architectural concept should advance merely because it appears elegant or compiles successfully.

## 2. Minimum three-review rule

Every non-trivial modification or new concept must complete at least **three distinct review passes** before it is considered ready.

The same reviewer may perform more than one pass during early development, but the passes must be separate in purpose and documented separately.

### Review 1 — correctness and scope

Questions:

- Does the change solve the issue it claims to solve?
- Is the implementation smaller than necessary, or has scope expanded?
- Does it preserve the documented ABI v1 contract?
- Does it import Exec-specific concepts into Nexus?
- Are error paths complete?
- Are lifetime/ownership rules explicit?
- Are architecture-specific details isolated?
- Is the implementation understandable without hidden assumptions?

Output:

- defects found;
- corrections made;
- unresolved assumptions.

A meaningful correction resets the affected portions for another correctness pass.

### Review 2 — regression, concurrency and integration

Questions:

- What existing AROS behaviour can regress?
- What happens under SMP?
- What locks or memory-ordering rules are assumed?
- Are TLB, IRQ, fault and scheduler interactions correct?
- Does upstream AROS already solve part of this differently?
- Does the change make future upstream synchronization harder?
- Are build/test paths for unchanged AROS still valid?
- What happens on cleanup, failure and partial initialization?

Review against:

- current Nexus branch;
- recorded upstream baseline;
- latest upstream AROS when the subsystem has changed.

Output:

- regression matrix;
- integration concerns;
- test evidence.

### Review 3 — adversarial red-team review

Assume the new design is wrong until evidence shows otherwise.

Try to break:

- security boundary;
- compatibility claim;
- resource ownership;
- lifetime model;
- privilege checks;
- capability validation;
- page permissions;
- error handling;
- restart/recovery;
- concurrency;
- DMA assumptions;
- user/kernel pointer assumptions.

Ask explicitly:

- How can a hostile legacy application abuse this?
- How can a malformed input reach privileged state?
- Can a stale handle regain authority?
- Can a race invalidate a check?
- Can a device bypass CPU page protection?
- Can a Cell stop physical scheduling or interrupts?
- Can a page fault still become a machine halt?
- Is the claimed isolation level overstated?
- Is there a simpler design with fewer trusted components?

Output:

- attack/failure scenarios;
- tests attempted;
- residual risk;
- decision: accept, revise, postpone or reject.

A red-team finding that changes a security or architecture assumption requires a new review cycle.

## 3. Architecture concepts follow the same rule

Documents and concepts are not exempt.

Before an architectural idea becomes an implementation dependency, perform:

1. internal consistency review;
2. source-code reality check against AROS;
3. adversarial/red-team review.

A concept may be downgraded, split, postponed or rejected without being considered a project failure.

## 4. Upstream review is continuous

AROS upstream is active.

Before starting work on a subsystem and again before merge:

1. inspect the latest upstream branch;
2. identify new commits affecting the same code;
3. determine whether they:
   - should be fast-forwarded/merged first;
   - fix a problem Nexus was about to solve;
   - invalidate a Nexus assumption;
   - create a conflict requiring redesign;
4. record the conclusion in the issue or PR.

Nexus must not knowingly replace recent community work with a stale local design.

## 5. Required PR evidence

A non-trivial Nexus PR should contain a review section such as:

```
Review 1 — correctness/scope: PASS
Findings:
- ...

Review 2 — regression/integration: PASS
Upstream checked at: <sha>
Tests:
- ...

Review 3 — red team: PASS WITH RESIDUAL RISKS
Attacks/failures tested:
- ...

Residual risks:
- ...
```

"PASS" means the documented gate was performed; it does not mean the code is proven bug-free.

## 6. Hardware stop rule

Development must pause when a claim depends materially on physical hardware behaviour that QEMU cannot validate with sufficient confidence.

Typical stop conditions include:

- IOMMU/DMA isolation;
- PCIe/NVMe bus-master behaviour;
- interrupt remapping;
- firmware/UEFI quirks;
- physical APIC/chipset behaviour;
- USB/xHCI timing;
- GPU behaviour;
- resume/power state.

At that point:

1. do not continue stacking dependent changes;
2. mark the related issue as blocked by hardware validation;
3. prepare exact test instructions;
4. identify the commit/artifact to test;
5. request real-hardware execution;
6. record results before resuming.

The project must never convert "not tested on hardware" into "probably works".

## 7. Pace rule

A daily work cycle does not imply a daily code commit.

A productive cycle may end with:

- source analysis;
- a rejected approach;
- a refined test;
- documentation;
- upstream integration;
- a new red-team finding;
- a decision to pause.

Stability and architectural clarity are the output; commit count is not.

## 8. Definition of ready

A change is ready for integration only when:

- its scope is clear;
- upstream was checked;
- required tests pass;
- all three reviews are documented;
- red-team findings are resolved or explicitly accepted;
- hardware validation is complete when required;
- the claimed isolation level matches the evidence;
- documentation and issue status are updated.
