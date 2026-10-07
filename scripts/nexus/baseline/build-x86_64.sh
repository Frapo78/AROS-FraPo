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

first_version_line()
{
    "$1" --version 2>&1 | sed -n '1p' | tr '\r\n' '  '
}

for cmd in git make awk bash python3 cc c++ sed tr; do
    need "$cmd"
done

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git -C "$script_dir" rev-parse --show-toplevel 2>/dev/null)" ||
    die "script must run from an AROS-FraPo Git worktree"
repo_root="$(cd -- "$repo_root" && pwd -P)"

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
if [ -n "$(git -C "$repo_root" status --porcelain --untracked-files=normal)" ]; then
    die "source tree is dirty; baseline evidence requires a clean Git worktree"
fi
source_dirty=no

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

mkdir -p "$work_root"
work_root="$(cd -- "$work_root" && pwd -P)"
case "$work_root/" in
    "$repo_root/"*)
        die "NEXUS_WORK_ROOT must be outside the Git worktree"
        ;;
esac

host_os="$(uname -s)"
host_arch="$(uname -m)"
host_cc_version="$(first_version_line cc)"
host_cxx_version="$(first_version_line c++)"

crosstools_tree="$(git -C "$repo_root" rev-parse HEAD:tools/crosstools)"
collect_tree="$(git -C "$repo_root" rev-parse HEAD:tools/collect-aros)"
stage_driver_blob="$(git -C "$repo_root" rev-parse HEAD:scripts/azure/aros-stage.sh)"
configure_blob="$(git -C "$repo_root" rev-parse HEAD:configure)"

toolchain_input_key="$(
    printf '%s\n' \
        "$source_sha" \
        "$host_os" \
        "$host_arch" \
        "$target" \
        "$gcc_version" \
        "$binutils_version" \
        "$crosstools_tree" \
        "$collect_tree" \
        "$stage_driver_blob" \
        "$configure_blob" |
        sha256_text
)"

attempt_id="$(date -u '+%Y%m%dT%H%M%SZ')-$$"
run_root="$work_root/runs/$source_sha/$profile/$attempt_id"
build_dir="$run_root/build"
toolchain_dir="$run_root/toolchain"
ports_dir="$run_root/portssources"
artifact_dir="$run_root/artifacts"

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

[ ! -e "$run_root" ] || die "run path already exists: $run_root"
mkdir -p "$build_dir" "$toolchain_dir" "$ports_dir" "$artifact_dir"

manifest="$artifact_dir/build-manifest.txt"
submodule_manifest="$artifact_dir/submodules.txt"
iso_out="$artifact_dir/aros-pc-x86_64.iso"
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
    if [ -n "${NEXUS_GCC_VERSION:-}" ]; then
        printf 'GCC_VERSION_SOURCE=override\n'
    else
        printf 'GCC_VERSION_SOURCE=config/gcc_def\n'
    fi
    printf 'BINUTILS_VERSION=%s\n' "$binutils_version"
    if [ -n "${NEXUS_BINUTILS_VERSION:-}" ]; then
        printf 'BINUTILS_VERSION_SOURCE=override\n'
    else
        printf 'BINUTILS_VERSION_SOURCE=config/binutils_def\n'
    fi
    printf 'CROSSTOOLS_TREE=%s\n' "$crosstools_tree"
    printf 'COLLECT_AROS_TREE=%s\n' "$collect_tree"
    printf 'STAGE_DRIVER_BLOB=%s\n' "$stage_driver_blob"
    printf 'CONFIGURE_BLOB=%s\n' "$configure_blob"
    printf 'TOOLCHAIN_INPUT_KEY=%s\n' "$toolchain_input_key"
    printf 'HOST_OS=%s\n' "$host_os"
    printf 'HOST_ARCH=%s\n' "$host_arch"
    printf 'HOST_UNAME=%s\n' "$(uname -a | tr '\r\n' '  ')"
    printf 'HOST_CC_VERSION=%s\n' "$host_cc_version"
    printf 'HOST_CXX_VERSION=%s\n' "$host_cxx_version"
    printf 'GIT_VERSION=%s\n' "$(git --version | tr '\r\n' '  ')"
    printf 'MAKE_VERSION=%s\n' "$(make --version | sed -n '1p' | tr '\r\n' '  ')"
    printf 'BUILDTHREADS=%s\n' "$jobs"
    printf 'CCACHE_DISABLE=1\n'
    printf 'RUN_ROOT=%s\n' "$run_root"
    printf 'BUILD_DIR=%s\n' "$build_dir"
    printf 'TOOLCHAIN_DIR=%s\n' "$toolchain_dir"
    printf 'PORTSSOURCES_DIR=%s\n' "$ports_dir"
    printf 'SUBMODULE_MANIFEST=%s\n' "$submodule_manifest"
} > "$manifest"

git -C "$repo_root" submodule status --recursive > "$submodule_manifest"
printf 'SUBMODULE_MANIFEST_SHA256=%s\n' "$(sha256_file "$submodule_manifest")" >> "$manifest"

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

# The upstream stage driver enables ccache. Baseline evidence disables cache
# reuse so prior host state cannot satisfy this build attempt.
export CCACHE_DISABLE=1

printf 'Building fresh AROS toolchain for baseline attempt %s...\n' "$attempt_id"
"$repo_root/scripts/azure/aros-stage.sh" toolchain "${configure_args[@]}"

toolchain_cc="$toolchain_dir/bin/x86_64-aros-gcc"
toolchain_ld="$toolchain_dir/bin/x86_64-aros-ld"
[ -x "$toolchain_cc" ] || die "expected compiler not found: $toolchain_cc"
[ -x "$toolchain_ld" ] || die "expected linker not found: $toolchain_ld"

{
    printf 'TOOLCHAIN_CC=%s\n' "$toolchain_cc"
    printf 'TOOLCHAIN_CC_SHA256=%s\n' "$(sha256_file "$toolchain_cc")"
    printf 'TOOLCHAIN_CC_VERSION=%s\n' "$(first_version_line "$toolchain_cc")"
    printf 'TOOLCHAIN_LD=%s\n' "$toolchain_ld"
    printf 'TOOLCHAIN_LD_SHA256=%s\n' "$(sha256_file "$toolchain_ld")"
    printf 'TOOLCHAIN_LD_VERSION=%s\n' "$(first_version_line "$toolchain_ld")"
} >> "$manifest"

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

{
    printf 'ARTIFACT=%s\n' "$iso_out"
    printf 'ARTIFACT_SIZE=%s\n' "$iso_size"
    printf 'ARTIFACT_SHA256=%s\n' "$iso_sha256"
} >> "$manifest"

status=success

printf 'Baseline ISO: %s\n' "$iso_out"
printf 'SHA-256: %s\n' "$iso_sha256"
printf 'Manifest: %s\n' "$manifest"
