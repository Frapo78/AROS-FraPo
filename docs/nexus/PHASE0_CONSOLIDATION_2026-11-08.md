# Phase 0 host-evidence PR consolidation (2026-11-08)

> Integration plan and gates, not an assertion that G1/G2b/G2c have passed.

## Task contract — issue #15, with independent P0.8 host audit #14

- **Goal:** reduce open Nexus host-tooling PR fragmentation by integrating the
  current G1/G2a ISO and release-policy harness (PR #37) with the read-only,
  SHA-bound PAT source guard (PR #38) in **one reviewed squash merge** to
  `nexus/main`. Keep the historical PR #24 G1/G2a evidence available by URL
  without importing its obsolete 52-commit branch or replacing current docs.
- **Non-goals:** upstream code changes, upstream-tracking `master` edits,
  kernel/ABI/MMU changes, an automatic baseline promotion, a new OS, P1.1,
  G2b/G2c Wanderer or USB/hardware/security claims.
- **Preconditions:** read root `AGENTS.md`, current ADR-0002, review and
  verification models; keep `nexus/main` unchanged until this candidate
  passes its exact-SHA gates. A combined branch must preserve all unique PR
  #37 and #38 files and both documentation index links.
- **Logical integrator:** Frapo78 (single integration owner).
- **Ownership:** U = existing AROS source, kernel, GRUB, PAT mapping; A = none;
  N = host-only build/QEMU harness, release policy, PAT source guard, synthetic
  tests, CI and documentation. No new B1/B2/B3 contract. Existing AROS
  mapping calls are B0 direct-only legacy.
- **Authority:** CR3/page tables, privilege, IDT/APIC/interrupts, physical
  memory, PCI/MMIO, DMA/IOMMU and device ownership remain legacy-owned.
- **Acceptance:** project sanity and source-hygiene PASS; Linux workdir/TAR
  negative tests PASS; release and QEMU policy adversarial tests PASS; PAT
  actual-source check at its exact pinned upstream SHA and mutations PASS;
  G1 reproducible exact combined-source ISO+manifest+GRUB hashes; G2a bounded
  QEMU real early serial marker from that exact ISO with retained manifest
  and serial log. The workflow's release publishing must remain fail-closed
  and be reviewed before activation.
- **Negative/red-team:** reject an ISO with forged/missing/duplicate manifest
  fields, altered GRUB or ISO hash, absent/early-false marker, unsafe QEMU
  triggers/resource settings, invalid source SHA/dirty upstream PAT files,
  changed PAT constants/branches and unsupported filesystem/TAR behaviour.
  No host-only positive result may be presented as G2b/G2c or as isolation.
- **Evidence required:** E1 source/structural, E2 executable adversarial
  host tests and E4 exact combined-commit QEMU G2a; E3 regression evidence
  as available. Prior PR #24 E4 belongs to its own tested source and cannot
  be transferred to this candidate. Human gate H0 for host tools; H1 before
  any future MMU/kernel/ABI/protection merge, H2 for real device/DMA/GPU,
  H3 before strong release-level L2-L5 claims.
- **Security:** no L0-L5 protection property is newly demonstrated.
- **Stop conditions:** failed check, incomplete/unbound G1/G2a, incomplete
  three-pass reviews, unexpected diff affecting AROS runtime or unexamined
  upstream conflict. No release claim or merge in that state.

## Branch and upstream audit

- Repo default/integration branch `nexus/main` at start:
  `0a194ba1e470cb0cdcc048f83b7369ce2f7fd2b7`.
- Upstream AROS master observed:
  `cafc41fca22a1205105faa14d8d0f0aea97112d3`.
  Five commits after the PAT fixture pinned source
  `43a4bdaccad5646edc9b00802ba9ad1a47e2066e`
  touch PCI BAR sizing and POSIX tests/runtime, not the three PAT source
  files; recheck latest upstream again before final merge.
- Fork tracking `master` observed
  `65e07cdcb543b436ab486ce4ffcf23cede176e46`;
  it is behind upstream. Do not place Nexus-only code there.
- **Tested baseline unchanged:** `2edd46536d08e3b54ecd1315f337a9b7de896f3a`.
- Branch inventory: 21 total pre-consolidation, including `master`,
  `nexus/main`, four behind-only historical features, thirteen divergent
  historical features, and two up-to-date open PR heads (#37 and #38).
  Most historical feature refs were used for previously merged/superseded
  proposals. Retain references for provenance; do not blind-merge or
  delete old branches without checking their unique content.
- **Old PR #24:** draft, diverged (52 commits and 18 changed files), has
  historical exact-commit G1/G2a E4 evidence
  [run 40076942687](https://github.com/Frapo78/AROS-FraPo/actions/runs/40076942687).
  Exclude its obsolete overlapping CI/documentation tree.
- **PR #37:** based directly on current main, comprehensive Phase 0
  G1/G2a harness, Docker workdir safety and ISO release policies.
- **PR #38:** also based directly on main, independent host-only PAT checker.
  Its unique files are brought over exactly; its documentation index link
  is merged with #37's Apple Silicon link. Both original PR histories
  remain visible after supersession.

## Public-release activation safety

The combined candidate changes the release workflow to **manual dispatch
only**. No GitHub push or clock trigger may create a public release merely
because the consolidation is merged. Policy negative tests must reject
both automatic triggers and a removed manual-event guard. Monthly cadence
remains planned and needs its own reviewed activation following a real
successful manual release test.

## Three-pass review checklist

1. **Construction:** verify unique-file union, no lost documentation links,
   no unintended source/runtime edits, no redundant older policy scripts,
   fail-closed manifests and bounded resource use.
2. **Integration:** compare combined candidate against current main, original
   PR heads and latest upstream; verify all corresponding CI paths. A passing
   host test is not the same as a successful rebuilt guest ISO.
3. **Evidence Red Team:** rerun all mutated host policies and require actual
   SHA-bound QEMU evidence for combined candidate. Strongest untested case
   is an apparently valid build/GRUB artifact whose kernel never reaches
   the real marker. Do not accept synthetic serial text as guest evidence.

**NO TEST, EXPLAIN WHY:** no actual combined SHA-specific G1/G2a evidence
exists at the moment of branch creation. It must be produced by the CI
build-and-boot run after opening the combined PR; until that completes
successfully, this merge is blocked. Full Wanderer and hardware work remain
separate gates.
