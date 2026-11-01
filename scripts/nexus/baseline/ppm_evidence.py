#!/usr/bin/env python3
"""Strict, bounded QEMU P6 framebuffer validation for Nexus host evidence.

QEMU's HMP screendump emits a canonical binary PPM header:
P6\nWIDTH HEIGHT\n255\n followed by exactly width*height*3 bytes.
This intentionally rejects comments, extra whitespace, and other PPM variants:
evidence that cannot be unambiguously parsed must not validate.
"""
import re

MAX_PPM_BYTES = 16 * 1024 * 1024
_HEADER = re.compile(rb"\AP6\n([1-9][0-9]*) ([1-9][0-9]*)\n255\n")


def validate_ppm_bytes(data: bytes) -> tuple[int, int]:
    """Return (width, height), or reject truncated/extra/malformed pixels."""
    if len(data) > MAX_PPM_BYTES:
        raise ValueError("PPM exceeds bounded evidence size")
    match = _HEADER.match(data)
    if match is None:
        raise ValueError("invalid canonical P6 header")
    width, height = int(match.group(1)), int(match.group(2))
    if width * height > (MAX_PPM_BYTES - match.end()) // 3:
        raise ValueError("PPM dimensions exceed bounded evidence size")
    expected = match.end() + width * height * 3
    if len(data) != expected:
        raise ValueError("PPM pixel payload length mismatch")
    return width, height
