#!/usr/bin/env python3
"""Host-only positive and adversarial tests for G2c evidence."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

script = Path(__file__).with_name("verify-desktop-evidence.py")
spec = importlib.util.spec_from_file_location("desktop_verifier", script)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def sha(data):
    return hashlib.sha256(data).hexdigest()


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.run = self.root / "run-manifest.txt"
        self.proof = self.root / "desktop-evidence.txt"
        self.screen = self.root / "screen.ppm"
        self.screen.write_bytes(b"P6\n2 1\n255\n" + b"\xff\x00\x00\x00\xff\x00")
        self.run.write_text("SOURCE_SHA=" + "a"*40 + "\nISO_SHA256=" + "b"*64 + "\nQEMU_SHA256=" + "c"*64 + "\nQEMU_VERSION=QEMU test\nFINAL_STATUS=timeout-unverified\n")
        self.refresh()

    def refresh(self):
        self.proof.write_text("FORMAT=nexus-desktop-evidence-v1\nRUN_MANIFEST_SHA256=" + sha(self.run.read_bytes()) + "\nSOURCE_SHA=" + "a"*40 + "\nISO_SHA256=" + "b"*64 + "\nVISUAL_RESULT=wanderer-usable\nHUMAN_VERIFIED=yes\nREVIEWER=human-reviewer\nREVIEWED_UTC=2026-10-25T10:00:00Z\nSCREENSHOT=screen.ppm\nSCREENSHOT_SHA256=" + sha(self.screen.read_bytes()) + "\n")

    def reject(self):
        with self.assertRaises((ValueError, OSError)):
            module.verify(self.root)

    def test_valid_package(self):
        self.assertTrue(module.verify(self.root))

    def test_tampered_screenshot(self):
        self.screen.write_bytes(self.screen.read_bytes() + b"X")
        self.reject()

    def test_tampered_manifest(self):
        self.run.write_text(self.run.read_text() + "UNTRUSTED=yes\n")
        self.reject()

    def test_duplicate_manifest_key(self):
        self.run.write_text(self.run.read_text() + "SOURCE_SHA=" + "a"*40 + "\n")
        self.refresh()
        self.reject()

    def test_g2a_is_not_g2c(self):
        self.run.write_text(self.run.read_text().replace("timeout-unverified", "marker-reached"))
        self.refresh()
        self.reject()

    def test_no_human_review(self):
        self.proof.write_text(self.proof.read_text().replace("HUMAN_VERIFIED=yes", "HUMAN_VERIFIED=no"))
        self.reject()

    def test_path_traversal(self):
        self.proof.write_text(self.proof.read_text().replace("SCREENSHOT=screen.ppm", "SCREENSHOT=../screen.ppm"))
        self.reject()

    def test_bad_ppm(self):
        self.screen.write_bytes(b"not a ppm screenshot")
        self.refresh()
        self.reject()

    def test_missing_provenance(self):
        self.run.write_text(self.run.read_text().replace("QEMU_VERSION=QEMU test\n", ""))
        self.refresh()
        self.reject()


if __name__ == "__main__":
    unittest.main()
