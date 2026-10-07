# Nexus x86-64 Baseline Harness

> Status: **v0 — repeatable harness only; G1/G2 are not yet claimed complete**
>
> Ownership: **N — Nexus-owned project tooling**
>
> Tracking: issues #3 and #15

## Purpose

This directory provides a deliberately thin wrapper around the
**upstream AROS build system**.

It does not replace:

- `configure`;
- MetaMake;
- `scripts/azure/aros-stage.sh`;
- the upstream boot-ISO rules.

That is intentional. If AROS changes its supported build procedure, Nexus
should adapt a small wrapper rather than maintain a second build system.

## Important terminology

"Repeatable" here means that the harness records and reuses explicit source,
toolchain and VM inputs.

It does **not** yet claim that two builds produce byte-identical ISOs.

AROS build outputs may contain timestamps and may consume external distfiles.
The exact artifact SHA-256 and the post-build external-source-pool manifest are
therefore evidence identifiers, not an assertion of deterministic binary
reproduction.

A stronger hermetic/bit-reproducible build can be pursued later if it provides
real value to Nexus validation.

## What v0 records

When successfully executed, the harness records independently:

1. exact source commit and dirty state;
2. target/profile;
3. source-selected or explicitly overridden GCC/binutils versions;
4. host OS/architecture;
5. toolchain source-tree identity and binary hashes;
6. successful `pc-x86_64` core/ISO build;
7. ISO size and SHA-256;
8. post-build external source-pool manifest;
9. QEMU binary/version and machine configuration;
10. a separate human-observed Wanderer result.

It **never** turns a QEMU process launch into a boot-success claim.

## Profiles

### `compat` — default

Uses the normal AROS configuration plus:

- target `pc-x86_64`;
- GRUB2 bootloader.

No Nexus diagnostic flag is added.

### `diagnostic`

Adds:

`--with-serial-debug=yes`

This profile exists to collect debug evidence. It is not treated as equivalent
to the compatibility profile for regression comparison.

## Toolchain policy

By default the harness uses the versions declared by the checked-out AROS
source:

- `config/gcc_def`;
- `config/binutils_def`.

An explicit experiment may override them:

```sh
NEXUS_GCC_VERSION=...
NEXUS_BINUTILS_VERSION=...
```

Overrides are recorded and must not silently become the project baseline.

The toolchain cache key includes:

- host OS/architecture;
- AROS target;
- GCC/binutils versions;
- `tools/crosstools` Git tree;
- `tools/collect-aros` Git tree.

A cache entry is reused only when its expected compiler/linker binaries exist
and still match the hashes stored in the Nexus marker.

This mirrors the upstream idea of caching toolchains while making the reused
binary identity explicit.

## Dirty-tree policy

The build refuses a dirty worktree by default.

For an intentional local experiment:

```sh
NEXUS_ALLOW_DIRTY=1
```

may be used, but:

- `SOURCE_DIRTY=yes` is recorded;
- the artifacts are placed under a `-dirty` source key;
- such evidence must not advance the tested baseline.

## Host requirements

The upstream AROS Azure pipeline is the source of truth for build dependencies.

Its current Linux preparation includes packages in these groups:

- build tools: `gawk bison flex automake cmake gperf nasm`;
- image/media tools: `netpbm genisoimage mtools xorriso`;
- Python: `python3-mako python3-yaml python3-distutils-extra`;
- toolchain helpers: `gcc-multilib g++ ccache libclang-dev`;
- libraries: `libpng-dev zlib1g-dev libxcursor-dev libgl1-mesa-dev libasound2-dev`;
- utilities: `jlha-utils wget liblzma-dev libswitch-perl`.

The harness additionally expects:

- `git`;
- `make`;
- `bash`;
- `python3`;
- SHA-256 support via `sha256sum` or `shasum`;
- `qemu-system-x86_64` for runtime testing.

Do not create a fork-specific dependency installer while the upstream list is
sufficient. A pinned CI image/container can be added later if required.

## Build

