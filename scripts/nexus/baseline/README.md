# Nexus x86-64 Baseline Harness

> Status: **v0 — repeatable harness only; G1/G2 are not yet complete**
>
> Ownership: **N — Nexus-owned project tooling**
>
> Tracking: issues #3 and #15

## Purpose

This directory is a thin wrapper around the **upstream AROS build system**.

It does not replace:

- `configure`;
- MetaMake;
- `scripts/azure/aros-stage.sh`;
- upstream boot-ISO rules.

Nexus should adapt a small wrapper when upstream changes rather than maintain a
second build system.

## Terminology

"Repeatable" means the harness records explicit source, toolchain and VM inputs.

It does **not** claim byte-identical ISO reproduction. AROS output may contain
timestamps and may consume external network content. Artifact SHA-256 values
identify exact artifacts; they do not assert that two rebuilds must match.

## Reference build policy

The v0 reference path is deliberately conservative:

- clean Git worktree only;
- one private run directory per attempt;
- fresh AROS cross-toolchain per attempt;
- private port-source directory per attempt;
- `CCACHE_DISABLE=1`;
- workspace must be outside the Git worktree.

This is slower than caching but removes stale-cache, shared-workspace and
concurrent-build ambiguity from the first baseline.

Caching can be added later only after the uncached path is proven.

## What a completed build records

- source commit;
- target/profile;
- GCC/binutils version and whether it came from AROS defaults or an override;
- host OS/architecture and host compiler versions;
- upstream build/toolchain source identities;
- submodule-state manifest hash;
- generated cross-compiler/linker hashes and versions;
- build configuration arguments;
- ISO size and SHA-256.

The `TOOLCHAIN_INPUT_KEY` is an evidence/comparison identifier. It is not used
as a cache key in v0.

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

Defaults come from the checked-out AROS source:

- `config/gcc_def`;
- `config/binutils_def`.

Explicit experiments may set:

```sh
NEXUS_GCC_VERSION=...
NEXUS_BINUTILS_VERSION=...
```

Overrides are recorded and must not silently become the tested project baseline.

## Host requirements

The current upstream Azure host-preparation template remains the source of
truth for AROS build dependencies.

The harness additionally checks for the local commands it directly uses,
including Bash, Git, Make, Python 3, host C/C++ compilers and SHA-256 support.
Runtime testing requires `qemu-system-x86_64` or an explicitly supplied QEMU
binary.

Do not duplicate the full upstream dependency installer here unless a future
pinned CI image/container requires it.

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
NEXUS_WORK_ROOT=/path/outside/source \
scripts/nexus/baseline/build-x86_64.sh
```

Diagnostic build:

```sh
NEXUS_PROFILE=diagnostic scripts/nexus/baseline/build-x86_64.sh
```

A successful execution is **G1 evidence**, not automatic completion of G1.

## QEMU provenance chain

The QEMU runner accepts only the exact ISO produced by the harness:

```sh
scripts/nexus/baseline/run-qemu-x86_64.sh \
    /path/to/run/artifacts/aros-pc-x86_64.iso
```

The ISO must have a sibling `build-manifest.txt`.

Before QEMU starts, the runner verifies:

- build manifest format;
- exactly one required provenance value per key;
- `FINAL_STATUS=success`;
- build exit code 0;
- recorded artifact path equals the supplied ISO path;
- ISO SHA-256 matches the build manifest;
- source/profile/toolchain identity is present.

The run manifest then records:

- source/profile/toolchain identity;
- build-manifest SHA-256;
- ISO SHA-256;
- QEMU path, SHA-256 and version;
- VM configuration.

This creates an explicit **G1 artifact → G2 run** evidence chain.

## Reference QEMU configuration

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

TCG avoids silently depending on host KVM features.

QEMU binary hash and version are recorded because machine aliases, CPU models
and device behavior evolve.

Headless diagnostic example:

```sh
NEXUS_QEMU_MODE=headless \
NEXUS_QEMU_TIMEOUT_SECONDS=120 \
scripts/nexus/baseline/run-qemu-x86_64.sh /path/to/artifact.iso
```

Timeout/failure remains unverified and returns non-zero.

## Wanderer verification

The QEMU runner never records boot success.

After an **interactive**, successfully exited run in which Wanderer was visibly
usable:

```sh
scripts/nexus/baseline/record-wanderer-result.sh \
    /path/to/qemu-run pass "Wanderer usable"
```

Optional fourth argument: screenshot/evidence file.

A pass is rejected when:

- the run manifest format/required keys are invalid;
- required manifest keys are duplicated;
- QEMU did not finish with the expected successful final state;
- QEMU exited non-zero;
- the run was headless;
- a verification already exists.

The verification is bound to the run-manifest and ISO hashes.

Manual observation is interim. A deterministic guest-side marker is preferred
before unattended CI can claim Wanderer success.

## Fast self-test

```sh
scripts/nexus/baseline/selftest.sh
```

This test does **not** compile or boot AROS. It uses synthetic evidence and a
fake QEMU executable to exercise the harness contract.

It checks at least:

- invalid target/profile rejection;
- work-root-inside-source rejection;
- ISO-without-build-manifest rejection;
- G1 provenance propagation into a QEMU run;
- QEMU binary identity recording;
- headless pass rejection;
- failed-QEMU pass rejection;
- verification overwrite rejection;
- duplicate manifest-key rejection;
- inconsistent final-state rejection;
- tampered ISO rejection.

`Nexus project sanity` runs both `bash -n` and this self-test.

## Comparison rule

Baseline and Nexus runs should use the same:

- tested baseline relationship;
- toolchain policy;
- profile;
- QEMU binary/version;
- VM settings.

Record exact artifact hashes but do not require equal ISO hashes between
separate builds unless bit reproducibility has independently been demonstrated.

## Deliberate non-goals of v0

- no cached reference toolchain;
- no shared build/toolchain/port-source workspace between attempts;
- no dirty-source baseline;
- no implicit "latest ISO";
- no arbitrary unbound ISO in the QEMU baseline path;
- no KVM-dependent reference result;
- no network-dependent **VM boot** result;
- no "QEMU launched == AROS booted";
- no "compiled == baseline advanced";
- no claim that other CPU targets are covered.

The AROS build itself may still download external source/distfiles. Therefore v0
is not yet a hermetic build environment.

## Current limitations

This is tooling, not runtime evidence.

G1/G2 remain open until the harness is executed on the selected reference host,
its outputs are reviewed, and the result is repeated.

Additional residual limitations include:

- host package versions are not pinned by Nexus;
- build-time external downloads are not hermetically mirrored;
- the `pc` QEMU alias is version-dependent, although QEMU identity is recorded;
- Wanderer success is still a manual observation.

A script committed to Git is not proof that AROS boots.
