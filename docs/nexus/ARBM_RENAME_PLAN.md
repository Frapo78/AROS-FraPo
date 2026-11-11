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

## Progress — active documentation batch

Updated project-facing branding in README.md, VISION.md, CONVERGENT_ARCHITECTURE.md, TRUST_MODEL.md, UPSTREAM_INTEGRATION.md, BRANCH_POLICY.md, ARCHITECTURE.md, ROADMAP.md, REVIEW_PROTOCOL.md, VERIFICATION_MODEL.md, ADDRESS_SPACE_MODEL.md, AI_FOUNDATIONS.md, NEXUS_EXEC_SPLIT.md and RELEASE_POLICY.md. Existing filenames and ADR link targets were restored where an automatic replacement would have broken them.

**Not complete:** this is a targeted documentation batch, not an exhaustive repository-wide inventory. CI/workflows, source symbols, case-insensitive tracked-file scanning and links still require mechanical validation. Do not infer build, boot, or CI success from these edits. Historical ADR text is unchanged. Branch and directory migration are deferred to avoid breaking external consumers.

### Review updates

Review 1: textual branding changes only, with known filename/link corrections; inspect full diff before merge.
Review 2: no intentional changes to ABI, binaries, upstream tracking or baseline; no build regression evidence yet.
Review 3: counterexample found — renaming link targets to ARBM without renaming files breaks documentation links; repaired in touched files. Remaining risk: unexamined references in other files. E0; E1 link checker not yet executed. H0.

## Additional validation checkpoint

Current-facing documentation also updated: docs/nexus/README.md, TASKS.md, GOVERNANCE.md. Wording corrections and stale README acceptance statements repaired. PR comparison confirms the diff is restricted to root AGENTS.md, root README.md, and files under docs/nexus/; no tracked source or CI file is changed by this PR.

**Blocking gaps before merge:** the available repository code-search endpoint returned zero results even for known present terms, so it cannot serve as a complete tracked-file inventory. The runtime cannot clone GitHub from this environment. No full-tree link checker, G0 run, workflow validation, or successful required check result has been obtained. Keep PR draft. The current work is a **partial branding/documentation change**, not the user's requested full elimination of old identifiers.

Review 1: no source, binary, or workflow files in the PR diff; text-only changes reviewed for known renamed link targets.
Review 2: `nexus/main` remains base; upstream observed `557dddb47786ee48fc824accaace0876a867a3c9`. Tested baseline untouched.
Review 3: failure hypothesis: missing historical filenames, stale workflow consumers, and false-positive zero-result code search could mask remaining old references. A complete git-grep over tracked files and link-checker are required to falsify this. E0 only until executed. **NO TEST**: full repository checkout is unavailable here, and code search is demonstrably incomplete. H0.

## Automated audit entry point

A read-only audit script is now available at `tools/arbm_name_audit.py`. Execute it from a complete checkout with `python3 tools/arbm_name_audit.py`. It inventories tracked text files, reports case-insensitive old-name occurrences, and fails on broken relative Markdown links. Review the reported occurrences manually: historical ADR, branch, directory and provenance references are intentionally not an automatic failure. It is not a replacement for G0, CI, or workflow validation.

The connected GitHub PR reports mergeable=true and base `7164c47c84d1bd468639c3fcad0e23104175f24f`, but the latest checked head `093dcaed54dcb1f065cc8aaf708d1cbff53f13a5` had zero commit statuses. A newer audit-script commit exists, so checks must be re-read on the current head. The checkout attempt in this execution environment failed DNS resolution of github.com; consequently no complete-checkout audit has been executed. **Merge remains blocked.**

## 2026-11-10 checkpoint

- Read root AGENTS.md, accepted ADR-0002, verification model, baseline, review protocol, tasks and project-sanity workflow.
- Added negative handling to the tracked-file audit for missing tracked files and links escaping the repository; wired the audit into the existing `.github/workflows/nexus-project-sanity.yml` (display name ARBM, historical workflow filename retained). The workflow now includes the audit script in its path filters. Old-name references remain reported rather than indiscriminately renamed.
- The complete checkout audit, G0 and GitHub Actions results are **not yet observed**: this environment cannot resolve github.com for git clone, and the GitHub commit-status endpoint returned no statuses for `2a72401df66cc4d2d8acbf0bf33de211c7526355`. No E1 pass is claimed for the complete tree.
- Upstream AROS master is 62 commits ahead of previously inspected `e3ec1bd71af7` at this checkpoint, with changes including `rom/exec/`, m68k MMU and RISC-V kernel files. This docs/tooling PR does not integrate or modify those runtime areas. The tested baseline remains `2edd46536d08e3b54ecd1315f337a9b7de896f3a`.
- Review 1 (Construction): scope restricted to docs and audit/CI tooling; negative handling improved. Review 2 (Integration): legacy workflow filename, `nexus/main`, `docs/nexus/` and historical ADR kept stable; upstream delta inspected at file-path level only. Review 3 (Evidence Red Team): missing tracked file and out-of-tree Markdown link are explicit failures. No full checkout test was possible; strongest outstanding counterexample is a broken pre-existing link or false-positive Markdown link causing CI failure. E0 until Actions runs; H0; no L0-L5 claim. **Do not merge while checks and link audit are unverified.**

## 2026-11-11 verification checkpoint

- Current upstream `aros-development-team/AROS:master` observed at `df648532783c8c88387379f9b1e19ad869c738a4`; naming-only changes do not require source integration. The tested baseline stays `2edd46536d08e3b54ecd1315f337a9b7de896f3a`.
- The GitHub PR head observed before this checkpoint was `ac6f45209777e1c640d7a98dc796813d061cfb4b`; the connector returned no commit statuses. The PR remained draft and GitHub reported mergeable, which is not proof of CI success.
- Fixed an audit observability gap: the sanity workflow previously redirected the full old-name inventory into a temporary log and showed only counts. It now emits the inventory into the workflow log and writes counts to the GitHub job summary. This does not classify the occurrences automatically.
- Review 1 (construction): workflow change is confined to log visibility and summary; no kernel, ABI, or artifact change. Review 2 (integration): existing `nexus/main` trigger and historical paths preserved; no upstream code changes. Review 3 (evidence red team): a plausible failure is a successful audit with numerous unclassified historical/current references; the job deliberately does not treat a zero-link-error exit as proof of completed renaming.
- Evidence E0 for review only, H0. No L0-L5 claim. **NO TEST, EXPLAIN WHY:** this runtime cannot resolve `github.com` for a complete clone, and connector commit-status results do not establish GitHub Actions success. To upgrade to E1, inspect a completed workflow on the new SHA, classify its `OLD_NAME` lines, validate G0 and relevant checks. Keep draft; do not merge.
