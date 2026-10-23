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

## Bounded serial-marker mode

For unattended QEMU evidence, the runner can wait for one exact serial marker:

```sh
NEXUS_QEMU_MODE=headless \
NEXUS_QEMU_EXPECT_MARKER='AROS64 - The AROS Research OS' \
NEXUS_QEMU_TIMEOUT_SECONDS=60 \
scripts/nexus/baseline/run-qemu-x86_64.sh /path/to/artifact.iso
```

Marker mode:

- validates the same G1 build provenance first;
- starts QEMU once;
- polls the captured serial log;
- exits as soon as the requested marker is observed;
- records `FINAL_STATUS=marker-reached`;
- records `MARKER_REACHED_FINAL=yes`;
- returns exit 124 on marker timeout;
- fails if QEMU exits before the marker.

A marker proves **only that named checkpoint**.

The initial CI marker:

`AROS64 - The AROS Research OS`

is the existing upstream x86-64 kernel banner. It is classified as G2a early-kernel evidence and does not imply Exec, DOS, Wanderer, SMP or isolation success.

## GitHub Actions usage

The resource-aware workflow is:

`.github/workflows/nexus-qemu.yml`

It deliberately does not run on every push or every PR update.

Normal automatic PR execution is restricted to relevant low-level paths and selected PR lifecycle events. Explicit reruns use `workflow_dispatch`.

The workflow:

- uses one vCPU and TCG;
- uses a hard job timeout and marker timeout;
- cancels obsolete runs for the same PR/ref;
- stops QEMU immediately when the required marker is found;
- uploads only short-lived logs/manifests;
- does not upload the ISO by default.

The policy itself is tested by:

`scripts/nexus/verify-qemu-policy.sh --selftest`

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
- marker-found success;
- marker-timeout failure;
- QEMU-exit-before-marker failure;
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


## 2026-10-13 task contract: opt-in timeout framebuffer diagnostics

- **Goal:** when an existing bounded G2a marker test times out, optionally request one
  QEMU monitor framebuffer snapshot to distinguish a blank VM from a visible
  firmware/GRUB/kernel error. The screenshot is diagnostic, never boot evidence.
- **Non-goals:** change AROS or the kernel, alter the existing ISO, change G2a's
  marker/exit-code criteria, extend CI runtime, enable extra CPUs or devices,
  introduce an automatic scheduled QEMU run, or claim Wanderer.
- **Preconditions:** the normal G1-bound ISO and QEMU runner; Python 3 for the
  optional HMP helper; an isolated UNIX monitor socket within the result dir.
- **Ownership:** U = upstream OS and ISO build (untouched); N = diagnostic
  harness/helper/tests/workflow; A = none. B0–B3 are not applicable.
  All CR3/IRQ/memory/device/DMA authority remains legacy-owned.
- **Integrator:** Frapo78, on the existing focused `nexus/qemu-ci` branch.
- **Acceptance:** opt-in only; one HMP screendump near marker timeout; retain a
  non-empty PPM evidence file if generated; preserve `marker-timeout`, exit 124,
  one vCPU, 60-second guest deadline and the 3-day artifact policy. Diagnostic
  failure must not turn a failed G2a into a success.
- **Negative / red-team criteria:** reject missing monitor socket, malformed or
  pre-existing screenshot, unsafe output pathname, and bogus screenshot bytes.
  A PPM screenshot cannot be promoted to G2a or Wanderer success.
- **Evidence:** E1 static shell/CI-policy review; E2 synthetic socket-based
  tests; E4 only if a real bounded QEMU run provides fresh screen + marker data.
- **Human/hardware:** H0 for diagnostics only. H1 before future protected
  kernel/ABI changes; H2 when material hardware properties require it; H3 for
  strong release claims. No L1–L5 claim.
- **Stop:** reject if provenance checks are weakened, resource caps are raised,
  CI fails or the screenshot is wrongly treated as proof. Keep G2a blocked until
  a real marker reaches the serial capture.
- **Review 1:** examine output-file safety and fail-closed command parsing.
- **Review 2:** ensure optional mode leaves normal QEMU args, guest deadline and
  upstream OS unchanged; rerun CI sanity after changes.
- **Review 3:** simulate a fake HMP endpoint plus absent/malformed/stale output.
  **NO TEST, EXPLAIN WHY:** synthetic tests cannot prove a BIOS/GRUB framebuffer
  is legible in a real VM; only a fresh controlled QEMU run can demonstrate that.

### Evidence and reviews for the timeout-screen diagnostic

- Verified implementation head before review note:
  `9fa1543f64dab6a55ee48902f2edc47d3ca705df`.