```sh
scripts/nexus/baseline/build-x86_64.sh
```

Default workspace:

```
$XDG_CACHE_HOME/aros-nexus/baseline
```

or:

```
$HOME/.cache/aros-nexus/baseline
```

Override:

```sh
NEXUS_WORK_ROOT=/path/to/work scripts/nexus/baseline/build-x86_64.sh
```

Diagnostic profile:

```sh
NEXUS_PROFILE=diagnostic scripts/nexus/baseline/build-x86_64.sh
```

The script creates a new immutable attempt directory for every invocation.

It then:

1. rejects unsupported targets/profiles;
2. rejects dirty source by default;
3. computes/verifies a host-aware toolchain cache key;
4. calls upstream `scripts/azure/aros-stage.sh toolchain` when needed;
5. calls upstream `scripts/azure/aros-stage.sh core`;
6. invokes the configured upstream `bootiso` target;
7. requires a non-empty `distfiles/aros-pc-x86_64.iso`;
8. records the exact artifact hash;
9. records toolchain binary hashes;
10. snapshots the external-source pool into a checksum manifest.

The ports-source manifest is provenance for the pool state after the build. It
is **not** a claim that every file in that pool was consumed by that build.

A successful execution is G1 evidence. It does not close #3 until the selected
reference environment has actually produced and repeated the expected result.

## QEMU run

The ISO path is always explicit:

```sh
scripts/nexus/baseline/run-qemu-x86_64.sh \
    /path/to/aros-pc-x86_64.iso
```

Reference settings:

- machine: `pc`;
- accelerator: TCG, single thread;
- CPU model: `qemu64`;
- one vCPU;
- 1024 MiB RAM;
- no network;
- CD-ROM boot;
- serial capture;
- UTC RTC;
- no automatic reboot.

TCG is intentional: the reference run should not silently depend on host KVM
features.

The QEMU version is recorded because QEMU machine aliases and device models
evolve.

For a non-graphical diagnostic run:

```sh
NEXUS_QEMU_MODE=headless \
NEXUS_QEMU_TIMEOUT_SECONDS=120 \
scripts/nexus/baseline/run-qemu-x86_64.sh /path/to/iso
```

A timeout is recorded as unverified and returns a non-zero status.

## Wanderer verification

QEMU always finishes **unverified**.

After an interactive run exits successfully and Wanderer was visibly usable:

```sh
scripts/nexus/baseline/record-wanderer-result.sh \
    /path/to/qemu-run pass "Wanderer usable"
```

Optional fourth argument: screenshot/evidence file.

A manual pass is rejected when:

- the run did not finish;
- QEMU exited non-zero;
- the run was headless.

The verification record is bound to:

- run-manifest SHA-256;
- ISO SHA-256;
- QEMU final status.

This is intentionally conservative.

Manual observation is an interim G2 mechanism. A deterministic guest-side
success signal should replace or supplement it before unattended CI can claim
Wanderer success.

## Comparison rule

A baseline/Nexus comparison should use:

- same tested source baseline relationship;
- same toolchain key;
- same profile;
- same QEMU binary/version;
- same QEMU settings;
- explicit artifact hashes.

Do not compare `compat` and `diagnostic` as if they were equivalent.

Do not require ISO SHA-256 equality between separate rebuilds unless/ until
AROS build reproducibility has itself been demonstrated.

## Red-team constraints

The harness deliberately rejects:

- implicit "latest ISO" selection;
- evidence overwrite by default;
- dirty baseline promotion;
- silent toolchain override;
- unchecked toolchain-cache corruption;
- host-acceleration dependence in the reference VM;
- network dependence in the reference VM;
- headless/manual Wanderer false positives;
- "QEMU launched" == "AROS booted";
- "compiled" == "baseline advanced".

## Current limitation

This v0 harness is source-reviewed tooling, not runtime evidence.

G1 and G2 remain open until the scripts are executed on the selected reference
host, their outputs are reviewed, and the run is repeated.

A script committed to Git is not proof that the system boots.
