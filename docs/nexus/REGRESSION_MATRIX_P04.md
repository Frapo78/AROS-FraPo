# P0.4 regression inventory checkpoint: upstream m68k and SMP

> Status: partial Phase 0 inventory; **not** a passing runtime gate.
>
> Reviewed: 2026-11-01, `aros-development-team/AROS:master` at
> `bf196e7dc17f879d0eeb7b86446e14160df65b5b`.
>
> Tested AROS baseline remains
> `2edd46536d08e3b54ecd1315f337a9b7de896f3a`.
> This checkpoint does not update `BASELINE.md`.

## Task contract (issue #5)

**Goal:** map newly available upstream-owned m68k compatibility and SMP
regression tests to observable compatibility claims, and identify what
must still be run before Nexus protection work. **Non-goals:** change
upstream code, create a second m68k translator, declare a protected
bridge, implement P1.1, promote a boot baseline, or claim isolation.

**Preconditions:** root `AGENTS.md`, accepted ADR-0002, current upstream
source and existing Nexus ABI/trust documentation. **Integrator:**
Frapo78. **Branch:** `nexus/p04-upstream-regression-inventory`.

**Ownership:** U = `rom/m68kemu`, `developer/debug/test/m68kemu*`,
`developer/debug/test/smp`, native AROS Exec/DOS and test semantics.
N = this inventory only. A = none. Existing emulator/native thunks
preserve legacy compatibility semantics (**B0**); they are *not* a
Nexus B1 generated protected bridge. B1/B2/B3 are not implemented.
CR3/page tables, privilege, IDT/APIC/IRQ, physical memory, PCI/MMIO,
DMA/IOMMU and device authority remain **legacy-owned**.

**Acceptance for this document:** each named existing test has a
source path and reproducible invocation or build target; unrun tests
are explicitly marked; at least one negative scenario is specified for
each candidate boundary. **Negative criteria:** do not equate
contained m68k memory with a sandbox, generated thunk coverage with
a safe protected ABI, or host tests with an AROS guest boot.
Do not infer an SMP TLB revocation guarantee from unrelated SMP tests.

**Evidence required for later acceptance:** E2 host executions with
compiler/version and exit status, E3 AROS guest regressions, E4
SHA-bound G1/G2 QEMU boot (two vCPUs for SMP-specific claims).
A human must inspect compatibility/ABI consequences of any future
boundary-changing patch (H1); hardware-dependent DMA/IRQ claims need
H2, strong release isolation claims H3. This **documentation-only**
checkpoint is H0. No L0-L5 isolation level is demonstrated.
**Stop:** a failed host test, missing submodule/toolchain, or absent
G1-bound guest evidence blocks promotion of the affected row.

## Current upstream regression candidates

| Compatibility behavior | Existing upstream test/target | Environment | Current evidence |
| --- | --- | --- | --- |
| m68k containment allocation, heap reuse, endian access, pointer round-trip and fake library bases | `developer/debug/test/m68kemu_host/Makefile`: `make -C developer/debug/test/m68kemu_host test` | Native C++20 host; full suite needs its declared source/submodule dependencies | Source target inspected, **not executed** |
| m68k bounds: zero/tiny arenas, end-of-buffer, integer wrap, low-vector guard and rejected writes | `make -C developer/debug/test/m68kemu_host test-memory-bounds` | Python 3.9+, C++17; no AROS SDK/NDK/Moira required for this focused regression | Source target and regression README inspected, **not executed** |
| m68k bounds under sanitizers | `make -C developer/debug/test/m68kemu_host test-memory-bounds-sanitize` | Host ASan/UBSan support | Source target inspected, **not executed** |
| m68k hunk/RunFile smoke in AROS | `developer/debug/test/m68kemu/mmakefile.src`: `test-m68kemu`; `test-m68kemu-runm68k` | Built AROS guest with `m68kemu.library` | Build targets inspected, **not executed** |
| Exec task/preemption, semaphore and list stress on SMP | `developer/debug/test/smp/mmakefile.src`: `test-smp-preempt`, `test-smp-sem`, `test-smp-lists` (and quick variants) | Built multi-vCPU AROS guest | Build targets inspected, **not executed** |

