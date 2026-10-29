#!/usr/bin/env python3
"""Unit tests for bounded observation runner preconditions."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

p = Path(__file__).with_name("run-desktop-observation.py")
spec = importlib.util.spec_from_file_location("desktop_runner", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.iso = self.root / "aros.iso"
        self.iso.write_bytes(b"ISO")
        self.out = self.root / "output"
        (self.root / "build-manifest.txt").write_text(
            "FINAL_STATUS=success\nEXIT_CODE=0\nARTIFACT=" + str(self.iso) +
            "\nARTIFACT_SHA256=" + m.sha(self.iso) +
            "\nSOURCE_SHA=" + "a" * 40 + "\n")

    def reject(self, phrase, seconds=120):
        with self.assertRaisesRegex(ValueError, phrase):
            m.run(self.iso, self.out, seconds)

    def test_symlinked_iso_rejected(self):
        target = self.root / "real.iso"
        self.iso.rename(target)
        self.iso.symlink_to(target)
        self.reject("symlinked ISO")
        self.assertFalse(self.out.exists())

    def test_symlinked_manifest_rejected(self):
        manifest = self.root / "build-manifest.txt"
        target = self.root / "real-manifest.txt"
        manifest.rename(target)
        manifest.symlink_to(target)
        self.reject("symlinked G1 manifest")
        self.assertFalse(self.out.exists())

    def test_missing_iso(self):
        self.iso.unlink()
        self.reject("missing ISO")

    def test_corrupt_iso(self):
        self.iso.write_bytes(b"tampered")
        self.reject("hash or path mismatch")

    def test_failed_build(self):
        path = self.root / "build-manifest.txt"
        path.write_text(path.read_text().replace("FINAL_STATUS=success", "FINAL_STATUS=failed"))
        self.reject("G1 not successful")

    def test_duplicate_manifest(self):
        path = self.root / "build-manifest.txt"
        path.write_text(path.read_text() + "FINAL_STATUS=success\n")
        self.reject("duplicate")

    def test_output_overwrite(self):
        self.out.mkdir()
        self.reject("already exists")

    def test_duration_too_long(self):
        self.reject("duration", 601)

    def test_duration_too_short(self):
        self.reject("duration", 9)

    def test_no_qemu(self):
        with patch.object(m.shutil, "which", return_value=None):
            self.reject("QEMU not installed")

    def test_headless_command_has_no_vnc_listener(self):
        args = m.qemu_command(Path("/usr/bin/qemu-system-x86_64"), self.iso, self.out, False)
        self.assertEqual(args[args.index("-display") + 1], "none")
        self.assertNotIn("-vnc", args)
        self.assertEqual(args[args.index("-nic") + 1], "none")

    def test_interactive_command_is_unix_vnc_only(self):
        args = m.qemu_command(Path("/usr/bin/qemu-system-x86_64"), self.iso, self.out, True)
        self.assertNotIn("-display", args)
        self.assertEqual(args[args.index("-vnc") + 1], "unix:" + str(self.out / "vnc.sock"))
        self.assertEqual(args[args.index("-nic") + 1], "none")
        self.assertNotIn("-netdev", args)
        self.assertNotIn("-websocket", args)

    def test_interactive_cli_is_explicit_opt_in(self):
        with patch.object(m, "run", return_value=0) as runner:
            self.assertEqual(m.main([str(self.iso), str(self.out), "30", "--interactive"]), 0)
            runner.assert_called_once_with(str(self.iso), str(self.out), 30, True)

    def test_default_cli_is_headless(self):
        with patch.object(m, "run", return_value=0) as runner:
            self.assertEqual(m.main([str(self.iso), str(self.out)]), 0)
            runner.assert_called_once_with(str(self.iso), str(self.out), 120, False)

    def test_socket_path_too_long(self):
        self.out = self.root / ("x" * 100)
        self.reject("UNIX socket path too long")
        self.assertFalse(self.out.exists())

    def test_socket_path_byte_limit(self):
        with self.assertRaisesRegex(ValueError, "UNIX socket path too long"):
            m.validate_socket_paths(Path("/tmp") / ("a" * 110), True)

    def test_hmp_unsafe_path_rejected_before_qemu(self):
        self.out = self.root / "space in path"
        self.reject("unsupported HMP characters")
        self.assertFalse(self.out.exists())

    def test_sha(self):
        self.assertEqual(len(m.sha(self.iso)), 64)


if __name__ == "__main__":
    unittest.main()
