#!/usr/bin/env python3
"""Full host-runner integration against a fake UNIX-socket QEMU.

The fake emits synthetic pixels; this proves only runner/capture lifecycle,
never AROS boot or an interactive Wanderer desktop.
"""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

script = Path(__file__).with_name("run-desktop-observation.py")
spec = importlib.util.spec_from_file_location("desktop_runner_integration", script)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

FAKE_QEMU = r'''#!/usr/bin/env python3
import os
from pathlib import Path
import socket
import sys

if "--version" in sys.argv:
    print("QEMU synthetic-host-test 0.1")
    sys.exit(0)
iso = Path(sys.argv[sys.argv.index("-cdrom") + 1])
if (iso.parent / "exit-early").exists():
    sys.exit(7)
monitor = sys.argv[sys.argv.index("-monitor") + 1]
assert monitor.startswith("unix:") and monitor.endswith(",server=on,wait=off")
monitor_path = monitor[5:].split(",", 1)[0]
assert "-nic" in sys.argv and sys.argv[sys.argv.index("-nic") + 1] == "none"
sockets = [socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)]
sockets[0].bind(monitor_path)
sockets[0].listen(1)
if "-vnc" in sys.argv:
    vnc = sys.argv[sys.argv.index("-vnc") + 1]
    assert vnc.startswith("unix:")
    sockets.append(socket.socket(socket.AF_UNIX, socket.SOCK_STREAM))
    sockets[-1].bind(vnc[5:])
    sockets[-1].listen(1)
sockets[0].settimeout(0.2)
while True:
    try:
        conn, _ = sockets[0].accept()
    except socket.timeout:
        continue
    with conn:
        command = conn.recv(4096).decode("ascii").strip()
        if command.startswith("screendump "):
            path = Path(command[len("screendump "):])
            path.write_bytes(b"P6\n2 1\n255\n" + bytes([255, 0, 0, 0, 255, 0]))
'''


class HostIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="nexus-g2c-host-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.iso = self.root / "aros.iso"
        self.iso.write_bytes(b"synthetic ISO, not AROS")
        self.out = self.root / "observation"
        (self.root / "build-manifest.txt").write_text(
            "FINAL_STATUS=success\nEXIT_CODE=0\nARTIFACT=" + str(self.iso) +
            "\nARTIFACT_SHA256=" + runner.sha(self.iso) +
            "\nSOURCE_SHA=" + "a" * 40 + "\n", encoding="utf-8")
        self.fake = self.root / "qemu-system-x86_64"
        self.fake.write_text(FAKE_QEMU, encoding="utf-8")
        self.fake.chmod(0o700)

    def run_fake(self, interactive):
        with patch.object(runner.shutil, "which", return_value=str(self.fake)):
            return runner.run(self.iso, self.out, 10, interactive)

    def test_interactive_host_capture_and_cleanup(self):
        self.assertEqual(self.run_fake(True), 0)
        manifest = (self.out / "run-manifest.txt").read_text()
        observation = (self.out / "desktop-observation.txt").read_text()
        self.assertIn("INTERACTIVE_MODE=unix-vnc\n", manifest)
        self.assertIn("FINAL_STATUS=timeout-unverified\n", manifest)
        self.assertIn("WANDERER_VERIFICATION=unverified\n", observation)
        self.assertEqual((self.out / "desktop-observation.ppm").read_bytes(),
                         b"P6\n2 1\n255\n" + bytes([255, 0, 0, 0, 255, 0]))
        self.assertFalse((self.out / "hmp.sock").exists())
        self.assertFalse((self.out / "vnc.sock").exists())
        self.assertFalse((self.out / "desktop-evidence.txt").exists())
        self.assertEqual(self.out.stat().st_mode & 0o777, 0o700)

    def test_early_guest_exit_cannot_create_capture(self):
        (self.root / "exit-early").write_text("1")
        self.assertEqual(self.run_fake(False), 1)
        self.assertIn("FINAL_STATUS=qemu-exited-unverified\n",
                      (self.out / "run-manifest.txt").read_text())
        self.assertFalse((self.out / "desktop-observation.ppm").exists())
        self.assertFalse((self.out / "desktop-observation.txt").exists())
        self.assertFalse((self.out / "desktop-evidence.txt").exists())


if __name__ == "__main__":
    unittest.main()
