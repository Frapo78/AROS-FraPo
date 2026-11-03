#!/usr/bin/env python3
"""Fail-closed, synthetic host checks for Nexus resource-bounded G2a CI.

This is NOT an actual x86-64 build, QEMU test or release validation.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import yaml

DEFAULT = Path(__file__).resolve().parents[3] / ".github/workflows/nexus-qemu.yml"
MARKER = "AROS64 - The AROS Research OS"


def check(doc: object) -> list[str]:
    errors: list[str] = []

    def require(ok: bool, message: str) -> None:
        if not ok:
            errors.append(message)

    if not isinstance(doc, dict):
        return ["workflow must be a YAML mapping"]
    triggers = doc.get("on")
    if not isinstance(triggers, dict):
        return ["on triggers must be a mapping"]
    require(set(triggers) == {"pull_request", "workflow_dispatch"},
            "only scoped pull_request and manual dispatch permitted")
    pr = triggers.get("pull_request")
    if not isinstance(pr, dict):
        return errors + ["pull_request must be configured"]
    require(pr.get("branches") == ["nexus/main"], "PR base must be nexus/main")
    types = pr.get("types")
    require(isinstance(types, list) and
            set(types) == {"opened", "reopened", "ready_for_review"} and len(types) == 3,
            "disallowed PR event (especially synchronize)")
    paths = pr.get("paths")
    require(isinstance(paths, list) and
            "scripts/nexus/baseline/**" in paths and
            ".github/workflows/nexus-qemu.yml" in paths,
            "PR path filters missing")
    require(doc.get("permissions") == {"contents": "read"},
            "global permissions must be read-only")
    concurrency = doc.get("concurrency")
    require(isinstance(concurrency, dict) and
            concurrency.get("cancel-in-progress") == "true",
            "obsolete PR/ref runs must be cancelled")
    jobs = doc.get("jobs", {})
    job = jobs.get("qemu-kernel-smoke") if isinstance(jobs, dict) else None
    if not isinstance(job, dict):
        return errors + ["qemu-kernel-smoke job missing"]
    require(job.get("runs-on") == "ubuntu-latest", "unexpected QEMU runner")
    require(job.get("timeout-minutes") == "60",
            "QEMU job timeout must be 60 minutes")
    condition = job.get("if")
    require(isinstance(condition, str) and
            "github.event.pull_request.draft == false" in condition,
            "draft PR guard missing")
    env = job.get("env", {})
    if not isinstance(env, dict):
        return errors + ["job environment missing"]
    expected = {
        "BUILDTHREADS": "2",
        "NEXUS_PROFILE": "diagnostic",
        "NEXUS_QEMU_MODE": "headless",
        "NEXUS_QEMU_MEMORY_MIB": "1024",
        "NEXUS_QEMU_CPUS": "1",
        "NEXUS_QEMU_TIMEOUT_SECONDS": "60",
        "NEXUS_QEMU_EXPECT_MARKER": MARKER,
    }
    for key, value in expected.items():
        require(env.get(key) == value, f"missing/changed resource guard: {key}")
    steps = job.get("steps", [])
    if not isinstance(steps, list):
        return errors + ["job steps missing"]
    commands = "\n".join(step.get("run", "") for step in steps
                         if isinstance(step, dict) and isinstance(step.get("run"), str))
    require("bash scripts/nexus/baseline/build-x86_64.sh" in commands,
            "G1 build wrapper missing")
    require("bash scripts/nexus/baseline/run-qemu-x86_64.sh" in commands,
            "bounded G2a runner missing")
    require("MARKER_REACHED_FINAL=yes" in commands and
            "FINAL_STATUS=marker-reached" in commands,
            "G2a marker state not checked")
    return errors


def negative_cases(original: dict) -> None:
    cases = {
        "synchronize trigger": lambda x: x["on"]["pull_request"]["types"].append("synchronize"),
        "push trigger": lambda x: x["on"].update({"push": {"branches": ["nexus/main"]}}),
        "wrong branch": lambda x: x["on"]["pull_request"].update({"branches": ["master"]}),
        "no cancellation": lambda x: x["concurrency"].update({"cancel-in-progress": "false"}),
        "two vCPUs": lambda x: x["jobs"]["qemu-kernel-smoke"]["env"].update({"NEXUS_QEMU_CPUS": "2"}),
        "no timeout": lambda x: x["jobs"]["qemu-kernel-smoke"].update({"timeout-minutes": "0"}),
        "missing marker": lambda x: x["jobs"]["qemu-kernel-smoke"]["env"].pop("NEXUS_QEMU_EXPECT_MARKER"),
        "write permission": lambda x: x.update({"permissions": {"contents": "write"}}),
    }
    for label, mutation in cases.items():
        mutant = deepcopy(original)
        mutation(mutant)
        if not check(mutant):
            raise AssertionError(f"validator accepted weakened policy: {label}")


def main() -> None:
    if len(sys.argv) > 2:
        raise SystemExit("usage: verify-qemu-policy.py [workflow.yml]")
    workflow = Path(sys.argv[1]) if len(sys.argv) == 2 else DEFAULT
    try:
        document = yaml.load(workflow.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    except (OSError, yaml.YAMLError) as exc:
        raise SystemExit(f"QEMU policy YAML rejected: {exc}") from exc
    failures = check(document)
    if failures:
        raise SystemExit("QEMU policy FAIL:\n- " + "\n- ".join(failures))
    negative_cases(document)
    print("QEMU policy PASS: actual workflow + 8 rejected adversarial mutations")
    print("E1 policy structure + E2 host mutation tests; NOT G1/G2a evidence")


if __name__ == "__main__":
    main()