For the focused bounds regression, the upstream runner extracts production
accessors from `m68kemu_intern.h` and callbacks from
`m68kemu_moira.cpp`, and compares against a separately computed 64-bit
range oracle. This is stronger than a hand-copied model, but does not
prove thunk, shadow-object or whole-guest safety.

### Generator and bridgeability checkpoint

`rom/m68kemu/m68kemu_thunkgen.py` rejects explicitly recognized
pointer-to-pointer prototype types in `classify_type()`. When a C
prototype is missing, `gen_param_line()` instead falls back to
register-class heuristics (A-register pointer or selected D-register
pointer, otherwise scalar). This is an **upstream B0 compatibility
fallback**, not evidence of a fail-closed protected bridge. Unknown
pointer lifetimes, callbacks/Hooks, raw physical addresses and nested
pointers must remain in B0 or receive explicit reviewed B2 handling
until a distinct Nexus B1/B3 contract and adversarial tests exist.
Do not reuse this fallback in a protected-boundary generator.

The upstream `rom/m68kemu/INTERNALS.md` explicitly lists missing
regressions for generated-thunk fallback, unimplemented LVOs, task
and semaphore behavior, shadow/taglist translation, device I/O,
and several loader paths. These are **gaps**, not assumed passes.
The upstream implementation is the primary compatibility path; do not
fork it to address these gaps without upstream-first review.

## Falsifiable follow-up / red-team matrix

1. **Host memory bounds (E2 candidate):** run both commands above on
   the pinned source; inject addresses near `UINT32_MAX`, short
   buffers and rejected writes; fail if any write changes guard bytes.
2. **m68k-to-native bridge (E3 candidate):** exercise missing prototype,
   pointer-to-pointer, stale native handle, callback/Hook and malformed
   TagItem paths in a controlled guest; require explicit rejection or
   a documented, bounded legacy-only outcome. No B1 acceptance from
   the current thunk generator.
3. **SMP regression (E3/E4 candidate):** run existing preemption,
   semaphore and list tests under a two-vCPU SHA-bound guest; record
   hangs, faults and CPU IDs. These tests **do not** replace the
   dedicated cross-CPU TLB revocation experiment in P0.8.
4. **G1/G2 dependency (E4 candidate):** retain the exact ISO,
   `build-manifest.txt`, QEMU version, serial log and human Wanderer
   interaction. A G2a serial marker is not G2c.

## Three reviews and evidence limits

**Review 1 — Construction:** inventory restricted to existing upstream
targets; no ABI or runtime changes, no duplicate m68k implementation.
Commands and source paths were checked against the pinned upstream
Makefiles/README. No ownership or lifetime contract is invented.

**Review 2 — Integration:** upstream-first comparison identified 31
commits since `a9e77d13349a6bf7f8006f79f94a1ad4dc3cfac2`,
including m68kemu and SMP test changes. Fork `master` was fast-forwarded
to `bf196e7d` without Nexus changes. `nexus/main` and the tested
baseline were not advanced. Existing upstream tests are preferred over
Nexus duplicates.

**Review 3 — Evidence Red Team:** twelve mechanical source assertions
verified the named Makefile targets, the independent bounds oracle,
pointer-to-pointer rejection and missing-prototype fallback (E1).
**NO TEST, EXPLAIN WHY:** no complete upstream checkout/toolchain or
G1-bound current-upstream ISO was available to execute the C++ or
AROS guest suites in this cycle. Strongest remaining counterexamples:
a malformed guest pointer reaching a native thunk, a stale native
handle surviving an object's lifetime, or a stale remote TLB
permission after CPU-local invalidation. The required next evidence is
a real host bounds run and a built, instrumented two-vCPU guest.
Neither was produced here.

**Evidence:** E0 source reasoning and E1 mechanical source assertions
only; **E2/E3/E4/E5/E6/E7 not newly established**.
**Security:** no L0-L5 claim. **Residual risk:** source inventory
cannot establish execution success, portability or actual containment.
