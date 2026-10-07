# Nexus pull request

## Related issue

Closes/relates to:

## Integrator

Logical integrator responsible for final coherence:

## Goal

What single observable result does this PR deliver?

## Non-goals

What is deliberately excluded?

## Scope

Describe the smallest logical change.

## Ownership / bridgeability

- U/A/N classification:
- B0/B1/B2/B3 if applicable:
- Why this classification is correct:

## Upstream state

- Recorded tested Nexus baseline:
- Latest upstream AROS commit reviewed:
- Relevant upstream changes:
- Integration decision:

## Compatibility impact

- ABI v1:
- protected AROS:
- m68k compatibility:
- upstream mergeability:
- architecture/endianness assumptions:

## Acceptance criteria

Observable PASS conditions:

- [ ]

## Negative / red-team criteria

What must fail or remain impossible?

- [ ]

## Evidence

- Highest evidence class achieved (E0-E7):
- Exact automated tests:
- Exact QEMU environment:
- Exact hardware environment:
- Untested cases:

## Claimed isolation level

Highest level actually demonstrated:

- [ ] No isolation claim
- [ ] L0 — compatibility-domain classification/containment
- [ ] L1 — CPU memory isolation
- [ ] L2 — privilege isolation
- [ ] L3 — hardware/MMIO/IRQ isolation
- [ ] L4 — DMA isolation
- [ ] L5 — service fault isolation

Evidence supporting the claim:

## Human / hardware gate

Highest required gate:

- [ ] H0 — automated evidence sufficient
- [ ] H1 — human technical review required
- [ ] H2 — real-hardware evidence required
- [ ] H3 — independent expert review required for release/security claim

Required evidence/reviewer:

## Review 1 — Construction

Status:

Findings:

Corrections made:

Open assumptions:

## Review 2 — Integration

Status:

Regression matrix:

SMP/concurrency findings:

Portability findings:

Upstream comparison:

Tests repeated:

## Review 3 — Evidence Red Team

Status:

Falsification hypothesis:

Adversarial/negative test:

Result:

Evidence class:

### NO TEST, EXPLAIN WHY

Complete only if no executable adversarial test was possible:

- Why not:
- Strongest concrete counterexample/failure scenario:
- Evidence available now:
- Future prerequisite for executable test:

Residual risks:

Decision:

- [ ] Accept
- [ ] Revise and repeat affected reviews
- [ ] Postpone
- [ ] Reject

## Hardware validation

- [ ] Not required
- [ ] Required and completed
- [ ] Required — PR remains blocked

Hardware tested:

Evidence/result:

Recovery/risk notes:

## Documentation

List ADR/architecture/test/review documentation updated by this PR.
