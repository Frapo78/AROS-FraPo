# x86-64 Baseline Harness v0 Review — 2026-10-07

> Scope: Phase 0 build/runtime evidence tooling for issues #3 and #15.
>
> Pull request: #20
>
> Ownership: **N — Nexus-owned project tooling**
>
> Result: **ACCEPT TOOLING, KEEP G1/G2 OPEN UNTIL REAL EXECUTION**

## Scope

This review covers:

- `scripts/nexus/baseline/build-x86_64.sh`;
- `scripts/nexus/baseline/run-qemu-x86_64.sh`;
- `scripts/nexus/baseline/record-wanderer-result.sh`;
- `scripts/nexus/baseline/selftest.sh`;
- baseline-harness documentation;
- the related `Nexus project sanity` checks.

The work does **not** modify AROS operating-system source code.

The harness wraps upstream AROS build machinery rather than replacing it.

## Review 1 — correctness and scope

### Goal

Verify that the harness:

- remains a thin wrapper around upstream;
- does not overstate what a compile or QEMU launch proves;
- records enough provenance for later comparison;
- fails closed on malformed or ambiguous local evidence;
- has cheap automated tests for its own control logic.

### Findings

#### R1-F1 — incremental patch corruption

Early edits produced two real script defects:

- a truncated build-attempt identifier;
- a duplicated/corrupted QEMU runner body.

### Correction

The affected scripts were rebuilt from complete known-good contents rather than patched further in place.

The repository gate now runs `bash -n` over Nexus shell scripts.

#### R1-F2 — documentation drift

The harness README temporarily described:

- cache behavior;
- provenance data;
- dirty-source behavior;

that no longer matched the actual implementation.

### Correction

The README was rewritten to describe the final v0 contract only.

#### R1-F3 — self-test contract drift

The first behavioural self-test still assumed that the QEMU runner accepted an arbitrary ISO.

After provenance binding was introduced, the test no longer exercised the real contract.

### Correction

The self-test now constructs a synthetic successful G1 build manifest and verifies the full G1-artifact-to-G2-run chain.

#### R1-F4 — syntax checks were insufficient

A shell script can be syntactically valid while accepting false evidence.

### Correction

`Nexus project sanity` now runs a behavioural self-test in addition to `bash -n`.

The self-test covers positive and negative evidence paths without compiling AROS or launching real QEMU.

### Review 1 result

**PASS after correction and repeated CI execution.**

## Review 2 — regression, upstream integration and scope isolation

### Upstream state

Current upstream head reviewed:

`aros-development-team/AROS@e2cb3acaace051317da486a5bfd574cda726540d`

New upstream changes since the previous Nexus integration affect Raspberry Pi:

- serial/debug routing;
- Bluetooth patchram/firmware.

They do not change the x86-64 stage driver, toolchain flow, boot-ISO path or QEMU assumptions used by this harness.

Fork `master` was fast-forwarded and the changes were merged into `nexus/main` through PR #21 before final integration of this work.

### U/A/N classification

- upstream `configure`, MetaMake and `scripts/azure/aros-stage.sh`: **U — upstream-owned**;
- Nexus baseline wrapper/scripts: **N — Nexus-owned tooling**;
- no A-class modification to AROS build implementation is introduced.

### Finding R2-F1 — accidental upstream regression in feature tree

During branch refresh, an intermediate tree accidentally reverted four ARM64/Raspberry Pi files relative to current `nexus/main`.

### Correction

The feature tree was reconstructed from the exact current `nexus/main` tree, with only Nexus harness files overlaid.

A final compare against `nexus/main` was used as a hard scope check.

### Final scope rule

Before merge, the PR diff must contain only Nexus baseline tooling, its project-sanity integration and review/status documentation.

No AROS implementation file may be modified.

### Review 2 result

**PASS after upstream synchronization and tree repair.**

## Review 3 — adversarial red-team

The red-team attempted to create false-positive or contaminated baseline evidence.

