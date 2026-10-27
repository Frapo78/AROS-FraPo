#!/usr/bin/env python3
"""Host-only positive and adversarial tests for bound G2c evidence."""
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
        self.observation = self.root / "desktop-observation.txt"
        self.proof = self.root / "desktop-evidence.txt"
        self.screen = self.root / "desktop-observation.ppm"
        self.screen.write_bytes(b"P6\n2 1\n255\n" + b"\xff\x00\x00\x00\xff\x00")
        self.run.write_text(
            "FORMAT=nexus-qemu-v0\nSOURCE_SHA=" + "a" * 40 +
            "\nISO_SHA256=" + "b" * 64 +
            "\nQEMU_SHA256=" + "c" * 64 +
            "\nQEMU_VERSION=QEMU test\nINTERACTIVE_MODE=unix-vnc\nFINAL_STATUS=timeout-unverified\n")
        self.refresh()

    def refresh(self):
        run_sha = sha(self.run.read_bytes())
        screen_sha = sha(self.screen.read_bytes())
        self.observation.write_text(
            "FORMAT=nexus-desktop-observation-v1\n"
            "CAPTURED_UTC=2026-10-25T09:59:00Z\n"
            "RUN_MANIFEST_SHA256=" + run_sha +
            "\nSCREENSHOT=desktop-observation.ppm\n"
            "SCREENSHOT_SHA256=" + screen_sha +
            "\nWANDERER_VERIFICATION=unverified\n")
        self.proof.write_text(
            "FORMAT=nexus-desktop-evidence-v1\n"
            "RUN_MANIFEST_SHA256=" + run_sha +
            "\nSOURCE_SHA=" + "a" * 40 +
            "\nISO_SHA256=" + "b" * 64 +
            "\nVISUAL_RESULT=wanderer-usable\n"
            "HUMAN_VERIFIED=yes\nREVIEWER=human-reviewer\n"
            "REVIEWED_UTC=2026-10-25T10:00:00Z\n"
            "SCREENSHOT=desktop-observation.ppm\n"
            "SCREENSHOT_SHA256=" + screen_sha + "\n")

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
        self.run.write_text(self.run.read_text() + "SOURCE_SHA=" + "a" * 40 + "\n")
        self.refresh()
        self.reject()

    def test_headless_run_cannot_claim_usable_wanderer(self):
        self.run.write_text(self.run.read_text().replace(
            "INTERACTIVE_MODE=unix-vnc", "INTERACTIVE_MODE=none"))
        self.refresh()
        self.reject()

    def test_missing_interactive_mode_rejected(self):
        self.run.write_text(self.run.read_text().replace(
            "INTERACTIVE_MODE=unix-vnc\n", ""))
        self.refresh()
        self.reject()

    def test_unknown_interactive_mode_rejected(self):
        self.run.write_text(self.run.read_text().replace(
            "INTERACTIVE_MODE=unix-vnc", "INTERACTIVE_MODE=tcp-vnc"))
        self.refresh()
        self.reject()

    def test_early_guest_exit_rejected(self):
        self.run.write_text(self.run.read_text().replace(
            "timeout-unverified", "qemu-exited-unverified"))
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
        self.proof.write_text(self.proof.read_text().replace(
            "SCREENSHOT=desktop-observation.ppm", "SCREENSHOT=../desktop-observation.ppm"))
        self.reject()

    def test_bad_ppm(self):
        self.screen.write_bytes(b"not a ppm screenshot")
        self.refresh()
        self.reject()

    def test_missing_provenance(self):
        self.run.write_text(self.run.read_text().replace("QEMU_VERSION=QEMU test\n", ""))
        self.refresh()
        self.reject()

    def test_missing_capture_observation(self):
        self.observation.unlink()
        self.reject()

    def test_unbound_capture_run(self):
        self.observation.write_text(self.observation.read_text().replace(
            "RUN_MANIFEST_SHA256=", "RUN_MANIFEST_SHA256=0"))
        self.reject()

    def test_unbound_capture_screenshot(self):
        self.observation.write_text(self.observation.read_text().replace(
            "SCREENSHOT_SHA256=", "SCREENSHOT_SHA256=0"))
        self.reject()

    def test_rehashed_truncated_ppm(self):
        self.screen.write_bytes(self.screen.read_bytes()[:-1])
        self.refresh()
        self.reject()

    def test_rehashed_extra_pixels(self):
        self.screen.write_bytes(self.screen.read_bytes() + b"\x00")
        self.refresh()
        self.reject()

    def test_capture_review_order(self):
        self.proof.write_text(self.proof.read_text().replace(
            "REVIEWED_UTC=2026-10-25T10:00:00Z", "REVIEWED_UTC=2026-10-25T09:58:00Z"))
        self.reject()

    def test_symlinked_screenshot(self):
        original = self.root / "other.ppm"
        self.screen.rename(original)
        self.screen.symlink_to(original)
        self.reject()

    def test_invalid_captured_date(self):
        self.observation.write_text(self.observation.read_text().replace(
            "CAPTURED_UTC=2026-10-25", "CAPTURED_UTC=2026-99-25"))
        self.reject()

    def test_capture_must_not_claim_verified(self):
        self.observation.write_text(self.observation.read_text().replace(
            "WANDERER_VERIFICATION=unverified", "WANDERER_VERIFICATION=verified"))
        self.reject()

    def test_capture_filename_mismatch(self):
        self.observation.write_text(self.observation.read_text().replace(
            "SCREENSHOT=desktop-observation.ppm", "SCREENSHOT=other.ppm"))
        self.reject()

    def test_noncanonical_ppm(self):
        self.screen.write_bytes(self.screen.read_bytes().replace(b"2 1\n", b"2\t1\n"))
        self.refresh()
        self.reject()


if __name__ == "__main__":
    unittest.main()
