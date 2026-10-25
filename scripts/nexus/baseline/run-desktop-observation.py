#!/usr/bin/env python3
"""Opt-in, bounded x86-64 QEMU desktop observation (not a G2c PASS).

Usage: python3 run-desktop-observation.py ISO RESULT_DIR [seconds]
Requires QEMU and a successful G1 build-manifest.txt alongside ISO.
"""
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fields(path):
    result = {}
    for line in path.read_text().splitlines():
        if "=" not in line:
            raise ValueError("invalid manifest line")
        key, val = line.split("=", 1)
        if key in result:
            raise ValueError("duplicate manifest key")
        result[key] = val
    return result


def run(iso, out, seconds=120):
    iso, out = Path(iso).resolve(), Path(out).resolve()
    if not iso.is_file() or not iso.stat().st_size:
        raise ValueError("missing ISO")
    build = iso.parent / "build-manifest.txt"
    data = fields(build)
    if data.get("FINAL_STATUS") != "success" or data.get("EXIT_CODE") != "0":
        raise ValueError("G1 not successful")
    if data.get("ARTIFACT") != str(iso) or data.get("ARTIFACT_SHA256") != sha(iso):
        raise ValueError("G1 artifact hash or path mismatch")
    if not re.fullmatch(r"[0-9a-f]{40}", data.get("SOURCE_SHA", "")):
        raise ValueError("invalid source SHA")
    if out.exists():
        raise ValueError("output already exists")
    if not 10 <= seconds <= 600:
        raise ValueError("duration must be 10..600 seconds")
    qemu = shutil.which("qemu-system-x86_64")
    if not qemu:
        raise ValueError("QEMU not installed")
    qemu = Path(qemu).resolve()
    out.mkdir(parents=True)
    sock = out / "hmp.sock"
    screen = out / "desktop-observation.ppm"
    log = out / "serial.log"
    manifest = out / "run-manifest.txt"
    args = [str(qemu), "-machine", "pc", "-accel", "tcg,thread=single",
            "-cpu", "qemu64", "-smp", "1", "-m", "1024",
            "-boot", "order=d,menu=off", "-cdrom", str(iso),
            "-nic", "none", "-display", "none", "-serial", "file:" + str(log),
            "-monitor", "unix:" + str(sock) + ",server=on,wait=off", "-no-reboot"]
    proc = None
    try:
        proc = subprocess.Popen(args, stdin=subprocess.DEVNULL)
        time.sleep(seconds)
        if proc.poll() is not None:
            status = "qemu-exited-unverified"
        else:
            status = "timeout-unverified"
        manifest.write_text(
            "FORMAT=nexus-qemu-v0\nSOURCE_SHA=" + data["SOURCE_SHA"] +
            "\nISO_SHA256=" + sha(iso) +
            "\nQEMU_SHA256=" + sha(qemu) +
            "\nQEMU_VERSION=" + subprocess.check_output([str(qemu), "--version"], text=True).splitlines()[0] +
            "\nFINAL_STATUS=" + status + "\n")
        if proc.poll() is None and sock.is_socket():
            subprocess.run([sys.executable, str(Path(__file__).with_name("capture-desktop-observation.py")), str(out), str(sock)],
                           check=True, timeout=30)
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


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        sys.exit("usage: run-desktop-observation.py ISO RESULT_DIR [seconds]")
    try:
        sys.exit(run(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) == 4 else 120))
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        sys.exit("desktop observation failed: " + str(exc))
