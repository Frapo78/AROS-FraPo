# Nexus documentation and evidence reconciliation — 2026-11-01

> Snapshot, not a live dashboard. Recheck GitHub before using these observations as merge gates.

## Scope and authority

Reviewed the root `AGENTS.md` and `README.md`; the Nexus documentation
index, architecture/vision/convergence/trust/privilege/Exec/AddressSpace,
boot map, bootstrap MVP, ABI, roadmap, baseline, CI strategy, review protocol,
verification model, branch policy, governance, community, upstream integration,
regression inventory, AI foundations, ADR-0001/0002, tasks; and the merged
standalone mapping contract README. Source was read from `nexus/main`
before the documentation patch. PR and workflow state were checked through
GitHub. This is **not** a full runtime source-code or build audit.

## Observed immutable references

- Upstream `aros-development-team/AROS:master`:
  `bf196e7dc17f879d0eeb7b86446e14160df65b5b` (observed 2026-11-01).
- Recorded AROS implementation baseline:
  `2edd46536d08e3b54ecd1315f337a9b7de896f3a` (unchanged).
- Nexus main immediately before this documentation branch:
  `cf6a26fe0ea76e5d86536bbe6052fc64ff65ca99`.
- PR #34 merged the standalone C mapping-rights policy and negative NX tests;
  its focused GitHub Actions CI passed. **Not kernel/MMU enforcement.**
- PR #24: successful historical G1 x86-64 build and G2a early serial
  marker under QEMU at its pinned commit, but PR remains unmerged and
  the result does not transfer to the current main/upstream automatically.
- PR #35: 12 host-only G2c evidence-tooling files, based on main; its
  desktop-evidence, project-sanity and source-hygiene CI checks passed.
  **No real G2b/G2c guest Wanderer usability evidence accepted.**
- PRs #27/#28/#29/#30/#33 closed as superseded/obsolete.
  #30's useful tooling is carried by #35; #29/#33's C work by merged #34.

## Corrections made in this audit

1. `BASELINE.md`: replace stale upstream-tracking SHA and explicitly
   distinguish tested baseline, tracked head, early QEMU marker and desktop.
2. `TASKS.md`: replace misleading todo/pending descriptions, add
   merged code and current PR inventory, preserve Phase 1 blocks.
3. `CI_STRATEGY.md`: distinguish G0, G1, G2a, G2b/G2c and G3-G5
   evidence, including artifact-specific limitations.
4. Root and Nexus READMEs: report actual host-only implementation and
   current branch workflow instead of implying zero code or a default
   bootstrap branch.
5. `X86_64_BOOT_MAP.md`: remove proposed mandatory Legacy Cell relocation
   of ordinary Exec; align AS0/AS1 sequence with accepted ADR-0002.
   The original boot chain remains a source-derived map, not a guest test.
6. `nexus/experimental/README.md`: replace obsolete PR #29 and
   pre-CI wording with the merged #34 evidence.

## Reviews

**Review 1 — Construction:** all edits concern status/provenance or
superseded conceptual topology. No kernel, ABI, workflow, executable or
baseline SHA is changed. Historical architectural proposals remain
historical unless explicitly superseded.

**Review 2 — Integration:** ADR-0002 remains accepted; no mandatory
Legacy Cell, parallel ExecNG, or competing m68k translator is introduced.
U: upstream source and test corpus unchanged. A: none. N: documentation.
B0-B3: no new bridge. All machine authority remains legacy-owned.

**Review 3 — Evidence Red Team:** counterexamples checked include:
an early serial marker mislabeled Wanderer, an unmerged PR mislabeled
main, a green host test mislabeled MMU enforcement, a tracking head
mislabeled a tested baseline, and a source inventory presented as
an executed regression suite. The corrected docs explicitly reject
all five inferences.

**NO TEST, EXPLAIN WHY:** this patch changes documentation only.
GitHub project-sanity/link validation is the applicable E1 automated
gate; executable E2/E4 evidence cited here belongs to separate
immutable code/CI artifacts, not to this documentation change.
The strongest remaining failure is an unreviewed status statement
becoming stale as PRs or upstream advance. Recheck references on
every later integration. H0 documentation; no L0-L5 claim.

## Remaining unresolved gates

- Phase 0 exit: reproducible current main/upstream build, complete QEMU
  boot to usable Wanderer, independent human desktop interaction.
- Host-only G2c evidence tools are not a substitute for a guest run.
- P0.8 remote TLB shootdown, NX hardware enforcement, failure paths and
  resource exhaustion remain open.
- P0.4 m68k/SMP upstream regression candidates were inventoried, not run.
- H1 before real kernel/MMU/privilege/ABI/protection integration.
- Branch protection settings and actual stale-branch deletion were
  not verified by this documentation-only audit.
- Phase 1 AS0/AS1, protected faults and MemoryObject are not implemented.

## Next falsifiable milestone

Integrate the smallest reviewed QEMU G1/G2a harness from PR #24
without stale unrelated commits, rerun the build and pinned ISO boot
on the new combined tree, then attempt real G2b/G2c desktop evidence
with human input-response confirmation. Do not promote `BASELINE.md`
until those criteria are satisfied.
