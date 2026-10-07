# Nexus x86-64 Baseline Harness

> Status: **v0 — repeatable harness only; G1/G2 are not yet claimed complete**
>
> Ownership: **N — Nexus-owned project tooling**
>
> Tracking: issues #3 and #15

## Purpose

This directory is a thin wrapper around the **upstream AROS build system**.

It does not replace `configure`, MetaMake, `scripts/azure/aros-stage.sh`, or
the upstream boot-ISO rules. If AROS changes its supported build procedure,
Nexus should adapt a small wrapper rather than maintain a second build system.

## Important terminology

"Repeatable" means that the harness records explicit source, toolchain and VM
inputs. It does **not** yet claim byte-identical ISO reproduction.

AROS outputs may contain timestamps and may consume external distfiles. Artifact
SHA-256 values identify exact artifacts; they are not an assertion that separate
rebuilds must have equal hashes.

## Reference-toolchain policy

For baseline v0, every build attempt creates a **fresh AROS cross-toolchain** in
that attempt's private run directory.

This is deliberately slower than caching, but it avoids making the first Nexus
baseline depend on cache validity, relocation or stale host artifacts.

Toolchain caching may be added later only after the uncached reference path is
proven and the cache can demonstrate equivalent results.

## What v0 records

A completed build records:

- source commit and dirty state;
- target/profile;
- GCC/binutils version source;
- host OS/architecture and host compiler versions;
- relevant upstream build/toolchain source identities;
- cross-compiler/linker binary hashes;
- ISO size and SHA-256.

A QEMU run separately records its binary/version and fixed VM configuration.
Wanderer success is a separate manual observation.

## Profiles

### `compat`

Default. Adds only:

- `--target=pc-x86_64`;
- `--with-bootloader=grub2`.

### `diagnostic`

Additionally enables:

`--with-serial-debug=yes`

The diagnostic profile is not equivalent to `compat` for regression claims.

## Toolchain versions

By default, versions come from the checked-out AROS source:

- `config/gcc_def`;
- `config/binutils_def`.

Explicit experiments may set:

```sh
NEXUS_GCC_VERSION=...
NEXUS_BINUTILS_VERSION=...
```

Overrides are recorded and must not silently become the tested project baseline.

The initial source defaults are chosen because they are an explicit property of
the checked-out AROS source. If the real G1 run shows that the current x86-64
tree requires a different community-tested toolchain, that result must be
documented rather than guessed in advance.

## Dirty-tree policy

Dirty source is rejected by default.

```sh
NEXUS_ALLOW_DIRTY=1 scripts/nexus/baseline/build-x86_64.sh
```

is allowed only for experiments. Such output is recorded as dirty and must not
advance the tested baseline.

## Host requirements

The current upstream Azure host-preparation template remains the source of
truth for AROS build dependencies.

The Nexus harness additionally checks for:

- Bash;
- Git;
- Make;
- Python 3;
- host C/C++ compilers;
- `sha256sum` or `shasum`;
- `qemu-system-x86_64` for runtime testing.

Do not duplicate the complete upstream dependency installer here unless a
future pinned CI image/container requires it.

## Build

```sh
scripts/nexus/baseline/build-x86_64.sh
```

Default workspace:

```
$XDG_CACHE_HOME/aros-nexus/baseline
```

falling back to:

```
$HOME/.cache/aros-nexus/baseline
```

Override:

```sh
NEXUS_WORK_ROOT=/path/to/work scripts/nexus/baseline/build-x86_64.sh
```

Diagnostic build:

```sh
NEXUS_PROFILE=diagnostic scripts/nexus/baseline/build-x86_64.sh
```

Every invocation creates an immutable run directory containing its private
build directory, toolchain and artifacts.

The build script:

1. validates target/profile and clean-source policy;
2. records the upstream build/toolchain source identities;
3. builds a fresh upstream AROS cross-toolchain;
4. records compiler/linker hashes;
5. calls upstream `aros-stage.sh core`;
6. invokes upstream `bootiso`;
7. requires a non-empty `distfiles/aros-pc-x86_64.iso`;
8. records the exact artifact hash.

The external ports-source pool remains shared to avoid redownloading large
distfiles. This makes v0 **non-hermetic** and is recorded as a known limitation.

A successful execution is **G1 evidence**, not automatic completion of G1.

## QEMU

The ISO path is explicit:

```sh
scripts/nexus/baseline/run-qemu-x86_64.sh /path/to/aros-pc-x86_64.iso
```

Reference configuration:

- `pc` machine;
- TCG, single thread;
- `qemu64`;
- one vCPU;
- 1024 MiB RAM;
- no network;
- CD-ROM boot;
- serial capture;
- UTC RTC;
- no automatic reboot.

TCG avoids silently depending on host KVM features. QEMU version is recorded
because machine aliases/device models evolve.

Headless diagnostic example:

```sh
NEXUS_QEMU_MODE=headless \
NEXUS_QEMU_TIMEOUT_SECONDS=120 \
scripts/nexus/baseline/run-qemu-x86_64.sh /path/to/iso
```

Timeout/failure remains unverified and returns non-zero.

## Wanderer verification

The QEMU launcher never records boot success.

After an **interactive**, successfully exited run in which Wanderer was visibly
usable:

```sh
scripts/nexus/baseline/record-wanderer-result.sh \
    /path/to/qemu-run pass "Wanderer usable"
```

Optional fourth argument: screenshot/evidence file.

A pass is rejected if:

- the QEMU run is incomplete;
- QEMU exited non-zero;
- the run was headless.

The record contains hashes tying it to the run manifest and ISO.

This manual gate is interim. A deterministic guest-side success signal is
preferred before unattended CI claims Wanderer success.

## Fast self-test

The harness has a no-build/no-real-QEMU self-test:

```sh
scripts/nexus/baseline/selftest.sh
```

It checks:

- invalid target/profile rejection;
- headless pass rejection;
- failed-QEMU pass rejection;
- evidence overwrite rejection;
- run-directory overwrite rejection;
- positive interactive evidence recording.

G0 runs both `bash -n` and this self-test.

## Comparison rule

Baseline and Nexus runs should use the same:

- toolchain input/version policy;
- profile;
- QEMU version;
- VM settings.

Record exact artifact hashes but do not require equal ISO hashes between
separate builds unless bit reproducibility has independently been proven.

## Deliberate non-goals of v0

- no cached reference toolchain;
- no implicit "latest ISO";
- no baseline promotion from dirty source;
- no silent toolchain override;
- no KVM-dependent reference result;
- no network-dependent boot result;
- no "QEMU launched == AROS booted";
- no "compiled == baseline advanced";
- no claim that m68k/ARM/RISC-V are covered by this x86-64 harness.

## Current limitation

This is tooling, not runtime evidence.

G1/G2 remain open until the harness is run on the selected reference host,
the outputs are reviewed, and the result is repeated.

A script committed to Git is not proof that AROS boots.
