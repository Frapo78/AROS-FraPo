#!/usr/bin/env bash
#
# Fast behavioural tests for the Nexus baseline evidence harness.
# Does not compile or boot AROS.
#
set -euo pipefail

die()
{
    printf 'nexus-selftest: ERROR: %s\n' "$*" >&2
    exit 1
}

expect_failure()
{
    label="$1"
    shift

    set +e
    "$@" >/dev/null 2>&1
    rc=$?
    set -e

    [ "$rc" -ne 0 ] || die "expected failure: $label"
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

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

artifact_dir="$tmp/artifacts"
mkdir -p "$artifact_dir"

iso="$artifact_dir/aros-pc-x86_64.iso"
printf 'nexus-baseline-selftest-iso\n' > "$iso"
iso_sha256="$(sha256_file "$iso")"

build_manifest="$artifact_dir/build-manifest.txt"
cat > "$build_manifest" <<EOF
FORMAT=nexus-baseline-v0
SOURCE_SHA=selftest-source
PROFILE=compat
TOOLCHAIN_INPUT_KEY=selftest-toolchain
ARTIFACT=$iso
ARTIFACT_SHA256=$iso_sha256
FINAL_STATUS=success
EXIT_CODE=0
EOF

fake_qemu="$tmp/qemu-system-x86_64"
cat > "$fake_qemu" <<'EOF'
#!/usr/bin/env bash
set -eu
if [ "${1:-}" = "--version" ]; then
    printf 'QEMU emulator version nexus-selftest\n'
    exit 0
fi
exit "${FAKE_QEMU_EXIT:-0}"
EOF
chmod +x "$fake_qemu"

run_ok="$tmp/run-ok"
NEXUS_QEMU_BINARY="$fake_qemu" \
    "$script_dir/run-qemu-x86_64.sh" "$iso" "$run_ok"

grep -q '^FINAL_STATUS=vm-exited-unverified$' "$run_ok/run-manifest.txt" ||
    die "successful fake QEMU run did not record expected final status"
grep -q '^SOURCE_SHA=selftest-source$' "$run_ok/run-manifest.txt" ||
    die "run manifest lost build source provenance"
grep -q '^BUILD_MANIFEST_SHA256=' "$run_ok/run-manifest.txt" ||
    die "run manifest did not bind the build manifest"
grep -q '^QEMU_SHA256=' "$run_ok/run-manifest.txt" ||
    die "run manifest did not record QEMU binary identity"

NEXUS_OBSERVER=nexus-selftest \
    "$script_dir/record-wanderer-result.sh" \
    "$run_ok" pass "self-test interactive pass"

grep -q '^RESULT=pass$' "$run_ok/wanderer-verification.txt" ||
    die "manual pass was not recorded"

expect_failure "verification overwrite" \
    "$script_dir/record-wanderer-result.sh" \
    "$run_ok" pass "duplicate should fail"

run_headless="$tmp/run-headless"
NEXUS_QEMU_BINARY="$fake_qemu" \
NEXUS_QEMU_MODE=headless \
    "$script_dir/run-qemu-x86_64.sh" "$iso" "$run_headless"

expect_failure "headless manual pass" \
    "$script_dir/record-wanderer-result.sh" \
    "$run_headless" pass "headless should fail"

run_error="$tmp/run-error"
set +e
FAKE_QEMU_EXIT=7 \
NEXUS_QEMU_BINARY="$fake_qemu" \
    "$script_dir/run-qemu-x86_64.sh" "$iso" "$run_error" >/dev/null 2>&1
qemu_rc=$?
set -e

[ "$qemu_rc" -eq 7 ] ||
    die "QEMU error exit code was not preserved"

expect_failure "QEMU-error manual pass" \
    "$script_dir/record-wanderer-result.sh" \
    "$run_error" pass "QEMU error should fail"

printf 'tampered\n' >> "$iso"
expect_failure "tampered ISO provenance" \
    env NEXUS_QEMU_BINARY="$fake_qemu" \
    "$script_dir/run-qemu-x86_64.sh" "$iso" "$tmp/run-tampered"

printf 'Nexus baseline harness self-test: PASS\n'
