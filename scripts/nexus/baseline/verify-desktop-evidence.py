#!/usr/bin/env python3
"""Fail-closed verifier for human-reviewed G2c desktop evidence.

A valid package binds one QEMU run, one machine-captured PPM observation and
one subsequent human visual assertion. It does not independently recognize
Wanderer, authenticate the human reviewer, or prove runtime isolation.
"""
import argparse
from datetime import datetime
import hashlib
from pathlib import Path
import re
import sys

from ppm_evidence import MAX_PPM_BYTES, validate_ppm_bytes


def fields(path):
    if path.is_symlink():
        raise ValueError("symlinked evidence manifest")
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" not in line:
            raise ValueError("malformed manifest line")
        key, value = line.split("=", 1)
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", key) or key in result:
            raise ValueError("invalid or duplicate manifest key")
        result[key] = value
    return result


def timestamp(value):
    if not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", value or ""):
        raise ValueError("invalid evidence timestamp")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ValueError("invalid evidence timestamp") from exc


def verify(folder):
    folder = Path(folder).resolve()
    run_path = folder / "run-manifest.txt"
    observation_path = folder / "desktop-observation.txt"
    proof_path = folder / "desktop-evidence.txt"
    run = fields(run_path)
    observation = fields(observation_path)
    proof = fields(proof_path)

    if run.get("FORMAT") != "nexus-qemu-v0":
        raise ValueError("unsupported QEMU run format")
    for key in ("SOURCE_SHA", "ISO_SHA256", "QEMU_SHA256", "QEMU_VERSION", "FINAL_STATUS"):
        if not run.get(key):
            raise ValueError("missing run provenance: " + key)
    if not re.fullmatch(r"[0-9a-f]{40}", run["SOURCE_SHA"]):
        raise ValueError("invalid source SHA")
    for key in ("ISO_SHA256", "QEMU_SHA256"):
        if not re.fullmatch(r"[0-9a-f]{64}", run[key]):
            raise ValueError("invalid SHA: " + key)
    # A screenshot must be bound to the same ISO before and after QEMU ran.
    # Do not accept a self-consistent human proof if the guest media changed.
    if run.get("ISO_SHA256_AFTER") != run["ISO_SHA256"]:
        raise ValueError("missing or mismatched post-run ISO SHA")
    # A human usability claim requires a live guest with an explicitly
    # enabled local interactive console; headless screenshots are diagnostic.
    if run.get("INTERACTIVE_MODE") != "unix-vnc":
        raise ValueError("human G2c proof requires an interactive UNIX VNC run")
    if run["FINAL_STATUS"] != "timeout-unverified":
        raise ValueError("guest exited before interactive capture")

    run_sha = hashlib.sha256(run_path.read_bytes()).hexdigest()
    if observation.get("FORMAT") != "nexus-desktop-observation-v1":
        raise ValueError("unsupported capture observation format")
    if observation.get("RUN_MANIFEST_SHA256") != run_sha:
        raise ValueError("capture not bound to run manifest")
    if observation.get("WANDERER_VERIFICATION") != "unverified":
        raise ValueError("machine capture must not claim human verification")
    captured = timestamp(observation.get("CAPTURED_UTC"))

    if proof.get("FORMAT") != "nexus-desktop-evidence-v1":
        raise ValueError("unsupported evidence format")
    if proof.get("RUN_MANIFEST_SHA256") != run_sha:
        raise ValueError("run manifest hash mismatch")
    for key in ("SOURCE_SHA", "ISO_SHA256"):
        if proof.get(key) != run[key]:
            raise ValueError("source or ISO provenance mismatch")
    if proof.get("VISUAL_RESULT") != "wanderer-usable" or proof.get("HUMAN_VERIFIED") != "yes":
        raise ValueError("no human-confirmed Wanderer")
    if not proof.get("REVIEWER", "").strip():
        raise ValueError("missing reviewer")
    if timestamp(proof.get("REVIEWED_UTC")) < captured:
        raise ValueError("human review predates QEMU capture")

    filename = proof.get("SCREENSHOT", "")
    if filename != "desktop-observation.ppm" or observation.get("SCREENSHOT") != filename:
        raise ValueError("screenshot is not the QEMU capture")
    screenshot = folder / filename
    if screenshot.is_symlink() or not screenshot.is_file():
        raise ValueError("missing or symlinked screenshot")
    if screenshot.stat().st_size > MAX_PPM_BYTES:
        raise ValueError("PPM exceeds bounded evidence size")
    data = screenshot.read_bytes()
    validate_ppm_bytes(data)
    screenshot_sha = hashlib.sha256(data).hexdigest()
    if proof.get("SCREENSHOT_SHA256") != screenshot_sha:
        raise ValueError("human evidence screenshot hash mismatch")
    if observation.get("SCREENSHOT_SHA256") != screenshot_sha:
        raise ValueError("capture screenshot hash mismatch")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result_directory")
    args = parser.parse_args()
    try:
        verify(args.result_directory)
    except (ValueError, OSError, UnicodeError) as exc:
        print("G2c FAIL:", exc, file=sys.stderr)
        return 1
    print("G2c package validated: human assertion, not independent visual proof")
    return 0


if __name__ == "__main__":
    sys.exit(main())
