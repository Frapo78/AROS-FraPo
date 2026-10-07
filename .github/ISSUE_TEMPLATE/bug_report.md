---
name: Nexus bug report
about: Report a reproducible problem in AROS-FraPo / Nexus
title: ''
labels: 'bug'
assignees: ''
---

## What happened?

Describe the problem clearly and concisely.

## What did you expect?

Describe the expected behaviour.

## Reproduction steps

1.
2.
3.

## Nexus / repository state

- Branch:
- Commit SHA:
- Upstream baseline SHA:
- Related Nexus issue/PR, if any:

## Environment

- Target (for example pc-x86_64):
- Host OS:
- QEMU version / physical hardware:
- CPU count:
- RAM:
- Firmware/boot method:
- Toolchain/compiler:

## Isolation level involved

If relevant, state the highest claimed/proven level:

- L0 Compatibility containment
- L1 CPU memory isolation
- L2 Privilege isolation
- L3 Hardware isolation
- L4 DMA isolation
- L5 Service fault isolation
- Not applicable / unknown

## Logs

Attach or paste the smallest useful:

- serial/debug log;
- panic/fault output;
- build error;
- test output.

For low-level faults include CR2/fault address, instruction pointer and error code when available.

## Regression?

- [ ] Reproduces on the recorded upstream baseline
- [ ] Nexus-only regression
- [ ] Unknown

If you tested both upstream-compatible `master` and `nexus/main`, describe the difference.

## Additional context

Add anything else that helps reproduce or classify the issue.
