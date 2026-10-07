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
    if "$@" >/dev/null 2>&1; then
        fail "command unexpectedly succeeded: $*"
    fi
}

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
build="$script_dir/build-x86_64.sh"
runner="$script_dir/run-qemu-x86_64.sh"
recorder="$script_dir/record-wanderer-result.sh"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

iso="$tmp/fake.iso"
printf 'not-a-real-iso\n' > "$iso"

fake_qemu="$tmp/qemu-system-x86_64"
cat > "$fake_qemu" <<'FAKE'
#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "--version" ]; then
    printf 'QEMU emulator version nexus-selftest\n'
    exit 0
fi

exit "${FAKE_QEMU_EXIT:-0}"
FAKE
chmod +x "$fake_qemu"

expect_fail env NEXUS_TARGET=invalid "$build"
expect_fail env NEXUS_PROFILE=invalid "$build"

headless="$tmp/headless"
env NEXUS_QEMU_BINARY="$fake_qemu" NEXUS_QEMU_MODE=headless     "$runner" "$iso" "$headless" >/dev/null
expect_fail "$recorder" "$headless" pass "must reject headless pass"
"$recorder" "$headless" fail "headless run is not a Wanderer proof" >/dev/null
expect_fail "$recorder" "$headless" fail "must reject duplicate evidence"

interactive="$tmp/interactive"
env NEXUS_QEMU_BINARY="$fake_qemu" NEXUS_QEMU_MODE=interactive     "$runner" "$iso" "$interactive" >/dev/null
"$recorder" "$interactive" pass "synthetic interactive harness test" >/dev/null
grep -q '^RESULT=pass$' "$interactive/wanderer-verification.txt" ||
    fail "interactive pass was not recorded"
grep -q '^RUN_MANIFEST_SHA256=' "$interactive/wanderer-verification.txt" ||
    fail "verification is not bound to the run manifest"

expect_fail env NEXUS_QEMU_BINARY="$fake_qemu"     "$runner" "$iso" "$interactive"

failed="$tmp/qemu-failed"
set +e
FAKE_QEMU_EXIT=42 NEXUS_QEMU_BINARY="$fake_qemu" NEXUS_QEMU_MODE=interactive     "$runner" "$iso" "$failed" >/dev/null 2>&1
rc=$?
set -e
[ "$rc" -eq 42 ] || fail "expected synthetic QEMU exit 42, got $rc"
expect_fail "$recorder" "$failed" pass "must reject failed QEMU run"
"$recorder" "$failed" fail "synthetic QEMU failure" >/dev/null

printf 'nexus-baseline-selftest: PASS\n'
