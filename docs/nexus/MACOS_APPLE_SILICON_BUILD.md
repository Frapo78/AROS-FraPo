# Apple Silicon macOS — local x86-64 diagnostic build

> Experimental Phase 0 recipe for PR #37 (`nexus/qemu-smoke-clean-20261101`).
> A successful host preflight does not prove G1/G2a, Wanderer, or any isolation level.

## Failure and scope

A local AMD64 Ubuntu build on Apple Silicon can fail during GNU tar extraction of Mesa
when `/work` is a macOS Docker bind mount (`Permission denied`, `Function not implemented`).
Run the build on a **Docker named volume** instead. Keep source bind-mounted read-only
and copy only a verified ISO to the macOS export directory.

Upstream AROS / Mesa remain unchanged (U); no adapted code (A). This optional
filesystem preflight is Nexus-owned host tooling (N), with no B0-B3 bridge and no
runtime trust-authority change. The tested baseline stays pinned in [BASELINE.md](BASELINE.md).

## On macOS

Commands below assume Homebrew and Colima; an existing working Docker engine is also valid.

```bash
brew install git docker colima qemu
colima status || colima start --cpu 4 --memory 8 --disk 100
docker info
mkdir -p /Users/fra/APPS/NEXUS/ISO
cd /Users/fra/APPS/NEXUS
git clone --branch nexus/qemu-smoke-clean-20261101 --recurse-submodules \
    https://github.com/Frapo78/AROS-FraPo.git AROS-FraPo
docker volume create nexus-build-work
```

If the clone already exists, inspect it and use `git fetch` rather than overwriting.
If the container name is already used, restart it with `docker start -ai nexus-builder`.

```bash
docker run -it --name nexus-builder --platform linux/amd64 \
    -v /Users/fra/APPS/NEXUS/AROS-FraPo:/src:ro \
    -v nexus-build-work:/work \
    -v /Users/fra/APPS/NEXUS/ISO:/export \
    ubuntu:24.04 bash
```

## Inside Ubuntu

```bash
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y \
    git build-essential gcc g++ curl ca-certificates \
    libpng-dev zlib1g-dev libxcursor-dev libgl1-mesa-dev libasound2-dev \
    gawk bison flex netpbm automake cmake genisoimage \
    python3 python3-mako python3-yaml python3-distutils-extra \
    libswitch-perl gperf gcc-multilib ccache libclang-dev \
    jlha-utils wget liblzma-dev libelf-dev mtools xorriso nasm \
    qemu-system-x86
git config --global --add safe.directory /src
cd /src
git status --short
stat -f -c %T /work
bash scripts/nexus/host/check-linux-workdir.sh /work
```

The preflight must print `nexus-workdir: PASS`. It checks a small TAR extraction,
nested files, symlinks and chmod, and rejects known shared filesystem types.
**It is not a complete Mesa unpack test**; a PASS does not guarantee the build.
Do not bypass a failure to obtain apparently successful baseline evidence.

```bash
export BUILDTHREADS=2
export NEXUS_PROFILE=diagnostic
export NEXUS_WORK_ROOT=/work
set -o pipefail
bash scripts/nexus/baseline/build-x86_64.sh 2>&1 | tee /work/build.log
```

The baseline builder creates a fresh toolchain and work tree per attempt. Keep
sufficient VM disk space. Do not promote partial output from an earlier failed
macOS-bind-mount build to a tested baseline.

## Export only after successful G1 compilation

```bash
mapfile -t isos < <(find /work/runs -type f -path '*/artifacts/aros-pc-x86_64.iso')
test "${#isos[@]}" -eq 1 || { echo 'Expected exactly one ISO'; exit 1; }
iso="${isos[0]}"
manifest="$(dirname "$iso")/build-manifest.txt"
grep -qx 'FINAL_STATUS=success' "$manifest"
grep -qx 'EXIT_CODE=0' "$manifest"
expected="$(sed -n 's/^ARTIFACT_SHA256=//p' "$manifest")"
actual="$(sha256sum "$iso" | cut -d ' ' -f1)"
test -n "$expected" && test "$expected" = "$actual"
cp "$iso" /export/aros-pc-x86_64.iso
cp "$manifest" /export/build-manifest.txt
test "$(sha256sum /export/aros-pc-x86_64.iso | cut -d ' ' -f1)" = "$actual"
```

Once outside the container, QEMU on macOS can inspect the copied ISO:

```bash
qemu-system-x86_64 -machine pc -accel tcg,thread=single \
    -cpu qemu64 -smp 1 -m 1024 -boot order=d \
    -cdrom /Users/fra/APPS/NEXUS/ISO/aros-pc-x86_64.iso \
    -nic none -serial file:/Users/fra/APPS/NEXUS/ISO/serial.log -no-reboot
```

The expected early serial banner is `AROS64 - The AROS Research OS`.
A manual observation is not portable E4 evidence until source SHA, exact ISO
hash, build/run manifests, QEMU arguments and bounded verdict are retained.
Copying the ISO does not authorize rewriting its original build manifest.
Desktop/Wanderer usability needs separate G2b/G2c guest and human evidence.

## Verification and stop rules

- H0: host tooling only; no L0-L5 claim.
- E2: host tests for working Linux filesystem, simulated `virtiofs`, forced TAR
  creation and extraction failure, invalid arguments, and probe cleanup.
- E4: not provided by this preflight; run an actual SHA-bound G2a QEMU test.
- Stop if the filesystem probe, build manifest, hashes, or QEMU marker fails.
- Docker named volumes are VM-owned. Export artifacts before deleting volumes.
