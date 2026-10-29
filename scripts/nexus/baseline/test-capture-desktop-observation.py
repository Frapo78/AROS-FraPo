#!/usr/bin/env python3
"""Negative tests for the optional QEMU desktop observation path."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import subprocess

p = Path(__file__).with_name("capture-desktop-observation.py")
spec = importlib.util.spec_from_file_location("desktop_capture", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "run-manifest.txt").write_text("FORMAT=nexus-qemu-v0\n")
        self.socket = self.root / "monitor.sock"
        self.args = type("Args", (), {"result_dir": str(self.root), "monitor_socket": str(self.socket)})()

    def test_missing_socket_rejected(self):
        with self.assertRaisesRegex(ValueError, "socket unavailable"):
            m.run(self.args)

    def test_missing_manifest_rejected(self):
        (self.root / "run-manifest.txt").unlink()
        with self.assertRaisesRegex(ValueError, "missing run-manifest"):
            m.run(self.args)

    def test_existing_output_rejected(self):
        (self.root / "desktop-observation.ppm").write_bytes(b"old")
        with self.assertRaisesRegex(ValueError, "already exists"):
            m.run(self.args)

    def test_existing_manifest_rejected(self):
        (self.root / "desktop-observation.txt").write_text("old")
        with self.assertRaisesRegex(ValueError, "already exists"):
            m.run(self.args)

    def test_subprocess_not_called_without_socket(self):
        with patch.object(m.subprocess, "run") as runner:
            with self.assertRaises(ValueError):
                m.run(self.args)
            runner.assert_not_called()

    def test_valid_ppm_capture_writes_manifest(self):
        def create_ppm(*_args, **_kwargs):
            (self.root / "desktop-observation.ppm").write_bytes(b"P6\n2 1\n255\n" + b"\xff\x00\x00\x00\xff\x00")
        with patch.object(m.Path, "is_socket", return_value=True), patch.object(m.subprocess, "run", side_effect=create_ppm):
            m.run(self.args)
        proof = (self.root / "desktop-observation.txt").read_text()
        self.assertIn("FORMAT=nexus-desktop-observation-v1\n", proof)
        self.assertIn("WANDERER_VERIFICATION=unverified\n", proof)
        self.assertIn("SCREENSHOT_SHA256=", proof)
        self.assertNotIn("\\n", proof)

    def test_truncated_ppm_is_failure(self):
        def write_truncated(*_args, **_kwargs):
            (self.root / "desktop-observation.ppm").write_bytes(
                b"P6\n2 1\n255\n" + b"\xff\x00\x00\x00\xff")
        with patch.object(m.Path, "is_socket", return_value=True), patch.object(
            m.subprocess, "run", side_effect=write_truncated
        ):
            with self.assertRaisesRegex(ValueError, "payload length mismatch"):
                m.run(self.args)

    def test_extra_ppm_bytes_are_failure(self):
        def write_extra(*_args, **_kwargs):
            (self.root / "desktop-observation.ppm").write_bytes(
                b"P6\n2 1\n255\n" + b"\xff\x00\x00\x00\xff\x00\x00")
        with patch.object(m.Path, "is_socket", return_value=True), patch.object(
            m.subprocess, "run", side_effect=write_extra
        ):
            with self.assertRaisesRegex(ValueError, "payload length mismatch"):
                m.run(self.args)

    def test_invalid_dimensions_are_failure(self):
        def write_bad_size(*_args, **_kwargs):
            (self.root / "desktop-observation.ppm").write_bytes(
                b"P6\n999999999 999999999\n255\n" + b"\x00" * 6)
        with patch.object(m.Path, "is_socket", return_value=True), patch.object(
            m.subprocess, "run", side_effect=write_bad_size
        ):
            with self.assertRaisesRegex(ValueError, "dimensions exceed"):
                m.run(self.args)

    def test_sha_matches(self):
        data = b"abc"
        path = self.root / "data"
        path.write_bytes(data)
        self.assertEqual(m.sha(path), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_missing_screenshot_is_failure(self):
        with patch.object(m.Path, "is_socket", return_value=True), patch.object(m.subprocess, "run", return_value=None):
            with self.assertRaisesRegex(ValueError, "screenshot missing"):
                m.run(self.args)

    def test_malformed_screenshot_is_failure(self):
        def write_bad(*_args, **_kwargs):
            (self.root / "desktop-observation.ppm").write_bytes(b"invalid screenshot bytes")
        with patch.object(m.Path, "is_socket", return_value=True), patch.object(m.subprocess, "run", side_effect=write_bad):
            with self.assertRaisesRegex(ValueError, "invalid canonical P6 header"):
                m.run(self.args)


if __name__ == "__main__":
    unittest.main()