### R3-F1 — stale/shared toolchain state

A shared toolchain cache could let a previous build satisfy a new baseline attempt.

### Correction

v0 uses a fresh cross-toolchain directory for every attempt.

Caching is deferred.

### R3-F2 — hidden host ccache state

The upstream stage driver enables ccache.

Fresh build directories alone therefore did not guarantee fresh compilation.

### Correction

The reference harness sets:

`CCACHE_DISABLE=1`

for baseline evidence builds.

### R3-F3 — shared workspace race/contamination

Shared build or port-source directories could create cross-attempt state or concurrent-build races.

### Correction

Build directory, toolchain directory and port-source directory are all attempt-local in v0.

### R3-F4 — dirty source could be promoted accidentally

A dirty-source override complicates provenance and makes exact reconstruction ambiguous.

### Correction

The baseline path is clean-worktree-only.

Dirty experiments must use another workflow and cannot masquerade as baseline evidence.

### R3-F5 — build output inside the source tree

A work root inside the Git worktree could contaminate source status or interact with the build unexpectedly.

### Correction

`NEXUS_WORK_ROOT` is rejected when it resolves inside the source tree.

### R3-F6 — arbitrary ISO accepted by QEMU runner

Without provenance binding, G2 could be performed on an ISO unrelated to G1.

### Correction

The QEMU runner requires the sibling G1 build manifest and verifies:

- manifest format;
- unique required keys;
- successful final build state;
- zero build exit status;
- artifact path;
- artifact SHA-256;
- source/profile/toolchain identity.

The run manifest stores the build-manifest hash.

### R3-F7 — QEMU executable ambiguity

Recording only a QEMU version string does not uniquely identify the runtime binary.

### Correction

The run manifest records:

- QEMU command;
- resolved binary path;
- SHA-256;
- version string.

### R3-F8 — false Wanderer pass

A user could otherwise mark:

- a headless run;
- a QEMU error;
- an incomplete or inconsistent run;

as a successful Wanderer boot.

### Correction

A manual `pass` requires:

- supported run-manifest format;
- exactly one required key;
- `FINAL_STATUS=vm-exited-unverified`;
- QEMU exit code 0;
- interactive mode.

Existing verification is not overwritten by default.

### R3-F9 — evidence tampering / ambiguous keys

Appending a duplicate key to a manifest can change how different parsers interpret it.

### Correction

Required manifest keys must appear exactly once.

The behavioural self-test explicitly attacks duplicate keys, inconsistent final state and modified ISO content.

## Automated evidence

At the final reviewed implementation stage, `Nexus project sanity` validates:

- required Nexus files;
- local Markdown links;
- shell syntax;
- baseline harness behavioural self-test;
- core Nexus process-document invariants.

Inherited repository checks also validate:

- source line endings;
- Windows filename compatibility.

## Residual risks

These are deliberately **not** hidden or solved by v0:

- a full AROS cross-toolchain/core/ISO build has not yet been executed through the harness;
- a real QEMU boot has not yet been executed through the harness;
- Wanderer success remains a human observation;
- host package versions are not pinned by Nexus;
- AROS build-time external downloads are not yet hermetic/mirrored;
- `pc` and `qemu64` semantics remain QEMU-version-dependent, although binary identity is recorded;
- optional GCC/binutils overrides remain possible and must not silently become the tested baseline;
- manifests are local evidence records, not cryptographically signed attestations;
- bit-for-bit ISO reproducibility is not claimed.

## Security/isolation claim

This tooling advances **no L0-L5 runtime isolation level**.

It improves evidence quality only.

## Decision

**Accept the baseline harness v0 tooling.**

Do not close G1 or G2 merely because the scripts and self-tests pass.

The next safe action is to run the harness in a suitable reference build environment, inspect the generated toolchain/ISO evidence, boot the exact bound ISO under QEMU, and repeat the result.

Only then should the project consider advancing the tested baseline or unblocking P1.1.
