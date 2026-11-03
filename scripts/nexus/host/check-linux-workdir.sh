#!/usr/bin/env bash
# Lightweight Linux filesystem preflight for AROS ports extraction.
# PASS only covers this fixture; it does not prove a complete build or boot.
set -euo pipefail

fail() { printf 'nexus-workdir: ERROR: %s\n' "$*" >&2; exit 1; }

[ "$#" -eq 1 ] || fail 'usage: check-linux-workdir.sh <existing-work-directory>'
[ "$(uname -s)" = Linux ] || fail 'run this inside Linux (e.g. an amd64 Docker container)'
for cmd in stat mktemp tar cmp readlink chmod rm mkdir ln; do
    command -v "$cmd" >/dev/null 2>&1 || fail "missing command: $cmd"
done

work_root="$1"
[ -d "$work_root" ] && [ ! -L "$work_root" ] ||
    fail 'work directory must exist and must not be a symlink'
work_root="$(cd -- "$work_root" && pwd -P)" || fail 'cannot resolve work directory'
fs_type="$(stat -f -c %T -- "$work_root")" || fail 'cannot determine work filesystem'

# Host shares often lack Linux ownership/mode semantics needed by GNU tar.
case "$fs_type" in
    virtiofs|9p|fuse*|smb*|cifs|nfs|nfs4|vboxsf|prl_fs|hgfs)
        fail "filesystem '$fs_type' at $work_root is unsuitable for baseline evidence; mount a Docker named volume at /work"
        ;;
esac

probe="$(mktemp -d "$work_root/.nexus-posix-probe-XXXXXXXX")" ||
    fail 'cannot create probe directory'
trap 'rm -rf -- "$probe"' EXIT

mkdir -p "$probe/seed/mesa-test/.gitlab-ci/bin" \
    "$probe/seed/mesa-test/src/compiler/isaspec" "$probe/unpack"
printf 'mesa-posix-probe\n' > "$probe/seed/mesa-test/.gitlab-ci/bin/check.sh"
printf 'compiler-metadata\n' > "$probe/seed/mesa-test/src/compiler/isaspec/README"
ln -s README "$probe/seed/mesa-test/src/compiler/isaspec/LINK"
chmod 755 "$probe/seed/mesa-test/.gitlab-ci/bin"
chmod 600 "$probe/seed/mesa-test/.gitlab-ci/bin/check.sh"

tar -C "$probe/seed" -cf "$probe/fixture.tar" mesa-test ||
    fail 'failed creating tar fixture'
tar -C "$probe/unpack" -xf "$probe/fixture.tar" ||
    fail 'tar extraction failed on work filesystem'
cmp "$probe/seed/mesa-test/.gitlab-ci/bin/check.sh" \
    "$probe/unpack/mesa-test/.gitlab-ci/bin/check.sh" ||
    fail 'extracted file differs from expected content'
cmp "$probe/seed/mesa-test/src/compiler/isaspec/README" \
    "$probe/unpack/mesa-test/src/compiler/isaspec/README" ||
    fail 'extracted nested file differs from expected content'
[ -L "$probe/unpack/mesa-test/src/compiler/isaspec/LINK" ] ||
    fail 'extracted symlink is missing'
[ "$(readlink "$probe/unpack/mesa-test/src/compiler/isaspec/LINK")" = README ] ||
    fail 'extracted symlink target differs'
chmod 640 "$probe/unpack/mesa-test/.gitlab-ci/bin/check.sh" ||
    fail 'chmod failed after extraction'

printf 'nexus-workdir: PASS filesystem=%s directory=%s (limited POSIX/tar preflight)\n' \
    "$fs_type" "$work_root"
