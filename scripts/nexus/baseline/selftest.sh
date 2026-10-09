#!/usr/bin/env bash
#
# Fast negative/positive tests for the Nexus baseline evidence harness.
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
    ("$@") >/dev/null 2>&1
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

# The upstream stage driver is a /bin/sh script and is not guaranteed to
# carry the executable bit in every checkout. The wrapper must invoke it through
# sh rather than execute it directly.
grep -Fq 'sh "$stage_driver" toolchain' "$build" ||
    fail "build wrapper does not invoke toolchain stage through sh"
grep -Fq 'sh "$stage_driver" core' "$build" ||
    fail "build wrapper does not invoke core stage through sh"

# Exercise the actual resolver extracted from the build wrapper, not a copy.
resolver_source="$tmp/resolve-tool.sh"
sed -n '/^resolve_tool() {/,/^}/p' "$build" > "$resolver_source"
grep -q '^resolve_tool() {' "$resolver_source" ||
    fail "toolchain resolver is missing"
# The build wrapper uses die() for rejected layouts.
die() { fail "$*"; }
# shellcheck disable=SC1090
source "$resolver_source"
toolchain_dir="$tmp/toolchain"
mkdir -p "$toolchain_dir/bin"
expect_fail "missing cross compiler" resolve_tool x86_64-aros-gcc
printf '#!/bin/sh\nexit 0\n' > "$toolchain_dir/x86_64-aros-gcc"
chmod +x "$toolchain_dir/x86_64-aros-gcc"
[ "$(resolve_tool x86_64-aros-gcc)" = "$toolchain_dir/x86_64-aros-gcc" ] ||
    fail "root-layout compiler was not resolved"
mv "$toolchain_dir/x86_64-aros-gcc" "$toolchain_dir/bin/x86_64-aros-gcc"
[ "$(resolve_tool x86_64-aros-gcc)" = "$toolchain_dir/bin/x86_64-aros-gcc" ] ||
    fail "bin-layout compiler was not resolved"
cp "$toolchain_dir/bin/x86_64-aros-gcc" "$toolchain_dir/x86_64-aros-gcc"
expect_fail "ambiguous cross compiler" resolve_tool x86_64-aros-gcc
chmod -x "$toolchain_dir/x86_64-aros-gcc"
[ "$(resolve_tool x86_64-aros-gcc)" = "$toolchain_dir/bin/x86_64-aros-gcc" ] ||
    fail "non-executable duplicate should not shadow compiler"

# The linker must obey the same strict path resolution rules as GCC.
expect_fail "missing cross linker" resolve_tool x86_64-aros-ld
printf '#!/bin/sh\nexit 0\n' > "$toolchain_dir/x86_64-aros-ld"
chmod +x "$toolchain_dir/x86_64-aros-ld"
[ "$(resolve_tool x86_64-aros-ld)" = "$toolchain_dir/x86_64-aros-ld" ] ||
    fail "root-layout linker was not resolved"
mv "$toolchain_dir/x86_64-aros-ld" "$toolchain_dir/bin/x86_64-aros-ld"
[ "$(resolve_tool x86_64-aros-ld)" = "$toolchain_dir/bin/x86_64-aros-ld" ] ||
    fail "bin-layout linker was not resolved"
cp "$toolchain_dir/bin/x86_64-aros-ld" "$toolchain_dir/x86_64-aros-ld"
expect_fail "ambiguous cross linker" resolve_tool x86_64-aros-ld
chmod -x "$toolchain_dir/x86_64-aros-ld"
[ "$(resolve_tool x86_64-aros-ld)" = "$toolchain_dir/bin/x86_64-aros-ld" ] ||
    fail "non-executable duplicate should not shadow linker"

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
PROFILE=diagnostic
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

serial_path=""
previous=""
for arg in "$@"; do
    if [ "$previous" = "-serial" ]; then
        case "$arg" in
            file:*) serial_path="${arg#file:}" ;;
        esac
    fi
    previous="$arg"
done

if [ -n "${FAKE_QEMU_WRITE_MARKER:-}" ] && [ -n "$serial_path" ]; then
    mkdir -p "$(dirname -- "$serial_path")"
    printf '%s\n' "$FAKE_QEMU_WRITE_MARKER" >> "$serial_path"
fi

sleep "${FAKE_QEMU_SLEEP_SECONDS:-0}"
exit "${FAKE_QEMU_EXIT:-0}"
EOF
chmod +x "$fake_qemu"

orphan_iso="$tmp/orphan.iso"
printf 'unbound-iso\n' > "$orphan_iso"

expect_fail "ISO without G1 build manifest" \
    env NEXUS_QEMU_BINARY="$fake_qemu" \
    "$runner" "$orphan_iso" "$tmp/run-orphan"

