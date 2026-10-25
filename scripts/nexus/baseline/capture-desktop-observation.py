#!/usr/bin/env python3
"""Capture one QEMU HMP screendump and bind it to a G2c observation manifest.

This is a diagnostic capture, not proof that Wanderer is usable.
"""
import argparse
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re
import subprocess
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args):
    root = Path(args.result_dir).resolve()
    manifest = root / "run-manifest.txt"
    if not manifest.is_file():
        raise ValueError("missing run-manifest.txt")
    # Refuse symlinks and pre-existing outputs to avoid overwriting evidence.
    screenshot = root / "desktop-observation.ppm"
    observation = root / "desktop-observation.txt"
    if screenshot.exists() or screenshot.is_symlink() or observation.exists() or observation.is_symlink():
        raise ValueError("observation already exists")
    monitor = Path(args.monitor_socket)
    if not monitor.is_socket():
        raise ValueError("QEMU HMP monitor socket unavailable")
    script = Path(__file__).with_name("capture-qemu-screen.py")
    if script.is_file():
        subprocess.run([sys.executable, str(script), str(monitor), str(screenshot)], check=True, timeout=20)
    else:
        import socket
        import time
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as conn:
            conn.settimeout(3)
            conn.connect(str(monitor))
            conn.sendall(("screendump " + str(screenshot) + "\\n").encode("ascii"))
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and not screenshot.is_file():
            time.sleep(0.1)
    if not screenshot.is_file() or screenshot.stat().st_size < 16:
        raise ValueError("screenshot missing or empty")
    data = screenshot.read_bytes()
    if not re.match(rb"^P6\\s+[0-9]+\\s+[0-9]+\\s+255\\s", data):
        raise ValueError("invalid PPM output")
    observation.write_text(
        "FORMAT=nexus-desktop-observation-v1\\n"
        "CAPTURED_UTC=" + datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") + "\\n"
        "RUN_MANIFEST_SHA256=" + sha(manifest) + "\\n"
        "SCREENSHOT=desktop-observation.ppm\\n"
        "SCREENSHOT_SHA256=" + sha(screenshot) + "\\n"
        "WANDERER_VERIFICATION=unverified\\n",
        encoding="utf-8",
    )
    print("Captured unverified desktop observation:", screenshot)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result_dir")
    parser.add_argument("monitor_socket")
    args = parser.parse_args()
    try:
        run(args)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print("observation failed:", exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
