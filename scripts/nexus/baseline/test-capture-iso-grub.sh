#!/usr/bin/env bash
# Synthetic adversarial tests; do not claim extraction from a real ISO.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
helper="$script_dir/capture-iso-grub.sh"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
mkdir "$tmp/bin"
cat > "$tmp/bin/xorriso" <<'FAKE'
#!/usr/bin/env bash
set -euo pipefail
[ "$#" -eq 7 ] || exit 13
[ "$1" = -osirrox ] && [ "$2" = on ] && [ "$3" = -indev ] &&
[ "$5" = -extract ] && [ "$6" = /boot/grub/grub.cfg ] || exit 14
case "${FAKE_XORRISO_MODE:-valid}" in
    valid) printf 'menuentry "AROS" {\n multiboot2 /boot/pc/bootstrap debug\n}\n' > "$7" ;;
    empty) : > "$7" ;;
    fail) exit 7 ;;
    tamper) printf 'tampered during extraction\n' >> "$4"; printf 'menuentry "AROS" {\n multiboot2 /boot/pc/bootstrap debug\n}\n' > "$7" ;;
    *) exit 8 ;;
esac
FAKE
chmod +x "$tmp/bin/xorriso"
export PATH="$tmp/bin:$PATH"
expect_fail() { if "$@" >/dev/null 2>&1; then echo "FAIL: unexpectedly accepted $*" >&2; exit 1; fi; }
printf 'fake ISO contents\n' > "$tmp/reference.iso"
expect_fail bash "$helper" "$tmp/missing.iso" "$tmp/noiso"
: > "$tmp/empty.iso"
expect_fail bash "$helper" "$tmp/empty.iso" "$tmp/empty-output"
mkdir "$tmp/existing"
expect_fail bash "$helper" "$tmp/reference.iso" "$tmp/existing"
ln -s "$tmp/existing" "$tmp/symlink"
expect_fail bash "$helper" "$tmp/reference.iso" "$tmp/symlink"
expect_fail env FAKE_XORRISO_MODE=fail bash "$helper" "$tmp/reference.iso" "$tmp/failure"
[ -f "$tmp/failure/xorriso.log" ] || { echo 'FAIL: missing extraction log' >&2; exit 1; }
expect_fail env FAKE_XORRISO_MODE=empty bash "$helper" "$tmp/reference.iso" "$tmp/empty-grub"
cp "$tmp/reference.iso" "$tmp/mutable.iso"
expect_fail env FAKE_XORRISO_MODE=tamper bash "$helper" "$tmp/mutable.iso" "$tmp/tamper"
bash "$helper" "$tmp/reference.iso" "$tmp/good" >/dev/null
[ -s "$tmp/good/grub.cfg" ] || exit 1
[ "$(sed -n 's/^ISO_SHA256=//p' "$tmp/good/provenance.txt")" = "$(sha256sum "$tmp/reference.iso" | awk '{print $1}')" ] || exit 1
[ "$(sed -n 's/^GRUB_SHA256=//p' "$tmp/good/provenance.txt")" = "$(sha256sum "$tmp/good/grub.cfg" | awk '{print $1}')" ] || exit 1
grep -qx 'CLAIM=diagnostic-only-not-boot-proof' "$tmp/good/provenance.txt"
expect_fail bash "$helper" "$tmp/reference.iso" "$tmp/good"
printf 'nexus-grub-selftest: PASS (8 negative cases and provenance checks)\n'
