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

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    printf 'usage: %s <aros-pc-x86_64.iso> [result-directory]\n' "$0" >&2
    exit 2
fi

[ -f "$1" ] || die "ISO not found: $1"
iso="$(cd -- "$(dirname -- "$1")" && pwd)/$(basename -- "$1")"
[ -s "$iso" ] || die "ISO is empty: $iso"

qemu_bin="${NEXUS_QEMU_BINARY:-qemu-system-x86_64}"
command -v "$qemu_bin" >/dev/null 2>&1 || die "QEMU binary not found: $qemu_bin"

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

qemu_version_full="$("$qemu_bin" --version 2>&1)"
qemu_version="${qemu_version_full%%$'\n'*}"

if [ "$#" -eq 2 ]; then
    result_dir="$2"
else
    stamp="$(date -u '+%Y%m%dT%H%M%SZ')"
    result_dir="$(dirname -- "$iso")/qemu-$stamp-$$"
fi

[ ! -e "$result_dir" ] || die "result path already exists: $result_dir"
mkdir -p "$result_dir"
result_dir="$(cd -- "$result_dir" && pwd)"

serial_log="$result_dir/serial.log"
manifest="$result_dir/run-manifest.txt"
iso_sha256="$(sha256_file "$iso")"

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
    printf 'ISO=%s\n' "$iso"
    printf 'ISO_SHA256=%s\n' "$iso_sha256"
    printf 'QEMU_BINARY=%s\n' "$qemu_bin"
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
    timeout --signal=TERM "$timeout_seconds" "$qemu_bin" "${qemu_args[@]}"
    rc=$?
else
    "$qemu_bin" "${qemu_args[@]}"
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
