# ARBM naming transition

Status: In progress — documentation-only first stage
Decision: ARBM = AROS Bare Metal
Previous project codename: Nexus
Logical integrator: ARBM naming transition maintainer

## Scope and invariants

ARBM names the convergent privileged executive project beneath the primary AROS runtime. This is a naming decision, **not** a superseding architecture decision. ADR-0002 remains accepted and authoritative; ADR-0001 and ADR-0002 are immutable historical decision records. Their original wording must not be rewritten. The name does not imply that upstream AROS previously lacked bare-metal support.

- U: upstream AROS source and fork `master` — untouched.
- A: integration seams — unchanged.
- N: project naming, documentation and future ARBM-owned identifiers.
- Bridge: B0/B1/B2/B3 contracts unchanged.
- Machine authority: remains legacy-owned/shared/Nexus-owned exactly as previously evidenced; naming does not transfer authority.
- Security: no new L0–L5 claims.

## Task contract

Goal: adopt ARBM consistently in current project-facing documentation and, after validation, non-historical owned tooling.
Non-goals: changing kernel code, ABI, protection contracts, upstream history, baseline, security claims or release readiness.
Preconditions: read root AGENTS.md, ADR-0002, latest upstream, baseline and affected workflow configuration.
Acceptance: active project-facing text says ARBM; historical references remain attributable; all internal links, CI paths, branch targets and scripts resolve; no change in generated binary behavior.
Negative criteria: no change to fork master, `nexus/main` target, tested baseline, old artifact provenance, historical ADR text, external URLs or upstream-owned identifiers by search-and-replace.
Automated evidence: exhaustive tracked-file inventory, case-sensitive and insensitive old-name scan with explicit allowlist, link validation, workflow parse, G0, and relevant script smoke tests.
Human evidence: H0 for pure docs; maintainer approval for external repository rename, branch rename and public release naming.
Hardware evidence: none for naming alone.
Stop conditions: broken link/workflow, unexpected identifier in executable path, unreviewed external dependency, or architectural semantic change.

## Migration sequence

1. Record the naming decision and add an ARBM alias in the operational contract. Keep existing `docs/nexus/` and `nexus/main` stable during the first stage.
2. Inventory every tracked `Nexus`, `NEXUS`, `nexus` occurrence and categorize it: current branding, historical record, executable identifier, CI path, artifact/provenance or external integration.
3. Rename current branding in focused batches; preserve historical ADRs, commits, citations, and baseline evidence. Keep compatibility aliases for paths or identifiers consumed by automation.
4. Update scripts, CI, documentation paths, and release artifact names only with mechanical validation and an explicit migration map. Never silently change tested baseline.
5. Consider repository rename and `nexus/main` branch migration as separate externally visible operations after validating GitHub Actions, branch protection, scheduled automation and local clones. GitHub redirects are not a substitute for validating consumers.
6. Recheck latest upstream and complete the three reviews before merge.

## Reviews — initial documentation stage

Review 1 / Construction: scope limited to naming and explicit preservation of operational gates. No runtime code touched.
Review 2 / Integration: current `nexus/main` and historical ADR-0002 retained. Upstream checked at `557dddb47786ee48fc824accaace0876a867a3c9`; no source integration required for a naming-only change.
Review 3 / Evidence Red Team: strongest failure scenario is a naive global replacement breaking CI path references, historical provenance or automated clients. No executable adversarial test yet: the full inventory and migration map must be established first; do not merge as a complete migration without them.
Evidence: E0 for plan and upstream comparison; E1 only after mechanical checks are run.
Gate: H0 for documentation; no hardware gate.
Residual risk: incomplete reference inventory; no claim of completed migration.
