#!/usr/bin/env python3
"""Bounded x86-64 QEMU observation, optionally interactive over local UNIX VNC.

This host diagnostic does not independently prove that Wanderer is usable.
A human must operate the same guest and review the captured framebuffer.
"""
import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time


def sha(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fields(path):
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" not in line:
            raise ValueError("invalid manifest line")
        key, val = line.split("=", 1)
        if key in result:
            raise ValueError("duplicate manifest key")
        result[key] = val
    return result


def validate_socket_paths(out, interactive):
    # The HMP screenshot helper intentionally rejects spaces and command
    # separators; reject incompatible result paths before starting QEMU.
    if not re.fullmatch(r"[/A-Za-z0-9_.-]+", str(out / "desktop-observation.ppm")):
        raise ValueError("output path contains unsupported HMP characters")
    # Linux sun_path is typically 108 bytes, macOS often shorter. Fail early
    # rather than silently starting a guest without an accessible console.
    paths = [out / "hmp.sock"]
    if interactive:
        paths.append(out / "vnc.sock")
    if any(len(os.fsencode(str(path))) > 100 for path in paths):
        raise ValueError("UNIX socket path too long (max 100 bytes)")


def qemu_command(qemu, iso, out, interactive):
    monitor = out / "hmp.sock"
    args = [str(qemu), "-machine", "pc", "-accel", "tcg,thread=single",
            "-cpu", "qemu64", "-smp", "1", "-m", "1024",
            "-boot", "order=d,menu=off", "-cdrom", str(iso),
            "-nic", "none", "-serial", "file:" + str(out / "serial.log"),
            "-monitor", "unix:" + str(monitor) + ",server=on,wait=off",
            "-no-reboot"]
    if interactive:
        # No TCP/WebSocket listener. The directory is created mode 0700.
        args += ["-vnc", "unix:" + str(out / "vnc.sock")]
    else:
        args += ["-display", "none"]
    return args


def run(iso, out, seconds=120, interactive=False):
    iso, out = Path(iso).resolve(), Path(out).resolve()
    if not iso.is_file() or not iso.stat().st_size:
        raise ValueError("missing ISO")
    build = iso.parent / "build-manifest.txt"
    data = fields(build)
    if data.get("FINAL_STATUS") != "success" or data.get("EXIT_CODE") != "0":
        raise ValueError("G1 not successful")
    initial_iso_sha = sha(iso)
    initial_build_sha = sha(build)
    if data.get("ARTIFACT") != str(iso) or data.get("ARTIFACT_SHA256") != initial_iso_sha:
        raise ValueError("G1 artifact hash or path mismatch")
    if not re.fullmatch(r"[0-9a-f]{40}", data.get("SOURCE_SHA", "")):
        raise ValueError("invalid source SHA")
    if out.exists():
        raise ValueError("output already exists")
    if not 10 <= seconds <= 600:
        raise ValueError("duration must be 10..600 seconds")
    validate_socket_paths(out, interactive)
    qemu = shutil.which("qemu-system-x86_64")
    if not qemu:
        raise ValueError("QEMU not installed")
    qemu = Path(qemu).resolve()
    out.mkdir(parents=True, mode=0o700)
    sock = out / "hmp.sock"
    vnc = out / "vnc.sock"
    screen = out / "desktop-observation.ppm"
    manifest = out / "run-manifest.txt"
    args = qemu_command(qemu, iso, out, interactive)
    proc = None
    try:
        proc = subprocess.Popen(args, stdin=subprocess.DEVNULL)
        if interactive:
            print("Local VNC socket:", vnc, flush=True)
            print("Connect a UNIX-socket-capable VNC viewer now; interact before the timeout.", flush=True)
        deadline = time.monotonic() + seconds
        while proc.poll() is None and time.monotonic() < deadline:
            time.sleep(min(1, max(0, deadline - time.monotonic())))
        final_iso_sha = sha(iso)
        iso_changed = final_iso_sha != initial_iso_sha
        status = ("iso-changed-unverified" if iso_changed else
                  "qemu-exited-unverified" if proc.poll() is not None else
                  "timeout-unverified")
        manifest.write_text(
            "FORMAT=nexus-qemu-v0\nSOURCE_SHA=" + data["SOURCE_SHA"] +
            "\nISO_SHA256=" + initial_iso_sha +
            "\nISO_SHA256_AFTER=" + final_iso_sha +
            "\nQEMU_SHA256=" + sha(qemu) +
            "\nQEMU_VERSION=" + subprocess.check_output([str(qemu), "--version"], text=True, timeout=10).splitlines()[0] +
            "\nINTERACTIVE_MODE=" + ("unix-vnc" if interactive else "none") +
            "\nFINAL_STATUS=" + status + "\n", encoding="utf-8")
        # A guest that read a different ISO invalidates the G1 binding.
        # Preserve the failed run manifest but never create desktop evidence.
        if iso_changed:
            return 1
        if interactive and not vnc.is_socket():
            raise ValueError("local VNC socket unavailable; no interactive evidence")
        if proc.poll() is None and sock.is_socket():
            subprocess.run([sys.executable, str(Path(__file__).with_name("capture-desktop-observation.py")), str(out), str(sock)],
                           check=True, timeout=30)
        # Recheck after the capture: QEMU can still read the ISO during HMP.
        # Never retain positive-looking evidence from a changed artifact or G1 manifest.
        if sha(iso) != initial_iso_sha or sha(build) != initial_build_sha:
            screen.unlink(missing_ok=True)
            (out / "desktop-observation.txt").unlink(missing_ok=True)
            with manifest.open("a", encoding="utf-8") as stream:
                stream.write("POST_CAPTURE_PROVENANCE=changed\n")
            return 1
        return 0 if screen.is_file() else 1
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
        sock.unlink(missing_ok=True)
        vnc.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("iso")
    parser.add_argument("result_directory")
    parser.add_argument("seconds", nargs="?", type=int, default=120)
    parser.add_argument("--interactive", action="store_true",
                        help="enable local UNIX VNC only (no TCP listener)")
    args = parser.parse_args(argv)
    try:
        return run(args.iso, args.result_directory, args.seconds, args.interactive)
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print("desktop observation failed:", exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
