# Nexus bootable image releases

> Policy approved for implementation on 2026-11-01. **No new public ISO or
> USB image is asserted to exist by this document.** This policy takes effect
> only after its workflow and the G1/G2a build harness are merged and verified.

## Cadence and promotion

- **Monthly candidate:** first calendar day of each month, 04:00 UTC,
  plus manual dispatch. Build the exact checked-out `nexus/main` commit.
  GitHub scheduled workflows are best-effort and can be delayed or skipped. **They execute from the repository default branch only**: if that branch is not `nexus/main`, this schedule is not active. Do not modify upstream-tracking `master` to work around this. A reviewed default-branch setting or dispatcher is a separate activation prerequisite.
- **Milestone candidate:** manual dispatch after an accepted roadmap gate
  (G1, G2a, G2b, G2c, then Phase 1 milestones). It uses the same verification.
- **No empty promises:** a failed build, missing manifest, ISO hash mismatch,
  absent QEMU marker or failed CI **blocks publication**. Record failure in
  workflow logs; do not create a misleading release.
- **No false upgrades:** a G2a release remains labelled **early-boot
  diagnostic / pre-release**, even if a calendar date or milestone is reached.
  G2b/G2c and later require their own real-guest and human evidence before
  upgrading the claim or removing the pre-release label.
- **No version drift:** immutable tags, ISO SHA-256, source SHA, build manifest,
  QEMU evidence and gate label travel together. Never silently replace a
  published asset. New artifact = new release tag.
- **Retention:** GitHub Releases hold the accepted ISO and accompanying
  SHA-256 and manifest; short-lived CI logs remain workflow artifacts.
  Do **not** commit binary ISO files into Git history.

## Current scope

Target: `x86_64` BIOS/GRUB boot ISO `aros-pc-x86_64.iso`, run under
one-vCPU resource-bounded QEMU. Initial gate: G1 build + G2a exact early
kernel serial marker. This is a bootable ISO candidate, **not** a claim of
a usable Wanderer desktop, isolation or tested USB hardware.

A raw USB disk image is a **separate future deliverable**: define partition
table, firmware mode, bootloader installation, read-back and QEMU disk boot
tests, then physical USB H2 evidence where hardware claims are made.
Do not rename or `dd` the ISO to `.img` and call it USB-validated.

## Release manifest / evidence

Each published candidate should contain:
- ISO and `SHA256SUMS`;
- exact Git commit and upstream/tested-baseline references;
- G1 build manifest and QEMU run manifest;
- precise achieved gate and **explicit non-claims**;
- runner/toolchain/QEMU identity and a link to the successful workflow run;
- a milestone name when manually triggered.

The release workflow must fail closed if artifacts exceed the hosting limit,
if the release tag already exists, or if evidence is incomplete. It may use
`GITHUB_TOKEN` with `contents: write` only in its publishing job. No
privileged secrets are needed to build or boot the public source.

## Roadmap promotion rules

| Release level | Minimum evidence | What it can claim |
| --- | --- | --- |
| G1 | fresh reproducible x86-64 build, exact ISO hash | ISO built, not booted |
| G2a | G1 + exact serial marker from QEMU | early kernel entry |
| G2b | guest desktop reached with retained evidence | graphical desktop reached |
| G2c | human-confirmed real guest input-response | usable Wanderer interaction |
| Phase 1 | gate-specific protection tests + H1 | only demonstrated mechanisms |

For current reality see [status audit](STATUS_AUDIT_2026-11-01.md),
[baseline](BASELINE.md), [CI strategy](CI_STRATEGY.md), and
[roadmap](ROADMAP.md).

## U/A/N, review and stop conditions

U: upstream AROS source/build; A: no kernel adaptation; N: release automation,
manifests and host verification. B0-B3: no new protection boundary.
H0 for host automation; H1/H2 apply to future protection/hardware claims.

Construction review: exact source, immutable tag, manifest, hash and
resource bounds. Integration review: no fork `master` modification and no
baseline promotion; upstream must be rechecked for each release.
Evidence Red Team: missing marker, forged manifest, changed ISO, existing
tag, incomplete logs, oversized file and scheduled-job delay must not yield
a falsely labelled successful release.

**NO TEST, EXPLAIN WHY:** publishing cannot be accepted until a real scheduled
or manually dispatched workflow builds the ISO, boots QEMU and uploads
the exact matching artifact. Host YAML review alone is E1, not E4.
