#!/usr/bin/env bash
# Focused positive and adversarial negative tests for Linux workdir preflight.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "$0")" && pwd -P)"
check="$script_dir/check-linux-workdir.sh"
scratch="$(mktemp -d)"
trap 'rm -rf -- "$scratch"' EXIT
mkdir -p "$scratch/work" "$scratch/fakebin"

pass() { printf 'PASS: %s\n' "$1"; }
expect_reject() {
    local label="$1"
    shift
    if "$@" > "$scratch/out" 2>&1; then
        printf 'FAIL: unexpectedly accepted %s\n' "$label" >&2
        exit 1
    fi
    pass "$label"
}

bash "$check" "$scratch/work" > "$scratch/out"
grep -q 'nexus-workdir: PASS' "$scratch/out"
pass 'native workdir with tar, symlink, chmod and nested-file checks'

expect_reject 'nonexistent workdir' bash "$check" "$scratch/missing"
expect_reject 'extra argument' bash "$check" "$scratch/work" extra

cat > "$scratch/fakebin/stat" <<'FAKE_STAT'
#!/usr/bin/env bash
printf '%s\n' virtiofs
FAKE_STAT
chmod +x "$scratch/fakebin/stat"
expect_reject 'virtiofs mount' env PATH="$scratch/fakebin:$PATH" \
    bash "$check" "$scratch/work"
grep -q 'Docker named volume' "$scratch/out"
rm "$scratch/fakebin/stat"

cat > "$scratch/fakebin/tar" <<'FAKE_TAR'
#!/usr/bin/env bash
exit 42
FAKE_TAR
chmod +x "$scratch/fakebin/tar"
expect_reject 'tar creation error' env PATH="$scratch/fakebin:$PATH" \
    bash "$check" "$scratch/work"
grep -q 'failed creating tar fixture' "$scratch/out"

cat > "$scratch/fakebin/tar" <<'FAKE_EXTRACT'
#!/usr/bin/env bash
for arg in "$@"; do
    if [ "$arg" = -xf ]; then exit 43; fi
done
exec "$NEXUS_REAL_TAR" "$@"
FAKE_EXTRACT
chmod +x "$scratch/fakebin/tar"
expect_reject 'tar extraction error' env NEXUS_REAL_TAR="$(command -v tar)" \
    PATH="$scratch/fakebin:$PATH" bash "$check" "$scratch/work"
grep -q 'tar extraction failed' "$scratch/out"

if find "$scratch/work" -maxdepth 1 -name '.nexus-posix-probe-*' | grep -q .; then
    echo 'FAIL: leaked temporary probe files' >&2
    exit 1
fi
pass 'temporary files cleaned after success and failure'
