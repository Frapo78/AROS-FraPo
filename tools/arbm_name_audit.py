#!/usr/bin/env python3
"""Audit tracked project naming and relative Markdown links; read-only.

Run from a complete git checkout: python3 tools/arbm_name_audit.py
Exit nonzero for broken relative links. Remaining old-name occurrences are
reported for manual classification, not silently replaced.
"""
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote

root = Path(__file__).resolve().parents[1]
try:
    raw = subprocess.check_output(["git", "-C", str(root), "ls-files", "-z"])
except (OSError, subprocess.CalledProcessError) as exc:
    sys.exit(f"ERROR: full tracked-file inventory unavailable: {exc}")
paths = [Path(x.decode("utf-8", "surrogateescape")) for x in raw.split(b"\0") if x]
old = re.compile(r"nexus", re.IGNORECASE)
links = re.compile(r"(?<!!)\[[^]]*\]\(([^)]+)\)")
issues = []
occurrences = []
for rel in paths:
    path = root / rel
    if path.is_symlink():
        continue
    if not path.is_file():
        issues.append(f"{rel}: tracked file missing from checkout")
        continue
    if rel.suffix.lower() not in {".md", ".markdown", ".txt", ".yml", ".yaml", ".json", ".py", ".sh", ".c", ".h", ".xml"} and rel.name != "AGENTS.md":
        continue
    try:
        data = path.read_text(encoding="utf-8")
    except (UnicodeError, OSError):
        continue
    for line_number, line in enumerate(data.splitlines(), 1):
        if old.search(line):
            occurrences.append(f"{rel}:{line_number}: {line.strip()[:180]}")
    if rel.suffix.lower() != ".md":
        continue
    for match in links.finditer(data):
        target = match.group(1).strip().split(" ", 1)[0].strip("<>")
        if not target or target.startswith(("#", "/", "http:", "https:", "mailto:", "data:")):
            continue
        target = unquote(target.split("#", 1)[0].split("?", 1)[0])
        if target:
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                issues.append(f"{rel}: link escapes repository -> {target}")
                continue
            if not resolved.exists():
                issues.append(f"{rel}: broken link -> {target}")
print(f"Tracked files inspected: {len(paths)}")
print(f"Old-name references requiring classification: {len(occurrences)}")
for item in occurrences:
    print("OLD_NAME:", item)
for item in issues:
    print("BROKEN_LINK:", item)
print(f"Broken relative Markdown links: {len(issues)}")
if issues:
    sys.exit(1)
