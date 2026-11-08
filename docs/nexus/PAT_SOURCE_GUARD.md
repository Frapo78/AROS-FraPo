# P0.8 — Source-backed x86-64 PAT mapping guard (experimental)

> Host-only diagnostic fixture. Not a guest MMU, device, isolation, or QEMU gate.

## Task contract (before implementation)

- Issue: [P0.8 #14](https://github.com/Frapo78/AROS-FraPo/issues/14). Logical integrator: Frapo78.
- Goal: detect source drift in the upstream MAP_WriteCombine -> PAT-index-4 path for 4 KiB and 2 MiB mappings, including IA32_PAT setup and the legacy PWT/PCD fallback.
- Non-goals: guest MSR/PTE reads, actual memory-type proof, runtime/MMU changes, ABI changes, Phase 1, or hardware-isolation claims.
- Preconditions: clean upstream source checkout at the exact 40-character Git SHA and Python 3.
- Ownership: U = upstream x86-64 mapglobal.c, kernel_startup.c and AROS map flags; A = none; N = this source guard, tests, CI and documentation.
- Current mapping boundary: B0, direct-only legacy KrnMapGlobal. No B1/B2/B3 bridge introduced.
- Authority: CR3/page tables, privilege, IDT/APIC/IRQ, physical memory, PCI/MMIO, DMA/IOMMU and device ownership remain legacy-owned.
- Acceptance: verify exact source SHA and clean tree, MAP_WriteCombine=0x0008, both map helper branches, legacy PWT/PCD, IA32_PAT 0x277 guarded by CPUID.PAT, PAT entry 4=WC, passing host adversarial tests.
- Negative criteria: reject wrong SHA, dirty tracked source, changed PAT constant, wrong MSR, removed/unguarded CPUID test, altered PTE/PDE PAT, changed priority, missing fallback, duplicate functions or forged comments.
- Automated evidence: E1 source check and E2 focused host mutation tests. Guest behavior requires E4 pinned QEMU evidence; physical VRAM/device correctness requires E6.
- Human/hardware gates: H0 for host-only fixture, H1 before any kernel/MMU/ABI merge, H2 for physical device claims, H3 for strong release-level L2–L5 claims.
- Security: no L0–L5 result established. Stop on source mismatch or missing executable guest evidence before stronger assertions.

## Exact upstream reference and source observations

Upstream master observed 2026-11-08: `43a4bdaccad5646edc9b00802ba9ad1a47e2066e`, 23 commits after PAT introduction `ff72af933af92968fb52075f8ca6c244b07b62a3`. Fork tracking master at inspection: `65e07cdcb543b436ab486ce4ffcf23cede176e46`. Tested baseline stays `2edd46536d08e3b54ecd1315f337a9b7de896f3a` and is not changed.

Upstream sets IA32_PAT entry 4 to WC (type code 1) only under CPUID.PAT and sets `tmp.pat=1` in both `set_pte()` and `set_pde_2m()` when MAP_WriteCombine is requested. The WC branch takes priority over cache-inhibit/write-through combinations; the non-WC path retains PWT/PCD flags.

**Unverified risk:** On hardware without PAT, upstream's debug message says MAP_WriteCombine becomes WB. This test does not establish whether the CPU uses WB, raises a reserved-bit fault or behaves differently. The actual physical memory type, page sizes, PAT consistency across CPUs and MMIO/VRAM safety remain untested.

## Run

Run from the Nexus worktree with a separate clean checkout of upstream AROS at the pinned commit:

```sh
python3 -m unittest discover -s scripts/nexus/pat -p 'test_*.py' -v
python3 scripts/nexus/pat/audit_upstream_pat.py \
  --source-root /path/to/clean/AROS-upstream-checkout \
  --expected-sha 43a4bdaccad5646edc9b00802ba9ad1a47e2066e
```

CI uses sparse checkout of the exact three upstream files at the pinned SHA. The 16-value host oracle models PAT/PWT/PCD *as inferred from source*. It is not executing the upstream kernel function or reading live PTE/PDE/MSRs. Regex pattern checks can miss changes elsewhere in the kernel.

## Mandatory review passes

1. **Review 1 — Construction:** standalone read-only source checker, explicit SHA and dirty-check, narrow function extraction, no kernel/ABI/device state changes. Pattern-matching limitations remain explicit.
2. **Review 2 — Integration:** upstream U is untouched and Nexus N fixture is isolated. G1/G2 remain unchanged and no baseline promotion is implied. Before merge, recheck upstream, PAT bitfield layout, x86-64 startup and SMP code.
3. **Review 3 — Evidence Red Team:** run mutation tests that change flags, MSR/CPU guard, PAT bits, fallback precedence, PS/US assumptions, forged comments and duplicate functions. A host unit-model PASS does not validate hardware.

**NO TEST, EXPLAIN WHY:** There is no instrumented, pinned guest build reading CPUID, IA32_PAT, PTE and PDE entries across 4 KiB/2 MiB pages and multiple CPUs. Strongest counterexample: no-PAT CPU faults or maps a device aperture WB when WC was requested. Prerequisite: G1-bound QEMU image, guest readback/fault probe, source/artifact/log hashes; H2 physical hardware for device claims.

Decision: this branch may only be accepted as a Phase 0 host tooling improvement; issue #14, G2c, P1.1 and L1–L5 claims remain open.
