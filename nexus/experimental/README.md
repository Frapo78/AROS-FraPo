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
