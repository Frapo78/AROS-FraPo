#!/usr/bin/env python3
"""Fail-closed verifier for human-reviewed G2c desktop evidence."""
import argparse
import hashlib
from pathlib import Path
import re
import sys


def fields(path):
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" not in line:
            raise ValueError("malformed manifest line")
        key, value = line.split("=", 1)
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", key) or key in result:
            raise ValueError("invalid or duplicate manifest key")
        result[key] = value
    return result


def verify(folder):
    folder = Path(folder).resolve()
    run_path = folder / "run-manifest.txt"
    run = fields(run_path)
    proof = fields(folder / "desktop-evidence.txt")
    for key in ("SOURCE_SHA", "ISO_SHA256", "QEMU_SHA256", "QEMU_VERSION", "FINAL_STATUS"):
        if not run.get(key):
            raise ValueError("missing run provenance: " + key)
    if not re.fullmatch(r"[0-9a-f]{40}", run["SOURCE_SHA"]):
        raise ValueError("invalid source SHA")
    for key in ("ISO_SHA256", "QEMU_SHA256"):
        if not re.fullmatch(r"[0-9a-f]{64}", run[key]):
            raise ValueError("invalid SHA: " + key)
    if proof.get("FORMAT") != "nexus-desktop-evidence-v1":
        raise ValueError("unsupported evidence format")
    if proof.get("RUN_MANIFEST_SHA256") != hashlib.sha256(run_path.read_bytes()).hexdigest():
        raise ValueError("run manifest hash mismatch")
    for key in ("SOURCE_SHA", "ISO_SHA256"):
        if proof.get(key) != run[key]:
            raise ValueError("source or ISO provenance mismatch")
    if proof.get("VISUAL_RESULT") != "wanderer-usable" or proof.get("HUMAN_VERIFIED") != "yes":
        raise ValueError("no human-confirmed Wanderer")
    if not proof.get("REVIEWER") or not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", proof.get("REVIEWED_UTC", "")):
        raise ValueError("missing reviewer or invalid timestamp")
    filename = proof.get("SCREENSHOT", "")
    if not filename or Path(filename).name != filename or not filename.endswith(".ppm"):
        raise ValueError("invalid screenshot filename")
    screenshot = folder / filename
    if not screenshot.is_file() or screenshot.stat().st_size < 16:
        raise ValueError("missing screenshot")
    data = screenshot.read_bytes()
    if not data.startswith(b"P6\n") or proof.get("SCREENSHOT_SHA256") != hashlib.sha256(data).hexdigest():
        raise ValueError("screenshot format or hash mismatch")
    if run["FINAL_STATUS"] not in ("timeout-unverified", "vm-exited-unverified"):
        raise ValueError("not a desktop observation run")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result_directory")
    args = parser.parse_args()
    try:
        verify(args.result_directory)
    except (ValueError, OSError) as exc:
        print("G2c FAIL:", exc, file=sys.stderr)
        return 1
    print("G2c package validated: human assertion, not independent visual proof")
    return 0


if __name__ == "__main__":
    sys.exit(main())
