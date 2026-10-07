#!/usr/bin/env bash
#
# Fast behavioural tests for the Nexus baseline evidence harness.
# No AROS build or real QEMU execution is performed.
#
set -euo pipefail

fail()
{
    printf 'nexus-baseline-selftest: FAIL: %s\n' "$*" >&2
    exit 1
}

expect_fail()
{
    label="$1"
    shift

    set +e
    "$@" >/dev/null 2>&1
    rc=$?
    set -e

    [ "$rc" -ne 0 ] || fail "expected failure: $label"
}

sha256_file()
{
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" | awk '{print $1}'
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$1" | awk '{print $1}'
    else
        fail "sha256sum or shasum is required"
    fi
}

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git -C "$script_dir" rev-parse --show-toplevel)"
build="$script_dir/build-x86_64.sh"
runner="$script_dir/run-qemu-x86_64.sh"
recorder="$script_dir/record-wanderer-result.sh"

tmp="$(mktemp -d)"
inside_work="$repo_root/.nexus-baseline-selftest-work"
trap 'rm -rf "$tmp" "$inside_work"' EXIT

# Build-wrapper guards that must fail before any expensive build begins.
expect_fail "unsupported build target" \
    env NEXUS_TARGET=not-a-real-target "$build"

expect_fail "unsupported build profile" \
    env NEXUS_PROFILE=not-a-real-profile "$build"

expect_fail "workspace inside source tree" \
    env NEXUS_WORK_ROOT="$inside_work" "$build"

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

interactive="$tmp/run-interactive"
env NEXUS_QEMU_BINARY="$fake_qemu" \
    NEXUS_QEMU_MODE=interactive \
    "$runner" "$iso" "$interactive" >/dev/null

grep -q '^FINAL_STATUS=vm-exited-unverified$' "$interactive/run-manifest.txt" ||
    fail "interactive run did not record expected final status"
grep -q '^SOURCE_SHA=selftest-source$' "$interactive/run-manifest.txt" ||
    fail "run manifest lost source provenance"
grep -q '^BUILD_MANIFEST_SHA256=' "$interactive/run-manifest.txt" ||
    fail "run manifest is not bound to the build manifest"
grep -q '^QEMU_SHA256=' "$interactive/run-manifest.txt" ||
    fail "run manifest did not record QEMU binary identity"

env NEXUS_OBSERVER=nexus-selftest \
    "$recorder" "$interactive" pass "synthetic interactive harness test" >/dev/null

grep -q '^RESULT=pass$' "$interactive/wanderer-verification.txt" ||
    fail "interactive pass was not recorded"
grep -q '^RUN_MANIFEST_SHA256=' "$interactive/wanderer-verification.txt" ||
    fail "verification is not bound to the run manifest"

expect_fail "verification overwrite" \
    "$recorder" "$interactive" pass "duplicate must fail"

headless="$tmp/run-headless"
env NEXUS_QEMU_BINARY="$fake_qemu" \
    NEXUS_QEMU_MODE=headless \
    "$runner" "$iso" "$headless" >/dev/null

expect_fail "headless manual Wanderer pass" \
    "$recorder" "$headless" pass "headless must fail"

"$recorder" "$headless" fail "headless is not Wanderer proof" >/dev/null

failed="$tmp/run-qemu-error"
set +e
FAKE_QEMU_EXIT=42 \
NEXUS_QEMU_BINARY="$fake_qemu" \
NEXUS_QEMU_MODE=interactive \
    "$runner" "$iso" "$failed" >/dev/null 2>&1
qemu_rc=$?
set -e

[ "$qemu_rc" -eq 42 ] ||
    fail "expected synthetic QEMU exit 42, got $qemu_rc"

expect_fail "QEMU-error manual Wanderer pass" \
    "$recorder" "$failed" pass "failed QEMU must not pass"

"$recorder" "$failed" fail "synthetic QEMU failure" >/dev/null

# The ISO must remain byte-identical to the artifact bound by G1 evidence.
printf 'tampered\n' >> "$iso"
expect_fail "tampered ISO provenance" \
    env NEXUS_QEMU_BINARY="$fake_qemu" \
    "$runner" "$iso" "$tmp/run-tampered"

printf 'nexus-baseline-selftest: PASS\n'