# Normal interactive run remains unverified until a separate manual record exists.
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
    "$recorder" "$interactive" pass "duplicate verification must fail"

# A headless non-marker run may not be manually promoted to Wanderer success.
headless="$tmp/run-headless"
env NEXUS_QEMU_BINARY="$fake_qemu" \
    NEXUS_QEMU_MODE=headless \
    "$runner" "$iso" "$headless" >/dev/null

expect_fail "headless manual Wanderer pass" \
    "$recorder" "$headless" pass "headless must fail"

"$recorder" "$headless" fail "headless is not Wanderer proof" >/dev/null

# QEMU errors must not be promoted to success.
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

duplicate_key="$tmp/run-duplicate-key"
mkdir "$duplicate_key"
cp "$interactive/run-manifest.txt" "$duplicate_key/run-manifest.txt"
printf 'QEMU_EXIT_CODE=0\n' >> "$duplicate_key/run-manifest.txt"

expect_fail "duplicate run-manifest key" \
    "$recorder" "$duplicate_key" pass "duplicate key must fail"

bad_status="$tmp/run-bad-status"
mkdir "$bad_status"
sed 's/^FINAL_STATUS=.*/FINAL_STATUS=qemu-error-unverified/' \
    "$interactive/run-manifest.txt" > "$bad_status/run-manifest.txt"

expect_fail "inconsistent QEMU final status" \
    "$recorder" "$bad_status" pass "bad status must fail"

# Marker mode: a precise serial checkpoint is a separate, bounded claim.
marker='AROS64 - The AROS Research OS'
marker_ok="$tmp/run-marker-ok"
env \
    FAKE_QEMU_WRITE_MARKER="$marker" \
    FAKE_QEMU_SLEEP_SECONDS=10 \
    NEXUS_QEMU_BINARY="$fake_qemu" \
    NEXUS_QEMU_MODE=headless \
    NEXUS_QEMU_EXPECT_MARKER="$marker" \
    NEXUS_QEMU_TIMEOUT_SECONDS=4 \
    "$runner" "$iso" "$marker_ok" >/dev/null

grep -q '^FINAL_STATUS=marker-reached$' "$marker_ok/run-manifest.txt" ||
    fail "marker run did not record marker-reached"
grep -q '^MARKER_REACHED_FINAL=yes$' "$marker_ok/run-manifest.txt" ||
    fail "marker run did not record marker success"
grep -Fq -- "$marker" "$marker_ok/serial.log" ||
    fail "expected marker is missing from serial evidence"

# Marker timeout must fail with exit 124 and a distinct state.
marker_timeout="$tmp/run-marker-timeout"
set +e
FAKE_QEMU_SLEEP_SECONDS=10 \
NEXUS_QEMU_BINARY="$fake_qemu" \
NEXUS_QEMU_MODE=headless \
NEXUS_QEMU_EXPECT_MARKER="$marker" \
NEXUS_QEMU_TIMEOUT_SECONDS=1 \
    "$runner" "$iso" "$marker_timeout" >/dev/null 2>&1
marker_timeout_rc=$?
set -e

[ "$marker_timeout_rc" -eq 124 ] ||
    fail "expected marker timeout exit 124, got $marker_timeout_rc"
grep -q '^FINAL_STATUS=marker-timeout$' "$marker_timeout/run-manifest.txt" ||
    fail "marker timeout did not record marker-timeout"
grep -q '^MARKER_REACHED_FINAL=no$' "$marker_timeout/run-manifest.txt" ||
    fail "marker timeout incorrectly recorded marker success"

# QEMU exiting before the marker must fail even if QEMU itself exits zero.
marker_early_exit="$tmp/run-marker-early-exit"
set +e
NEXUS_QEMU_BINARY="$fake_qemu" \
NEXUS_QEMU_MODE=headless \
NEXUS_QEMU_EXPECT_MARKER="$marker" \
NEXUS_QEMU_TIMEOUT_SECONDS=4 \
    "$runner" "$iso" "$marker_early_exit" >/dev/null 2>&1
marker_early_rc=$?
set -e

[ "$marker_early_rc" -ne 0 ] ||
    fail "QEMU early exit without marker was accepted"
grep -q '^FINAL_STATUS=qemu-exited-before-marker$' "$marker_early_exit/run-manifest.txt" ||
    fail "early exit did not record qemu-exited-before-marker"

# The ISO must remain byte-identical to the artifact bound by G1 evidence.
printf 'tampered\n' >> "$iso"

expect_fail "tampered ISO provenance" \
    env NEXUS_QEMU_BINARY="$fake_qemu" \
    "$runner" "$iso" "$tmp/run-tampered"

printf 'nexus-baseline-selftest: PASS\n'
