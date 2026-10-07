#!/usr/bin/env bash
#
# Record an explicit human-observed Wanderer result for a completed QEMU run.
#
# This is separate from the launcher so "VM started" cannot be confused with
# "AROS reached a usable desktop".
#
set -euo pipefail

die()
{
    printf 'nexus-record: ERROR: %s\n' "$*" >&2
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
    local key="$1"

    awk -F= -v key="$key"         '$1 == key { value=$0; sub(/^[^=]*=/, "", value) } END { print value }'         "$manifest"
}

if [ "$#" -lt 2 ] || [ "$#" -gt 4 ]; then
    printf 'usage: %s <run-directory> <pass|fail> [note] [evidence-file]\n' "$0" >&2
    exit 2
fi

[ -d "$1" ] || die "run directory not found: $1"
run_dir="$(cd -- "$1" && pwd)"
result="$2"
note="${3:-}"
evidence="${4:-}"

case "$result" in
    pass|fail) ;;
    *) die "result must be pass or fail" ;;
esac

manifest="$run_dir/run-manifest.txt"
[ -f "$manifest" ] || die "run manifest not found: $manifest"

final_status="$(manifest_value FINAL_STATUS)"
qemu_exit="$(manifest_value QEMU_EXIT_CODE)"
mode="$(manifest_value MODE)"
iso_sha256="$(manifest_value ISO_SHA256)"

[ -n "$final_status" ] || die "QEMU run is incomplete: FINAL_STATUS is missing"
[ -n "$qemu_exit" ] || die "QEMU run is incomplete: QEMU_EXIT_CODE is missing"
[ -n "$mode" ] || die "QEMU run manifest has no MODE"
[ -n "$iso_sha256" ] || die "QEMU run manifest has no ISO_SHA256"

if [ "$result" = pass ]; then
    [ "$qemu_exit" = 0 ] ||
        die "cannot record pass for a QEMU run with exit code $qemu_exit"
    [ "$mode" = interactive ] ||
        die "cannot record manual Wanderer pass for a headless run"
fi

record_file="$run_dir/wanderer-verification.txt"
if [ -e "$record_file" ] && [ "${NEXUS_OVERWRITE_VERIFICATION:-0}" != 1 ]; then
    die "verification already exists; set NEXUS_OVERWRITE_VERIFICATION=1 to replace it"
fi

evidence_abs=""
if [ -n "$evidence" ]; then
    [ -f "$evidence" ] || die "evidence file not found: $evidence"
    evidence_abs="$(cd -- "$(dirname -- "$evidence")" && pwd)/$(basename -- "$evidence")"
fi

{
    printf 'FORMAT=nexus-wanderer-verification-v0\n'
    printf 'RECORDED_UTC=%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    printf 'RESULT=%s\n' "$result"
    printf 'METHOD=manual-observation\n'
    printf 'OBSERVER=%s\n' "${NEXUS_OBSERVER:-${USER:-unknown}}"
    printf 'RUN_MANIFEST_SHA256=%s\n' "$(sha256_file "$manifest")"
    printf 'ISO_SHA256=%s\n' "$iso_sha256"
    printf 'QEMU_FINAL_STATUS=%s\n' "$final_status"
    printf 'QEMU_EXIT_CODE=%s\n' "$qemu_exit"
    printf 'NOTE=%s\n' "$(printf '%s' "$note" | tr '\r\n' '  ')"

    if [ -n "$evidence_abs" ]; then
        printf 'EVIDENCE=%s\n' "$evidence_abs"
        printf 'EVIDENCE_SHA256=%s\n' "$(sha256_file "$evidence_abs")"
    else
        printf 'EVIDENCE=none\n'
    fi
} > "$record_file"

printf 'Recorded Wanderer verification: %s\n' "$result"
printf 'Evidence record: %s\n' "$record_file"
