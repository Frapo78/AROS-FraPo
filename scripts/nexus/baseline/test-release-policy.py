#!/usr/bin/env python3
"""Fail-closed host policy checks for the Nexus diagnostic ISO release workflow.

This validates release automation structure and rejects representative weakened
variants. It does NOT build an ISO, execute QEMU, or prove publication.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github" / "workflows" / "nexus-iso-release.yml"


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def check(text: str) -> list[str]:
    errors: list[str] = []
    try:
        document = yaml.load(text, Loader=yaml.BaseLoader)
    except yaml.YAMLError as exc:
        return [f"invalid YAML: {exc}"]
    if not isinstance(document, dict):
        return ["workflow must be a mapping"]

    triggers = document.get("on", {})
    require(isinstance(triggers, dict), "missing on triggers", errors)
    if not isinstance(triggers, dict):
        return errors
    require(set(triggers) == {"push", "schedule", "workflow_dispatch"},
            "unexpected release trigger", errors)
    push = triggers.get("push", {})
    require(isinstance(push, dict) and push.get("branches") == ["nexus/main"],
            "push must be restricted to nexus/main", errors)
    schedule = triggers.get("schedule", [])
    require(isinstance(schedule, list) and any(
        isinstance(item, dict) and item.get("cron") == "0 4 1 * *"
        for item in schedule), "monthly schedule missing", errors)
    require(document.get("permissions") == {"contents": "read"},
            "global permissions must be read-only", errors)

    jobs = document.get("jobs", {})
    job = jobs.get("build-verify-publish", {}) if isinstance(jobs, dict) else {}
    require(isinstance(job, dict), "missing release job", errors)
    if not isinstance(job, dict):
        return errors
    require(job.get("if") == "github.ref == 'refs/heads/nexus/main'",
            "release job must be branch-guarded", errors)
    require(job.get("permissions") == {"contents": "write"},
            "publishing job permission must be explicit", errors)
    steps = job.get("steps", [])
    require(isinstance(steps, list), "release steps missing", errors)
    if not isinstance(steps, list):
        return errors
    by_name = {
        step.get("name"): step.get("run", "")
        for step in steps if isinstance(step, dict)
    }
    build = by_name.get("Build fresh diagnostic boot ISO", "")
    boot = by_name.get("Verify GRUB provenance and actual QEMU serial marker", "")
    stage = by_name.get("Stage immutable release candidate", "")
    publish = by_name.get("Publish only verified ISO as GitHub prerelease", "")

    require(bool(re.search(
        r"(?m)^\s*bash scripts/nexus/baseline/build-x86_64\.sh\s*$", build)),
        "build script must be invoked via bash", errors)
    require(bool(re.search(
        r"(?m)^\s*bash scripts/nexus/baseline/run-qemu-x86_64\.sh\b", boot)),
        "QEMU runner must be invoked via bash", errors)
    require("capture-iso-grub.sh" in boot and "prepare-serial-grub.py --check" in boot,
            "boot ISO GRUB provenance checks missing", errors)
    require('get ARTIFACT_SHA256 "$manifest"' in boot and
            'sha256sum "$iso"' in boot and
            'get ISO_SHA256 "$RUNNER_TEMP/nexus-grub/provenance.txt"' in boot,
            "ISO hash provenance missing", errors)
    require("GRUB_AFTER_SHA256" in boot and "GRUB_SHA256" in boot,
            "GRUB hash provenance missing", errors)
    require("FINAL_STATUS=marker-reached" in boot and
            "MARKER_REACHED_FINAL=yes" in boot and
            'grep -Fq "$NEXUS_QEMU_EXPECT_MARKER"' in boot,
            "real serial marker evidence missing", errors)
    require('test "$(git rev-parse HEAD)" = "$GITHUB_SHA"' in
            by_name.get("Validate release context and milestone", ""),
            "exact source SHA guard missing", errors)
    require("sha256sum aros-pc-x86_64.iso" in stage and
            "SHA256SUMS" in stage and
            "2147483648" in stage,
            "release hash/size checks missing", errors)
    require('gh release view "$tag"' in stage and "exit 1" in stage,
            "existing tag must fail closed", errors)
    require('gh release create "$tag"' in publish and
            '--target "$GITHUB_SHA"' in publish and
            "--prerelease" in publish,
            "immutable source-bound prerelease publishing missing", errors)
    return errors


def negative_cases(original: str) -> None:
    cases = {
        "non-executable build wrapper": (
            "bash scripts/nexus/baseline/build-x86_64.sh",
            "scripts/nexus/baseline/build-x86_64.sh"),
        "non-executable QEMU wrapper": (
            "bash scripts/nexus/baseline/run-qemu-x86_64.sh",
            "scripts/nexus/baseline/run-qemu-x86_64.sh"),
        "wrong release branch": (
            "github.ref == 'refs/heads/nexus/main'",
            "github.ref == 'refs/heads/master'"),
        "write permission at workflow scope": (
            "permissions:\n  contents: read",
            "permissions:\n  contents: write"),
        "missing source guard": (
            'test "$(git rev-parse HEAD)" = "$GITHUB_SHA"',
            'test -n "$GITHUB_SHA"'),
        "missing marker final state": (
            "MARKER_REACHED_FINAL=yes", "MARKER_REACHED_FINAL=unknown"),
        "missing ISO hash check": (
            'get ARTIFACT_SHA256 "$manifest"',
            'get ARTIFACT_SIZE "$manifest"'),
        "missing prerelease flag": ("--prerelease", "--draft"),
        "wrong release target": ('--target "$GITHUB_SHA"', '--target master'),
    }
    for label, (before, after) in cases.items():
        if before not in original:
            raise AssertionError(f"test fixture missing: {label}")
        mutant = original.replace(before, after, 1)
        if not check(mutant):
            raise AssertionError(f"validator accepted weakened policy: {label}")


def main() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    failures = check(text)
    if failures:
        raise SystemExit("Release policy FAIL:\n- " + "\n- ".join(failures))
    negative_cases(text)
    print("Release policy PASS: actual YAML + 9 rejected negative mutations")
    print("Evidence: E1 static release policy, E2 focused negative validator tests")
    print("NOT evidence of a completed ISO release or usable Wanderer desktop")


if __name__ == "__main__":
    main()
