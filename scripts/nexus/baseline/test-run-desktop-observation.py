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

    def test_sha(self):
        self.assertEqual(len(m.sha(self.iso)), 64)


if __name__ == "__main__":
    unittest.main()
