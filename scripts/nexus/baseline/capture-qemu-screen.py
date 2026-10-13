#!/usr/bin/env python3
"""Capture an HMP framebuffer snapshot for debugging, never as boot proof."""

import os
import re
import socket
import sys
import time


def complete_ppm(path: str) -> bool:
    """Check a bounded uncompressed P6 screenshot, not merely its magic bytes."""
    try:
        with open(path, "rb") as stream:
            header = stream.read(128)
        match = re.match(rb"P6\s+([1-9][0-9]*)\s+([1-9][0-9]*)\s+255\s", header)
        if not match:
            return False
        width, height = int(match.group(1)), int(match.group(2))
        size = match.end() + width * height * 3
        return 0 < size <= 16 * 1024 * 1024 and os.stat(path).st_size >= size
    except OSError:
        return False


def capture(monitor_path: str, screenshot_path: str) -> bool:
    # HMP uses an unstructured command line: reject shell/control characters.
    if not re.fullmatch(r"[/A-Za-z0-9_.-]+", screenshot_path):
        return False
    if not os.path.isabs(screenshot_path) or os.path.exists(screenshot_path):
        return False
    if not os.path.isabs(monitor_path):
        return False
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(2.0)
            connection.connect(monitor_path)
            connection.sendall(f"screendump {screenshot_path}\n".encode("ascii"))
            deadline = time.monotonic() + 3.0
            while time.monotonic() < deadline:
                if os.path.isfile(screenshot_path) and complete_ppm(screenshot_path):
                    return True
                time.sleep(0.1)
    except (OSError, UnicodeEncodeError):
        return False
    return False


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: capture-qemu-screen.py <hmp-socket> <output.ppm>", file=sys.stderr)
        sys.exit(2)
    if not capture(sys.argv[1], sys.argv[2]):
        print("QEMU screen capture unavailable or invalid", file=sys.stderr)
        sys.exit(1)
    print("QEMU screen capture saved (diagnostic only; boot unverified)")
