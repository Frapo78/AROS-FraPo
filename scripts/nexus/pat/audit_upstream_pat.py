#!/usr/bin/env python3
"""Fail-closed source-backed PAT layout audit; not a guest MMU test.

Requires an exact upstream AROS checkout. Observes only a narrow code pattern:
MAP_WriteCombine's PAT index, the non-WC branch, and CPU PAT setup.  This
script never writes an MSR or page table and makes no hardware safety claim.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess

MAP = Path('arch/x86_64-pc/kernel/mapglobal.c')
CPU = Path('arch/x86_64-pc/kernel/kernel_startup.c')
FLAGS = Path('compiler/include/aros/kernel.h')


def without_comments(source: str) -> str:
    """Remove comments without accepting pattern strings buried in comments."""
    return re.sub(r'/\*.*?\*/|//[^\n]*', '', source, flags=re.DOTALL)


def function_body(source: str, name: str) -> str:
    source = without_comments(source)
    matches = list(re.finditer(
        rf'\b(?:static\s+)?void\s+{re.escape(name)}\s*\([^{{}};]*\)\s*\{{',
        source,
    ))
    if len(matches) != 1:
        raise ValueError(f'expected exactly one {name} implementation')
    start = matches[0].end()
    level = 1
    for idx in range(start, len(source)):
        if source[idx] == '{':
            level += 1
        elif source[idx] == '}':
            level -= 1
            if level == 0:
                return source[start:idx]
    raise ValueError(f'unterminated {name} implementation')


def cache_bits(flags: int) -> tuple[int, int, int]:
    """Model the guarded *observed* source branch: PAT/PWT/PCD bits."""
    write_combine, write_through, cache_inhibit = 0x8, 0x2, 0x1
    if flags & write_combine:
        return 1, 0, 0
    return 0, int(bool(flags & write_through)), int(bool(flags & cache_inhibit))


def pat_index(flags: int) -> int:
    pat, pwt, pcd = cache_bits(flags)
    return (pat << 2) | (pcd << 1) | pwt


def audit_sources(map_text: str, cpu_text: str, flags_text: str) -> dict:
    errors: list[str] = []
    findings: dict = {}
    header = without_comments(flags_text)
    match = re.findall(r'\bMAP_WriteCombine\s*=\s*(0x[0-9a-fA-F]+|\d+)\s*,', header)
    if len(match) != 1 or int(match[0], 0) != 0x0008:
        errors.append('MAP_WriteCombine must be a unique flag with value 0x0008')

    for name in ('set_pte', 'set_pde_2m'):
        try:
            body = function_body(map_text, name)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        branch = re.compile(
            r'\bif\s*\(\s*flags\s*&\s*MAP_WriteCombine\s*\)\s*'
            r'tmp\.pat\s*=\s*1\s*;\s*else\s*\{\s*'
            r'tmp\.pwt\s*=\s*\(\s*flags\s*&\s*MAP_WriteThrough\s*\)\s*\?\s*1\s*:\s*0\s*;\s*'
            r'tmp\.pcd\s*=\s*\(\s*flags\s*&\s*MAP_CacheInhibit\s*\)\s*\?\s*1\s*:\s*0\s*;\s*\}',
            re.DOTALL,
        )
        if len(branch.findall(body)) != 1:
            errors.append(f'{name}: expected exact WC precedence and legacy PWT/PCD fallback')
        if len(re.findall(r'\btmp\.pat\s*=', body)) != 1:
            errors.append(f'{name}: unexpected additional PAT writes')
        if not re.search(r'\btmp\.us\s*=\s*1\s*;', body):
            errors.append(f'{name}: user/supervisor mapping assumption changed')
        if not re.search(r'\btmp\.p\s*=\s*\(\s*flags\s*&\s*\(\s*MAP_Readable\s*\|\s*MAP_Writable\s*\|\s*MAP_Executable\s*\)\s*\)\s*\?\s*1\s*:\s*0\s*;', body):
            errors.append(f'{name}: present-bit mapping assumption changed')
        if name == 'set_pde_2m' and not re.search(r'\btmp\.ps\s*=\s*1\s*;', body):
            errors.append('set_pde_2m: large-page (PS) bit assumption changed')
        findings[name] = 'PAT bit requested for WC; fallback PWT/PCD otherwise'

    try:
        cpu = function_body(cpu_text, 'core_CPUSetup')
    except ValueError as exc:
        errors.append(str(exc))
        cpu = ''
    cpuid_guard = re.search(
        r'if\s*\(\s*cpuid_edx\s*&\s*\(\s*1\s*<<\s*16\s*\)\s*\)\s*\{', cpu
    )
    if not cpuid_guard:
        errors.append('CPU PAT feature guard missing/changed')
    cpu_pat_block = ''
    if cpuid_guard:
        depth = 1
        for pos in range(cpuid_guard.end(), len(cpu)):
            if cpu[pos] == '{':
                depth += 1
            elif cpu[pos] == '}':
                depth -= 1
                if depth == 0:
                    cpu_pat_block = cpu[cpuid_guard.end():pos]
                    break
        if not cpu_pat_block:
            errors.append('CPU PAT feature guard block missing/empty')
    if not re.search(r'\bULONG\s+lo\s*=\s*0x00070406UL\s*;', cpu_pat_block):
        errors.append('IA32_PAT low dword changed')
    if not re.search(r'\bULONG\s+hi\s*=\s*0x00070401UL\s*;', cpu_pat_block):
        errors.append('IA32_PAT high dword changed')
    if not re.search(r'asm\s+volatile\s*\(\s*"wrmsr"\s*::\s*"c"\s*\(\s*0x277\s*\)\s*,\s*"a"\s*\(\s*lo\s*\)\s*,\s*"d"\s*\(\s*hi\s*\)\s*\)', cpu_pat_block):
        errors.append('IA32_PAT write to MSR 0x277 missing/changed')

    pat_bytes = (0x00070406 | (0x00070401 << 32)).to_bytes(8, 'little')
    if pat_bytes[4] != 1 or pat_bytes[0] != 6:
        errors.append('expected PAT entry 4 WC (1), entry 0 WB (6)')
    # Host-side deterministic model of the narrow mapping branch, not hardware.
    model = {f'{n:#04x}': pat_index(n) for n in range(0x10)}
    if not (model['0x00'] == 0 and model['0x01'] == 2 and
            model['0x02'] == 1 and model['0x03'] == 3 and
            all(model[f'{n:#04x}'] == 4 for n in range(0x8, 0x10))):
        errors.append('host PAT-index oracle inconsistent')
    return {
        'passed': not errors,
        'errors': errors,
        'mapping_findings': findings,
        'pat_bytes': list(pat_bytes),
        'requested_wc_pat_index': 4,
        'conflicting_flags_observation': 'WC takes precedence over cache-inhibit/write-through',
        'no_pat_cpu': 'UNVERIFIED: no-PAT CPU behavior requires guest/hardware test',
        'model_indices_flags_0_to_15': model,
        'evidence': 'E1 source guard + E2 focused host oracle/mutation tests; NOT E4',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--expected-sha', required=True, help='full 40-character upstream commit SHA')
    args = parser.parse_args()
    if not re.fullmatch(r'[0-9a-f]{40}', args.expected_sha):
        parser.error('--expected-sha must be an exact lowercase 40-char SHA')
    source = args.source_root.resolve()
    try:
        sha = subprocess.check_output(
            ['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True,
            stderr=subprocess.DEVNULL, timeout=5,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        parser.error('source root must be a Git checkout')
    if sha != args.expected_sha:
        parser.error(f'upstream SHA mismatch: expected {args.expected_sha}, got {sha}')
    dirty = subprocess.check_output(
        ['git', '-C', str(source), 'status', '--porcelain', '--untracked-files=no'],
        text=True, stderr=subprocess.DEVNULL, timeout=5,
    ).strip()
    if dirty:
        parser.error('upstream checkout has modified tracked files; source evidence must be clean')
    try:
        map_text = (source / MAP).read_text(encoding='utf-8')
        cpu_text = (source / CPU).read_text(encoding='utf-8')
        flags_text = (source / FLAGS).read_text(encoding='utf-8')
    except (OSError, UnicodeError) as exc:
        parser.error(f'cannot read upstream input: {exc}')
    result = audit_sources(map_text, cpu_text, flags_text)
    result['upstream_sha'] = sha
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
