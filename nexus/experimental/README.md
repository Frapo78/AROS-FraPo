# Nexus experimental mapping-rights contract

This is the first **Nexus-owned C code prototype**, deliberately isolated from the AROS build. It does not implement address spaces, write page tables, switch CR3, enforce W^X or establish CPU isolation. It is not Phase 1 P1.1 implementation.

## Phase 0 task contract

- Goal: express a conservative, fail-closed mapping-rights validation rule as executable C.
- Non-goals: change AROS ABI, legacy mappings, MMU state, fault handling or privilege.
- Preconditions: C11 compiler; this header is not integrated into the AROS kernel.
- Ownership: N only. No AROS U changes or A-class seam. B0–B3 not applicable because no bridge exists.
- Acceptance: host test compiles with warnings as errors and rejects missing READ, W+X, unknown bits and NX-required mappings when NX is unavailable.
- Negative criteria: no silent acceptance of unsupported rights; no claim of hardware enforcement.
- Evidence: focused host test E2 when actually run; source inspection alone E1. G1/G2a remain prerequisites to real kernel extraction.
- Human gates: H0 for standalone prototype; H1 before any integration affecting MMU/ABI/protection. No L1–L5 claim.
- Stop: do not include this header in a kernel path or expose it as public ABI until reviewed, upstream checked, G1/G2a validated and hardware semantics tested.

Run locally from the repository root:

```sh
cc -std=c11 -Wall -Wextra -Werror -pedantic -o /tmp/nexus-mapping-test nexus/experimental/tests/mapping_rights_test.c
/tmp/nexus-mapping-test
```

## Three reviews

1. Construction: no allocation, mutable state, pointer or machine instruction; explicit input validation.
2. Integration: isolated directory, no AROS build or ABI change; later MMU integration requires a new H1 review.
3. Evidence Red Team: negative cases in host test reject unknown flags, W+X, missing READ and missing NX. The strongest untested failure is mismatch between policy and real x86-64 PTE/NX semantics. **NO TEST, EXPLAIN WHY:** host tests cannot prove MMU enforcement; requires actual QEMU fault tests after G1/G2a.

## NX capability input hardening (2026-11-01)

**Task contract:** Goal: reject nonboolean NX capability inputs rather than treating
any nonzero integer as confirmed hardware NX. Non-goals: PTE manipulation, kernel
integration, public ABI, or hardware isolation. Preconditions: existing standalone
C11 mapping-rights contract, originally proposed in PR #29 and integrated via PR #34. U: AROS runtime untouched. N: experimental
header and host tests. A: none; B0-B3: no boundary exists. Integrator: Frapo78.
Acceptance: values 0 and 1 retain their behavior; -1 and 2 reject; 256 rights
patterns times four NX inputs plus 20 high-bit probes all match the oracle.
Negative criterion: no unknown NX state may return OK. Automated evidence:
focused host test with warnings-as-errors and UBSan (E2). Human gate: H0 for
host-only prototype, H1 before MMU integration. Hardware evidence: not applicable
to this host-only patch; E4 QEMU fault tests required for future MMU claims.
Security: no L0-L5 demonstrated. Stop: failing test or unexpected AROS linkage.

**Review 1 Construction:** A single fail-closed guard before rights processing;
no allocation, lifetime, shared state, ABI or error-path expansion.
**Review 2 Integration:** No upstream/kernel/ABI changes; upstream
`bf196e7dc17f879d0eeb7b86446e14160df65b5b` reviewed.
**Review 3 Evidence Red Team:** On the original code, READ with NX=-1 returned
OK (failing test); after the guard, 1,044 focused cases passed locally with
UBSan. Test: `cc -std=c11 -Wall -Wextra -Werror -pedantic -fsanitize=undefined
-o /tmp/nexus-nx-test nexus/experimental/tests/mapping_nx_input_test.c &&
/tmp/nexus-nx-test`. The clean integration PR #34 passed its GitHub Actions host contract workflow and was squash-merged into `nexus/main` at `cf6a26fe0ea76e5d86536bbe6052fc64ff65ca99`.
**NO TEST, EXPLAIN WHY:** These host tests cannot establish actual NX/PTE
enforcement or TLB behavior. Strongest untested failure: CPU executes a
supposedly non-executable page. Requires G1-bound deterministic QEMU fault
testing and H1 before integration. Evidence E2 is host-only, not E4.
