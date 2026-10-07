#!/usr/bin/env bash
#
# Run a Nexus x86-64 baseline ISO under a conservative QEMU configuration.
#
# A QEMU launch is evidence of launch only. This script never claims that AROS
# reached Wanderer.
#
set -euo pipefail

die()
{
    printf 'nexus-qemu: ERROR: %s\n' "$*" >&2
    exit 1
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

manifest_value()
{
    manifest_file="$1"
    key="$2"

    count="$(awk -F= -v key="$key" '$1 == key { count++ } END { print count + 0 }' "$manifest_file")"
    [ "$count" -eq 1 ] ||
        die "$manifest_file must contain exactly one $key entry"

    awk -F= -v key="$key" '
        $1 == key {
            value=$0
            sub(/^[^=]*=/, "", value)
            print value
            exit
        }
    ' "$manifest_file"
}

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    printf 'usage: %s <aros-pc-x86_64.iso> [result-directory]\n' "$0" >&2
    exit 2
fi

[ -f "$1" ] || die "ISO not found: $1"
iso="$(cd -- "$(dirname -- "$1")" && pwd -P)/$(basename -- "$1")"
[ -s "$iso" ] || die "ISO is empty: $iso"

build_manifest="$(dirname -- "$iso")/build-manifest.txt"
[ -f "$build_manifest" ] ||
    die "baseline ISO is not accompanied by build-manifest.txt"

build_format="$(manifest_value "$build_manifest" FORMAT)"
build_status="$(manifest_value "$build_manifest" FINAL_STATUS)"
build_exit="$(manifest_value "$build_manifest" EXIT_CODE)"
build_artifact="$(manifest_value "$build_manifest" ARTIFACT)"
build_artifact_sha256="$(manifest_value "$build_manifest" ARTIFACT_SHA256)"
source_sha="$(manifest_value "$build_manifest" SOURCE_SHA)"
profile="$(manifest_value "$build_manifest" PROFILE)"
toolchain_input_key="$(manifest_value "$build_manifest" TOOLCHAIN_INPUT_KEY)"

[ "$build_format" = nexus-baseline-v0 ] ||
    die "unsupported build manifest format: $build_format"
[ "$build_status" = success ] ||
    die "build manifest does not describe a successful build: $build_status"
[ "$build_exit" = 0 ] ||
    die "build manifest has non-zero exit code: $build_exit"
[ "$build_artifact" = "$iso" ] ||
    die "ISO path does not match the artifact recorded by the build manifest"

iso_sha256="$(sha256_file "$iso")"
[ "$build_artifact_sha256" = "$iso_sha256" ] ||
    die "ISO hash does not match the build manifest"

[ -n "$source_sha" ] || die "build manifest has empty SOURCE_SHA"
[ -n "$profile" ] || die "build manifest has empty PROFILE"
[ -n "$toolchain_input_key" ] || die "build manifest has empty TOOLCHAIN_INPUT_KEY"

build_manifest_sha256="$(sha256_file "$build_manifest")"

qemu_bin="${NEXUS_QEMU_BINARY:-qemu-system-x86_64}"
qemu_path="$(command -v "$qemu_bin" 2>/dev/null || true)"
[ -n "$qemu_path" ] || die "QEMU binary not found: $qemu_bin"
[ -f "$qemu_path" ] || die "QEMU path is not a regular file: $qemu_path"

qemu_sha256="$(sha256_file "$qemu_path")"
qemu_version_full="$("$qemu_path" --version 2>&1)"
qemu_version="${qemu_version_full%%$'\n'*}"

mode="${NEXUS_QEMU_MODE:-interactive}"
case "$mode" in
    interactive|headless) ;;
    *) die "NEXUS_QEMU_MODE must be interactive or headless" ;;
esac

memory_mib="${NEXUS_QEMU_MEMORY_MIB:-1024}"
cpus="${NEXUS_QEMU_CPUS:-1}"

case "$memory_mib" in
    ''|*[!0-9]*) die "NEXUS_QEMU_MEMORY_MIB must be a positive integer" ;;
esac
case "$cpus" in
    ''|*[!0-9]*) die "NEXUS_QEMU_CPUS must be a positive integer" ;;
esac

[ "$memory_mib" -gt 0 ] || die "memory must be greater than zero"
[ "$cpus" -gt 0 ] || die "CPU count must be greater than zero"

