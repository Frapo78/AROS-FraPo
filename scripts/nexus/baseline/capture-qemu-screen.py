#!/usr/bin/env python3
"""Capture an HMP framebuffer snapshot for debugging, never as boot proof."""

import os
import re
import socket
import sys
import time


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
                if os.path.isfile(screenshot_path):
                    with open(screenshot_path, "rb") as screenshot:
                        if screenshot.read(2) in (b"P6", b"P3"):
                            return True
                    return False
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
