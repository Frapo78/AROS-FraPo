# Nexus x86-64 Baseline Harness

> Status: **v0 — harness only, G1/G2 not yet claimed complete**
>
> Ownership: **N — Nexus-owned project tooling**
>
> Tracking: issues #3 and #15

## Purpose

This directory provides a deliberately thin, reproducible wrapper around the
**upstream AROS build system**.

It does not replace:

- `configure`;
- MetaMake;
- `scripts/azure/aros-stage.sh`;
- the upstream boot-ISO rules.

That is intentional. If AROS changes its supported build procedure, Nexus
should adapt a small wrapper rather than maintain a second build system.

## What v0 proves

When successfully executed, the harness can record independently:

1. the exact source commit and dirty state;
2. the AROS toolchain inputs used;
3. a successful `pc-x86_64` core/ISO build;
4. the exact ISO SHA-256;
5. the QEMU version and machine configuration used for a run;
6. a separate human-observed Wanderer result.

It **does not** turn a QEMU process launch into a boot-success claim.

## Profiles

### `compat` — default

Uses the normal AROS configuration plus:

- target `pc-x86_64`;
- GRUB2 bootloader.

No Nexus diagnostic build flag is added.

### `diagnostic`

Adds:

`--with-serial-debug=yes`

This profile exists to collect debug evidence. It is not treated as bit-for-bit
equivalent to the compatibility profile.

## Toolchain policy

By default the harness uses the toolchain versions declared by the checked-out
AROS source:

- `config/gcc_def`;
- `config/binutils_def`.

The resolved versions and the Git tree IDs of `tools/crosstools` and
`tools/collect-aros` are recorded.

The toolchain cache key includes those values. A kernel-only source change can
reuse the same toolchain, while a change to the upstream toolchain sources
invalidates the cache.

Explicit experiments may set:

```sh
NEXUS_GCC_VERSION=...
NEXUS_BINUTILS_VERSION=...
```

Such overrides are recorded in the manifest and must not be confused with the
default baseline.

## Dirty-tree policy

The build refuses a dirty Git worktree by default.

For an intentional local experiment:

```sh
NEXUS_ALLOW_DIRTY=1
```

may be used, but the resulting manifest records `SOURCE_DIRTY=yes` and the
result must not be promoted to the tested project baseline.

## Ubuntu host requirements

The AROS upstream Azure pipeline currently installs the following classes of
packages for Linux builds:

- build tools: `gawk bison flex automake cmake gperf nasm`;
- image/media tools: `netpbm genisoimage mtools xorriso`;
- Python: `python3-mako python3-yaml python3-distutils-extra`;
- toolchain helpers: `gcc-multilib g++ ccache libclang-dev`;
- libraries: `libpng-dev zlib1g-dev libxcursor-dev libgl1-mesa-dev libasound2-dev`;
- utilities: `jlha-utils wget liblzma-dev libswitch-perl`.

For the runtime harness also install the package providing
`qemu-system-x86_64` (commonly `qemu-system-x86`).

The upstream dependency list remains the source of truth. Do not fork it here
into an installer script unless CI requires a pinned container/image later.

## Build

From any directory:

```sh
scripts/nexus/baseline/build-x86_64.sh
```

The default workspace is outside the Git worktree:

```
$XDG_CACHE_HOME/aros-nexus/baseline
```

or, if `XDG_CACHE_HOME` is unset:

```
$HOME/.cache/aros-nexus/baseline
```

Override with:

```sh
NEXUS_WORK_ROOT=/path/to/work scripts/nexus/baseline/build-x86_64.sh
```

A diagnostic build is:

```sh
NEXUS_PROFILE=diagnostic scripts/nexus/baseline/build-x86_64.sh
```

The script:

1. rejects unsupported targets/profiles;
2. rejects a dirty source tree by default;
3. computes a toolchain cache key from upstream toolchain sources;
4. calls upstream `scripts/azure/aros-stage.sh toolchain`;
5. calls upstream `scripts/azure/aros-stage.sh core`;
6. calls the configured upstream `bootiso` target;
7. verifies that `distfiles/aros-pc-x86_64.iso` exists and is non-empty;
8. copies it to an immutable commit/profile/toolchain/attempt artifact directory;
9. records SHA-256 and build metadata.

A successful build is **G1 evidence**, but issue #3 is not complete until the
procedure has actually been executed on the chosen reference host and repeated.

## QEMU run

Run the exact ISO explicitly:

```sh
scripts/nexus/baseline/run-qemu-x86_64.sh \
    /path/to/aros-pc-x86_64.iso
```

The default configuration is deliberately conservative:

- TCG, single thread;
- `qemu64` CPU model;
- one vCPU;
- 1024 MiB RAM;
- `pc` machine;
- no network;
- CD-ROM boot;
- serial output captured to a file;
- UTC RTC;
- no automatic reboot.

The QEMU version is recorded because the `pc` machine alias and device models
can evolve across QEMU releases.

For non-graphical diagnostic execution:

```sh
NEXUS_QEMU_MODE=headless \
NEXUS_QEMU_TIMEOUT_SECONDS=120 \
scripts/nexus/baseline/run-qemu-x86_64.sh /path/to/iso
```

A headless run cannot by itself establish that Wanderer is usable.

## Wanderer verification

The launcher always records the run as **unverified**.

After visually checking that the desktop is usable, record the observation
separately:

```sh
scripts/nexus/baseline/record-wanderer-result.sh \
    /path/to/qemu-run pass "Wanderer usable"
```

An optional screenshot or other evidence file may be supplied as the fourth
argument. Its SHA-256 is recorded.

This manual marker is an interim G2 mechanism. It should later be replaced or
supplemented by a deterministic guest-side success signal suitable for CI.

## Comparison rule

When comparing baseline AROS with a Nexus change:

- use the same host;
- use the same toolchain key;
- use the same profile;
- use the same QEMU binary/version;
- use the same QEMU settings;
- record both ISO hashes;
- do not compare a `compat` build with a `diagnostic` build as if they were
  equivalent.

## Red-team constraints

The harness deliberately refuses several shortcuts:

- no implicit "latest ISO" selection;
- no dirty baseline by default;
- no silent toolchain-version override;
- no KVM acceleration in the reference command;
- no network dependency in the reference VM;
- no automatic Wanderer success claim;
- no baseline advancement merely because compilation succeeded.

## Current limitation

This v0 harness has been designed from the current upstream build rules but its
full G1/G2 result is **not yet asserted** until it is executed in a suitable
build environment.

A script committed to Git is not build evidence.
