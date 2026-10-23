#!/usr/bin/env bash
# Capture the BIOS GRUB configuration embedded in the exact supplied ISO.
# Diagnostic evidence only: no GRUB selection, serial marker or boot claim.
set -euo pipefail

die() { printf 'nexus-grub: ERROR: %s\n' "$*" >&2; exit 1; }

[ "$#" -eq 2 ] || die 'usage: capture-iso-grub.sh <iso> <new-evidence-directory>'
iso="$1"
evidence_dir="$2"
[ -f "$iso" ] && [ -s "$iso" ] || die 'ISO missing or empty'
[ ! -e "$evidence_dir" ] && [ ! -L "$evidence_dir" ] || die 'evidence destination already exists'
command -v xorriso >/dev/null 2>&1 || die 'xorriso unavailable'
command -v sha256sum >/dev/null 2>&1 || die 'sha256sum unavailable'
mkdir -- "$evidence_dir" || die 'cannot create evidence directory'

if ! xorriso -osirrox on -indev "$iso" \
    -extract /boot/grub/grub.cfg "$evidence_dir/grub.cfg" \
    > "$evidence_dir/xorriso.log" 2>&1; then
    die 'BIOS GRUB extraction failed (see xorriso.log)'
fi
[ -s "$evidence_dir/grub.cfg" ] || die 'extracted BIOS GRUB configuration is empty'

{
    printf 'FORMAT=nexus-grub-diagnostic-v1\n'
    printf 'ISO_SHA256=%s\n' "$(sha256sum "$iso" | awk '{print $1}')"
    printf 'GRUB_PATH=/boot/grub/grub.cfg\n'
    printf 'GRUB_SHA256=%s\n' "$(sha256sum "$evidence_dir/grub.cfg" | awk '{print $1}')"
    printf 'CLAIM=diagnostic-only-not-boot-proof\n'
} > "$evidence_dir/provenance.txt"
printf 'nexus-grub: captured BIOS GRUB diagnostic evidence\n'
