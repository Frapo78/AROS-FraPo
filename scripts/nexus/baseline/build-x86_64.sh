#!/usr/bin/env bash
#
# Nexus x86-64 baseline build harness.
#
# This deliberately wraps the upstream AROS stage driver. It does not replace
# the AROS build system and does not claim bit-for-bit reproducible output.
#
set -euo pipefail

die()
{
    printf 'nexus-baseline: ERROR: %s\n' "$*" >&2
    exit 1
}

need()
{
    command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

sha256_file()
{
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" | awk '{print $1}'
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$1" | awk '{print $1}'
    else
        die "sha256sum or shasum is required"
    fi
}

sha256_text()
{
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum | awk '{print $1}'
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 | awk '{print $1}'
    else
        die "sha256sum or shasum is required"
    fi
}

for cmd in git make awk bash python3; do
    need "$cmd"
done

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(git -C "$script_dir" rev-parse --show-toplevel 2>/dev/null)" ||
    die "script must run from an AROS-FraPo Git worktree"

target="${NEXUS_TARGET:-pc-x86_64}"
profile="${NEXUS_PROFILE:-compat}"

case "$target" in
    pc-x86_64) ;;
    *) die "unsupported baseline target: $target (expected pc-x86_64)" ;;
esac

case "$profile" in
    compat|diagnostic) ;;
    *) die "unsupported profile: $profile (expected compat or diagnostic)" ;;
esac

source_sha="$(git -C "$repo_root" rev-parse HEAD)"
source_dirty=no
if [ -n "$(git -C "$repo_root" status --porcelain --untracked-files=normal)" ]; then
    source_dirty=yes
fi

if [ "$source_dirty" = yes ] && [ "${NEXUS_ALLOW_DIRTY:-0}" != 1 ]; then
    die "source tree is dirty; commit/stash changes or set NEXUS_ALLOW_DIRTY=1"
fi

source_gcc_default="$(tr -d '\r\n' < "$repo_root/config/gcc_def")"
source_binutils_default="$(tr -d '\r\n' < "$repo_root/config/binutils_def")"
gcc_version="${NEXUS_GCC_VERSION:-$source_gcc_default}"
binutils_version="${NEXUS_BINUTILS_VERSION:-$source_binutils_default}"

if [ -n "${NEXUS_WORK_ROOT:-}" ]; then
    work_root="$NEXUS_WORK_ROOT"
else
    [ -n "${HOME:-}" ] || die "HOME is unset; set NEXUS_WORK_ROOT explicitly"
    work_root="${XDG_CACHE_HOME:-$HOME/.cache}/aros-nexus/baseline"
fi

build_dir="$work_root/build-$target-$profile"
ports_dir="$work_root/portssources"

host_os="$(uname -s)"
host_arch="$(uname -m)"
host_key="$host_os-$host_arch"

crosstools_tree="$(git -C "$repo_root" rev-parse HEAD:tools/crosstools)"
collect_tree="$(git -C "$repo_root" rev-parse HEAD:tools/collect-aros)"
toolchain_key="$(
    printf '%s\n'         "$host_key"         "$target"         "$gcc_version"         "$binutils_version"         "$crosstools_tree"         "$collect_tree" |
        sha256_text
)"

toolchain_dir="$work_root/toolchains/$toolchain_key"
toolchain_marker="$toolchain_dir/.nexus-toolchain-complete"
toolchain_cc="$toolchain_dir/bin/x86_64-aros-gcc"
toolchain_ld="$toolchain_dir/bin/x86_64-aros-ld"

source_key="$source_sha"
if [ "$source_dirty" = yes ]; then
    source_key="$source_sha-dirty"
fi

attempt_id="$(date -u '+%Y%m%dT%H%M%SZ')-$$"
artifact_base="$work_root/artifacts/$source_key/$profile/$toolchain_key"
artifact_dir="$artifact_base/$attempt_id"
[ ! -e "$artifact_dir" ] || die "artifact attempt already exists: $artifact_dir"

if [ -n "${BUILDTHREADS:-}" ]; then
    jobs="$BUILDTHREADS"
elif command -v nproc >/dev/null 2>&1; then
    jobs="$(nproc)"