timeout_seconds="${NEXUS_QEMU_TIMEOUT_SECONDS:-}"
if [ -n "$timeout_seconds" ]; then
    case "$timeout_seconds" in
        *[!0-9]*) die "NEXUS_QEMU_TIMEOUT_SECONDS must be a positive integer" ;;
    esac
    [ "$timeout_seconds" -gt 0 ] ||
        die "NEXUS_QEMU_TIMEOUT_SECONDS must be greater than zero"
    command -v timeout >/dev/null 2>&1 ||
        die "timeout command is required when NEXUS_QEMU_TIMEOUT_SECONDS is set"
fi

if [ "$#" -eq 2 ]; then
    result_dir="$2"
else
    stamp="$(date -u '+%Y%m%dT%H%M%SZ')-$$"
    result_dir="$(dirname -- "$iso")/qemu-$stamp"
fi

[ ! -e "$result_dir" ] || die "result path already exists: $result_dir"
mkdir -p "$result_dir"
result_dir="$(cd -- "$result_dir" && pwd -P)"

serial_log="$result_dir/serial.log"
manifest="$result_dir/run-manifest.txt"

qemu_args=(
    -machine pc
    -accel "tcg,thread=single"
    -cpu qemu64
    -smp "$cpus"
    -m "$memory_mib"
    -boot "order=d,menu=off"
    -cdrom "$iso"
    -nic none
    -serial "file:$serial_log"
    -monitor none
    -rtc base=utc
    -no-reboot
)

if [ "$mode" = headless ]; then
    qemu_args+=(-display none)
fi

{
    printf 'FORMAT=nexus-qemu-v0\n'
    printf 'STARTED_UTC=%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    printf 'INITIAL_STATUS=running-unverified\n'
    printf 'SOURCE_SHA=%s\n' "$source_sha"
    printf 'PROFILE=%s\n' "$profile"
    printf 'TOOLCHAIN_INPUT_KEY=%s\n' "$toolchain_input_key"
    printf 'BUILD_MANIFEST=%s\n' "$build_manifest"
    printf 'BUILD_MANIFEST_SHA256=%s\n' "$build_manifest_sha256"
    printf 'ISO=%s\n' "$iso"
    printf 'ISO_SHA256=%s\n' "$iso_sha256"
    printf 'QEMU_BINARY=%s\n' "$qemu_bin"
    printf 'QEMU_PATH=%s\n' "$qemu_path"
    printf 'QEMU_SHA256=%s\n' "$qemu_sha256"
    printf 'QEMU_VERSION=%s\n' "$qemu_version"
    printf 'MODE=%s\n' "$mode"
    printf 'MACHINE=pc\n'
    printf 'ACCEL=tcg-thread-single\n'
    printf 'CPU_MODEL=qemu64\n'
    printf 'VCPUS=%s\n' "$cpus"
    printf 'MEMORY_MIB=%s\n' "$memory_mib"
    printf 'NETWORK=none\n'
    printf 'SERIAL_LOG=%s\n' "$serial_log"
    printf 'WANDERER_VERIFICATION=unverified\n'
    printf 'QEMU_ARGS='
    printf '%q ' "${qemu_args[@]}"
    printf '\n'
} > "$manifest"

printf 'Starting QEMU. Close the VM after the observation is complete.\n'
printf 'This run remains UNVERIFIED until a separate verification is recorded.\n'
printf 'Run directory: %s\n' "$result_dir"

set +e
if [ -n "$timeout_seconds" ]; then
    timeout --signal=TERM "$timeout_seconds" "$qemu_path" "${qemu_args[@]}"
    rc=$?
else
    "$qemu_path" "${qemu_args[@]}"
    rc=$?
fi
set -e

{
    printf 'QEMU_EXIT_CODE=%s\n' "$rc"
    printf 'FINISHED_UTC=%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

    if [ "$rc" -eq 0 ]; then
        printf 'FINAL_STATUS=vm-exited-unverified\n'
    elif [ "$rc" -eq 124 ]; then
        printf 'FINAL_STATUS=timeout-unverified\n'
    else
        printf 'FINAL_STATUS=qemu-error-unverified\n'
    fi
} >> "$manifest"

printf 'QEMU exited with code %s. No Wanderer success claim has been made.\n' "$rc"
printf 'Manifest: %s\n' "$manifest"

exit "$rc"
