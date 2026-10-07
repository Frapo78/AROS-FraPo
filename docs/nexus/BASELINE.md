# Nexus Baseline

> Baseline established: 2026-10-07
>
> Upstream repository: `aros-development-team/AROS`
>
> Upstream branch: `master`
>
> Baseline commit: `2edd46536d08e3b54ecd1315f337a9b7de896f3a`

## Purpose

Nexus must always be able to answer:

> Which exact upstream AROS state was this experiment based on?

The fork remains active while upstream AROS continues to change. A documented baseline prevents boot results, regressions and architectural conclusions from becoming ambiguous.

## Current baseline

The first implementation baseline is:

```
aros-development-team/AROS
master
2edd46536d08e3b54ecd1315f337a9b7de896f3a
```

At the time the baseline was recorded, the fork's `master` branch was fast-forwarded to that same commit and then merged into `nexus/main`.

## Branch roles

### `master`

Purpose:

- upstream tracking only;
- no Nexus-specific changes;
- fast-forward to upstream where possible.

### `nexus/main`

Purpose:

- stable Nexus integration line;
- documentation;
- reviewed Nexus implementation work;
- periodic merges from `master`.

### `nexus/bootstrap-x86_64`

Purpose:

- x86-64 implementation experiments;
- short, measurable bootstrap work;
- should be rebased or refreshed from `nexus/main` before implementation starts.

Feature work should normally branch from `nexus/main` or the current approved implementation branch rather than directly modifying `master`.

## Upstream sync rule

Before beginning a new architecture milestone:

1. check current upstream `master`;
2. fast-forward fork `master`;
3. inspect upstream changes touching relevant Nexus areas;
4. merge `master` into `nexus/main`;
5. run baseline build/tests;
6. record a new baseline SHA only when the project intentionally advances its reference point.

Not every upstream commit requires changing this document immediately.

A baseline changes when Nexus decides that a newer upstream state is the reference against which the next milestone is measured.

## Areas requiring special review on sync

Changes under these paths deserve explicit Nexus review:

- `arch/*/kernel`;
- `arch/*/exec`;
- `arch/all-pc/kernel`;
- `rom/kernel`;
- `rom/exec`;
- `rom/hidds`;
- `rom/devs`;
- `compiler`;
- build/configuration files affecting x86-64;
- scheduler/SMP tests;
- MMU/page/protection tests.

A conflict in one of these areas should not be resolved mechanically without checking whether upstream has already changed the architectural assumption Nexus is working on.

## Baseline evidence

For each implementation milestone, record:

- upstream baseline SHA;
- Nexus commit SHA;
- configure command;
- compiler/toolchain version;
- QEMU version;
- QEMU command line;
- CPU count;
- memory size;
- boot-media generation;
- test results;
- serial/debug log hash or artifact.

This turns "it booted" into a reproducible engineering result.

## First implementation gate

No Nexus runtime code should be considered ready for review until the reference x86-64 baseline can be built and booted independently of Nexus-specific behaviour.

That work is tracked by the Phase 0 QEMU baseline task.