elif command -v sysctl >/dev/null 2>&1; then
    jobs="$(sysctl -n hw.ncpu 2>/dev/null || printf '1')"
else
    jobs=1
fi

case "$jobs" in
    ''|*[!0-9]*) die "BUILDTHREADS must be a positive integer" ;;
    0) die "BUILDTHREADS must be greater than zero" ;;
esac

mkdir -p "$work_root" "$ports_dir" "$artifact_base"
mkdir "$artifact_dir"
rm -rf "$build_dir"
mkdir -p "$build_dir"

manifest="$artifact_dir/build-manifest.txt"
iso_out="$artifact_dir/aros-pc-x86_64.iso"
ports_manifest="$artifact_dir/portssources.sha256"
status=failed

finish()
{
    rc=$?
    trap - EXIT
    {
        printf 'FINAL_STATUS=%s\n' "$status"
        printf 'EXIT_CODE=%s\n' "$rc"
        printf 'FINISHED_UTC=%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    } >> "$manifest"
    exit "$rc"
}
trap finish EXIT

{
    printf 'FORMAT=nexus-baseline-v0\n'
    printf 'INITIAL_STATUS=running\n'
    printf 'STARTED_UTC=%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    printf 'ATTEMPT_ID=%s\n' "$attempt_id"
    printf 'SOURCE_SHA=%s\n' "$source_sha"
    printf 'SOURCE_DIRTY=%s\n' "$source_dirty"
    printf 'TARGET=%s\n' "$target"
    printf 'PROFILE=%s\n' "$profile"
    printf 'BOOTLOADER=grub2\n'
    printf 'GCC_VERSION=%s\n' "$gcc_version"
    printf 'GCC_VERSION_SOURCE=%s\n'         "$([ -n "${NEXUS_GCC_VERSION:-}" ] && printf override || printf config/gcc_def)"
    printf 'BINUTILS_VERSION=%s\n' "$binutils_version"
    printf 'BINUTILS_VERSION_SOURCE=%s\n'         "$([ -n "${NEXUS_BINUTILS_VERSION:-}" ] && printf override || printf config/binutils_def)"
    printf 'CROSSTOOLS_TREE=%s\n' "$crosstools_tree"
    printf 'COLLECT_AROS_TREE=%s\n' "$collect_tree"
    printf 'TOOLCHAIN_KEY=%s\n' "$toolchain_key"
    printf 'HOST_OS=%s\n' "$host_os"
    printf 'HOST_ARCH=%s\n' "$host_arch"
    printf 'HOST_UNAME=%s\n' "$(uname -a | tr '\r\n' '  ')"
    printf 'BUILDTHREADS=%s\n' "$jobs"
    printf 'BUILD_DIR=%s\n' "$build_dir"
    printf 'TOOLCHAIN_DIR=%s\n' "$toolchain_dir"
    printf 'PORTSSOURCES_DIR=%s\n' "$ports_dir"
} > "$manifest"

configure_args=(
    "--target=$target"
    "--with-bootloader=grub2"
)

if [ -n "${NEXUS_GCC_VERSION:-}" ]; then
    configure_args+=("--with-gcc-version=$gcc_version")
fi

if [ -n "${NEXUS_BINUTILS_VERSION:-}" ]; then
    configure_args+=("--with-binutils-version=$binutils_version")
fi

if [ "$profile" = diagnostic ]; then
    configure_args+=("--with-serial-debug=yes")
fi

{
    printf 'CONFIGURE_ARGS='
    printf '%q ' "${configure_args[@]}"
    printf '\n'
} >> "$manifest"

export AROSSRCDIR="$repo_root"
export AROSBUILDDIR="$build_dir"
export AROSBUILDTOOLCHAINDIR="$toolchain_dir"
export AROSPORTSSRCSDIR="$ports_dir"
export BUILDTHREADS="$jobs"

toolchain_valid()
{
    [ -f "$toolchain_marker" ] || return 1
    [ -x "$toolchain_cc" ] || return 1
    [ -x "$toolchain_ld" ] || return 1

    marker_key="$(awk -F= '$1 == "KEY" { print $2; exit }' "$toolchain_marker")"
    marker_cc="$(awk -F= '$1 == "CC_SHA256" { print $2; exit }' "$toolchain_marker")"
    marker_ld="$(awk -F= '$1 == "LD_SHA256" { print $2; exit }' "$toolchain_marker")"

    [ "$marker_key" = "$toolchain_key" ] || return 1
    [ "$marker_cc" = "$(sha256_file "$toolchain_cc")" ] || return 1
    [ "$marker_ld" = "$(sha256_file "$toolchain_ld")" ] || return 1
}

if [ "${NEXUS_FORCE_TOOLCHAIN:-0}" = 1 ]; then
    rm -rf "$toolchain_dir"
fi

if ! toolchain_valid; then
    rm -rf "$toolchain_dir"
    mkdir -p "$toolchain_dir"

    printf 'Building AROS toolchain (key %s)...\n' "$toolchain_key"
    "$repo_root/scripts/azure/aros-stage.sh" toolchain "${configure_args[@]}"

    [ -x "$toolchain_cc" ] || die "expected compiler not found: $toolchain_cc"
    [ -x "$toolchain_ld" ] || die "expected linker not found: $toolchain_ld"

    {
        printf 'KEY=%s\n' "$toolchain_key"
        printf 'CC_SHA256=%s\n' "$(sha256_file "$toolchain_cc")"
        printf 'LD_SHA256=%s\n' "$(sha256_file "$toolchain_ld")"
    } > "$toolchain_marker"
else
    printf 'Reusing verified toolchain cache %s\n' "$toolchain_key"
fi

{
    printf 'TOOLCHAIN_CC=%s\n' "$toolchain_cc"
    printf 'TOOLCHAIN_CC_SHA256=%s\n' "$(sha256_file "$toolchain_cc")"
    printf 'TOOLCHAIN_CC_VERSION=%s\n'         "$("$toolchain_cc" --version | sed -n '1p' | tr '\r\n' '  ')"
    printf 'TOOLCHAIN_LD=%s\n' "$toolchain_ld"
    printf 'TOOLCHAIN_LD_SHA256=%s\n' "$(sha256_file "$toolchain_ld")"
    printf 'TOOLCHAIN_LD_VERSION=%s\n'         "$("$toolchain_ld" --version | sed -n '1p' | tr '\r\n' '  ')"
} >> "$manifest"

# The stage driver is upstream-owned. Use it for the core build instead of
# copying its configure/build policy into Nexus tooling.
printf 'Building AROS core for %s (%s profile)...\n' "$target" "$profile"
"$repo_root/scripts/azure/aros-stage.sh" core "${configure_args[@]}"

printf 'Building boot ISO...\n'
make -C "$build_dir" -j"$jobs" bootiso

built_iso="$build_dir/distfiles/aros-pc-x86_64.iso"
[ -f "$built_iso" ] || die "expected ISO was not produced: $built_iso"
[ -s "$built_iso" ] || die "produced ISO is empty: $built_iso"

cp -f "$built_iso" "$iso_out"
iso_sha256="$(sha256_file "$iso_out")"
iso_size="$(wc -c < "$iso_out" | tr -d '[:space:]')"

# Capture the external-source pool state after the build. This is provenance,
# not a claim that every file in the pool was consumed by this build.
python3 - "$ports_dir" "$ports_manifest" <<'PY'
from pathlib import Path
import hashlib
import json
import sys

root = Path(sys.argv[1])
out = Path(sys.argv[2])
records = []

if root.exists():
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        records.append((path.relative_to(root).as_posix(), digest.hexdigest()))

with out.open("w", encoding="utf-8") as handle:
    for relpath, digest in records:
        handle.write(f"{digest}  {json.dumps(relpath, ensure_ascii=True)}\n")
PY

{
    printf 'ARTIFACT=%s\n' "$iso_out"
    printf 'ARTIFACT_SIZE=%s\n' "$iso_size"
    printf 'ARTIFACT_SHA256=%s\n' "$iso_sha256"
    printf 'PORTSSOURCES_MANIFEST=%s\n' "$ports_manifest"
    printf 'PORTSSOURCES_MANIFEST_SHA256=%s\n' "$(sha256_file "$ports_manifest")"
} >> "$manifest"

status=success
printf 'Baseline ISO: %s\n' "$iso_out"
printf 'SHA-256: %s\n' "$iso_sha256"
printf 'Manifest: %s\n' "$manifest"
