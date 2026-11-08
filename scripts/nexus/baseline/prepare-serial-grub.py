#!/usr/bin/env python3
"""Fail-closed BIOS GRUB serial marker setup for Nexus diagnostic builds only.

Never call on upstream source files or a finished ISO. This edits only the
build-tree BIOS grub.cfg, and --check verifies the extracted ISO configuration.
"""

import argparse
import hashlib
import os
from pathlib import Path
import re
import stat
import sys
import tempfile

DEFAULT = re.compile(r'^\s*set\s+default\s*=\s*0\s*(?:#.*)?$')
MENU = re.compile(r'^menuentry\s+"AROS64 with native Gfx"\s*\{\s*$')
BOOT = re.compile(r'^(\s*multiboot2\s+)(/boot/pc/bootstrap\.xz)(\s+.*)?$')
FORBIDDEN = re.compile(r'^\s*(?:configfile|source|eval|chainloader|load_env|submenu|function)\b')
DEBUG = re.compile(r'^debug(?:=.*)?$')


def fail(message):
    raise ValueError(message)


def transform(data, check=False):
    if len(data) > 131072 or b'\x00' in data:
        fail('GRUB input is oversized or binary')
    text = data.decode('utf-8')
    if '\r' in text or not text.endswith('\n'):
        fail('unexpected GRUB line endings')
    lines = text.splitlines(keepends=True)
    active = [(i, s.rstrip('\n')) for i, s in enumerate(lines)
              if s.strip() and not s.lstrip().startswith('#')]
    if sum(bool(DEFAULT.fullmatch(s)) for _, s in active) != 1:
        fail('exactly one literal default=0 required')
    if sum(bool(re.match(r'^\s*set\s+default\s*=', s)) for _, s in active) != 1:
        fail('dynamic or duplicate default')
    if any(FORBIDDEN.match(s) or '`' in s or re.search(r';(?!\s*then\s*$)', s) for _, s in active):
        fail('unsupported GRUB control flow')
    menus = [(i, s) for i, s in active if re.match(r'^\s*menuentry\b', s)]
    if not menus or not MENU.fullmatch(menus[0][1]):
        fail('unexpected default BIOS menu entry')
    start = menus[0][0]
    default_index = next(i for i, line in active if DEFAULT.fullmatch(line))
    if default_index >= start or any(lines[i].strip() and not lines[i].lstrip().startswith('#')
                                     for i in range(default_index + 1, start)):
        fail('default menu is not the immediate top-level entry')
    end = next((i for i in range(start + 1, len(lines)) if lines[i].strip() == '}'), None)
    if end is None or any('{' in s for s in lines[start + 1:end]):
        fail('unexpected default menu structure')
    commands = [(i, s.rstrip('\n')) for i, s in enumerate(lines[start + 1:end], start + 1)
                if re.match(r'^\s*multiboot2\b', s)]
    if len(commands) != 1:
        fail('default entry must contain exactly one multiboot2 command')
    if any(s.strip() and not s.lstrip().startswith('#') and
           not re.match(r'^\s*(?:multiboot2|module2)\s+', s)
           for s in lines[start + 1:end]):
        fail('unsupported default entry command')
    index, line = commands[0]
    match = BOOT.fullmatch(line)
    if not match:
        fail('unexpected bootstrap command')
    tail = (match.group(3) or '').strip().split()
    if tail[:2] != ['ATA=32bit', '$bootstrap_flags'] or (len(tail) == 3 and tail[2] != 'debug=serial') or len(tail) not in (2, 3):
        fail('unexpected bootstrap arguments')
    if any(DEBUG.fullmatch(token) for token in tail):
        if tail.count('debug=serial') != 1 or sum(bool(DEBUG.fullmatch(t)) for t in tail) != 1:
            fail('conflicting or duplicate debug tokens')
        new = data
    else:
        if check:
            fail('default entry does not request debug=serial')
        lines[index] = line.rstrip() + ' debug=serial\n'
        new = ''.join(lines).encode('utf-8')
    if check and new != data:
        fail('check mode must not change GRUB')
    return new


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--apply', action='store_true')
    group.add_argument('--check', action='store_true')
    ap.add_argument('grub_cfg')
    args = ap.parse_args()
    path = Path(args.grub_cfg)
    if path.is_symlink() or not path.is_file():
        fail('GRUB file must be a regular non-symlink')
    mode = path.stat().st_mode
    if not stat.S_ISREG(mode):
        fail('GRUB file is not regular')
    old = path.read_bytes()
    new = transform(old, check=args.check)
    before = hashlib.sha256(old).hexdigest()
    after = hashlib.sha256(new).hexdigest()
    if args.apply and new != old:
        fd, temp = tempfile.mkstemp(prefix='.nexus-grub-', dir=path.parent)
        try:
            os.fchmod(fd, stat.S_IMODE(mode))
            with os.fdopen(fd, 'wb') as stream:
                stream.write(new)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp, path)
        finally:
            if os.path.exists(temp):
                os.unlink(temp)
    print('GRUB_SERIAL_STATUS=' + ('checked' if args.check else 'prepared'))
    print('GRUB_BEFORE_SHA256=' + before)
    print('GRUB_AFTER_SHA256=' + after)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, UnicodeError, OSError) as exc:
        print('nexus-grub-serial: ERROR: ' + str(exc), file=sys.stderr)
        sys.exit(1)