- GitHub-hosted `Nexus project sanity` run
  [38387664077](https://github.com/Frapo78/AROS-FraPo/actions/runs/38387664077)
  passed. Its baseline-harness negative test, new Python fake-HMP tests,
  shell syntax, and QEMU policy self-test all passed. Repository filename
  and line-ending jobs also passed on this SHA.
- **Review 1 / Construction (focused change):** optional, bounded HMP
  diagnostics only; rejects unsafe/pre-existing paths, bogus/truncated
  PPM evidence, and missing UNIX monitor sockets. No AROS source changes.
  A real display capture is deliberately not a boot pass.
- **Review 2 / Integration (focused change):** original serial marker,
  one vCPU, guest marker deadline, workflow trigger policy and artifact
  retention are preserved. HMP is enabled only by explicit option;
  the CI workflow opts in for its next bounded run. Upstream master is
  `084dfe66344b67591d34b7adb318d0fc203ddce7`; tested baseline
  remains `2edd46536d08e3b54ecd1315f337a9b7de896f3a`.
  No A-class seam, bridge, ABI or machine-authority change.
- **Review 3 / Evidence Red Team:** focused Python tests simulate a working
  HMP monitor, missing socket, untrusted path, pre-existing screenshot,
  truncated PPM and fake bytes. Baseline harness simulates an unreachable
  HMP monitor and confirms the original marker-timeout exit 124 and
  `FINAL_STATUS=marker-timeout` remain unchanged.
- **Evidence boundary:** E2 for synthetic tests on GitHub-hosted CI.
  **NO TEST, EXPLAIN WHY:** real framebuffer capture in QEMU was not run
  on this source SHA. Strongest remaining failure: BIOS/GRUB displays an
  error but the screenshot is blank, unsupported or absent. Required next
  step: one deliberately dispatched, resource-bounded QEMU run, retaining
  image/log/manifest for analysis. G2a requires its serial marker;
  screenshot presence cannot satisfy it.
- **Gate/claims:** H0 for this tooling addition, no H1/H2/H3 fulfillment
  implied, and no new L0–L5 runtime security claim.
- **Merge stop:** this focused change has G0 evidence, but the broader
  QEMU PR #24 is still blocked on G2a/E4. No automatic ISO upload and no
  baseline promotion are authorized.

## 2026-10-23 task contract: capture the BIOS GRUB configuration from the G1 ISO

- **Goal:** retain the actual `/boot/grub/grub.cfg` extracted from the exact
  G1 ISO, plus ISO/config SHA-256 and xorriso output, before attempting G2a.
- **Non-goals:** rewrite GRUB, parse GRUB execution semantics, modify AROS,
  infer the selected menu entry, promote a serial or security claim, or run
  additional QEMU instances.
- **Preconditions:** G1 creates a nonempty ISO; xorriso is already installed
  in the bounded QEMU workflow; evidence output directory is new.
- **Ownership:** U = upstream GRUB/ISO/kernel; N = capture helper, host
  self-test, workflow wiring; A = none. No B0-B3 bridge is introduced.
  Machine authority remains legacy-owned; no trust-ratchet transition.
- **Integrator:** Frapo78; feature branch `nexus/qemu-ci`; issue #15.
- **Acceptance:** extract nonempty BIOS GRUB config; retain xorriso log;
  record exact ISO and extracted-file hashes; fail on extraction failure;
  include evidence in the existing short-lived artifact; keep the existing
  QEMU CPU/time/network/resource caps and marker criteria unchanged.
- **Negative criteria:** missing/empty ISO, existing/symlink evidence
  directory, extraction error, empty extracted config, and repeat invocation
  must not report success. A synthetic xorriso test must not count as E4.
- **Required evidence:** E1 shell/workflow checks; E2 positive and negative
  fake-xorriso tests; E3 actual workflow integration; E4 only from a later
  deterministic QEMU run with the real G1-bound ISO.
- **Human/hardware:** H0 for this host diagnostic. No H1/H2/H3 requirement
  is satisfied or implied; no real-hardware gate applies to this diagnostic.
- **Security level:** no new L0-L5 property demonstrated.
- **Stop:** reject if capture alters the ISO, weakens provenance, creates
  an unbounded QEMU run, overwrites evidence, or promotes extracted text
  into proof of GRUB execution or kernel entry.
- **Review 1 (Construction):** inspect input validation, evidence overwrite,
  shell error paths, scope and artifact lifetime.
- **Review 2 (Integration):** inspect current upstream generator and ISO
  layout, G1/G2 provenance, workflow resource policy and CI results.
- **Review 3 (Evidence Red Team):** run missing/empty ISO, stale/symlink
  destination, xorriso failure, empty extraction and duplicate-invocation
  tests. **NO TEST, EXPLAIN WHY:** a fake xorriso cannot prove the real ISO
  contains the path or that GRUB selects it; a G1 build with captured ISO
  and a bounded real QEMU run are prerequisites for E3/E4.
