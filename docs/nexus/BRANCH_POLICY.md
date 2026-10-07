# Nexus Branch Policy

> Status: required repository policy
>
> This document describes the branch protections Nexus expects. Some protections must be enabled in GitHub repository settings and cannot be enforced by source files alone.

## 1. Branch roles

### `master`

Purpose:

- track `aros-development-team/AROS:master`;
- contain no Nexus-specific implementation;
- advance by reviewed fast-forward from upstream whenever possible.

Rules:

- never force-push;
- never add Nexus-specific commits;
- never rewrite upstream history;
- inspect upstream changes before advancing the recorded Nexus baseline.

### `nexus/main`

Purpose:

- stable Nexus integration branch;
- default public branch;
- contains only reviewed Nexus work plus reviewed upstream synchronization.

Rules:

- non-trivial implementation must arrive through a pull request;
- no force-push;
- no branch deletion;
- required validation checks must pass;
- the mandatory three-review evidence must be present;
- unresolved red-team findings block merge unless explicitly accepted and documented.

### Feature branches

Examples:

- `nexus/address-space-as0`;
- `nexus/fault-domain-classification`;
- `nexus/bootstrap-x86_64`.

Purpose:

- focused implementation or experiment;
- one logical scope;
- one logical integrator responsible for final coherence;
- disposable after integration.

Multiple agents may contribute to one feature branch, but the branch must not become unowned patch accumulation.

A feature branch may fail temporarily. `nexus/main` should not.

## 2. Required GitHub protection for nexus/main

Configure a GitHub branch rule or ruleset for `nexus/main` with at least:

- require a pull request before merging;
- require conversation resolution before merging;
- require status checks to pass;
- block force pushes;
- block branch deletion.

Required checks should include, once GitHub exposes stable check names:

- `Nexus project sanity`;
- inherited source line-ending validation;
- inherited Windows filename validation.

When the x86-64 build/QEMU gates exist, add them before allowing low-level implementation merges.

## 3. Review count versus review passes

GitHub's "required approving reviews" is not a substitute for the Nexus three-pass protocol.

The three required passes are different analyses:

1. Construction — correctness/scope;
2. Integration — regression/concurrency/upstream;
3. Evidence Red Team — active falsification through tests/evidence.

Review 3 follows the rule **NO TEST, EXPLAIN WHY** when an executable adversarial test is not yet possible.

During early development Francesco Poltero may perform multiple passes himself, but they must be separated in purpose and evidence.

Kernel/protection work is H1 and requires human technical review before merge.

Physical-hardware-dependent claims are H2.

Strong release-level L2-L5 security claims are H3 and require independent competent review.

See `VERIFICATION_MODEL.md`.

## 4. No same-step implementation and acceptance

For non-trivial kernel/protection work, creating a change and declaring all reviews complete in one superficial step is not acceptable.

A review pass must inspect the actual resulting diff and evidence.

If Review 1 or Review 2 causes a meaningful code correction:

- the corrected area is reviewed again;
- later passes operate on the corrected version.

If Review 3 changes a trust or architecture assumption:

- the change returns to architecture/correctness review;
- the affected ADR or design document is updated.

## 5. Upstream synchronization

Before a Nexus feature branch is merged:

1. inspect current upstream AROS;
2. check whether the touched files changed upstream;
3. integrate or account for relevant upstream work;
4. repeat affected regression tests.

Do not merge a local implementation whose assumptions are already obsolete upstream.

## 6. Emergency fixes

An emergency fix may reduce normal process only when the stable branch is already broken and the fix is necessary to restore the previous known-good state.

Even then:

- scope must be minimal;
- the reason for bypass must be documented;
- the three review passes must be performed retrospectively before further dependent work.

"Faster development" is not an emergency.

## 7. Current limitation

Repository source files cannot guarantee these GitHub settings.

Until the branch protection/ruleset is enabled in GitHub, the process remains socially enforced rather than technically enforced.

That limitation must remain visible and must not be mistaken for a completed governance control.
