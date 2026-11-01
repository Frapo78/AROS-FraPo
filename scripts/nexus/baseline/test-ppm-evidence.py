#!/usr/bin/env python3
"""Adversarial tests for canonical QEMU P6 framebuffer evidence."""
import unittest

from ppm_evidence import MAX_PPM_BYTES, validate_ppm_bytes


class PPMTests(unittest.TestCase):
    def setUp(self):
        self.header = b"P6\n2 1\n255\n"
        self.pixels = b"\xff\x00\x00\x00\xff\x00"

    def reject(self, data):
        with self.assertRaises(ValueError):
            validate_ppm_bytes(data)

    def test_valid(self):
        self.assertEqual(validate_ppm_bytes(self.header + self.pixels), (2, 1))

    def test_first_pixel_is_newline(self):
        self.assertEqual(validate_ppm_bytes(self.header + b"\n" + self.pixels[1:]), (2, 1))

    def test_truncated_payload(self):
        self.reject(self.header + self.pixels[:-1])

    def test_appended_payload(self):
        self.reject(self.header + self.pixels + b"\x00")

    def test_zero_dimension(self):
        self.reject(b"P6\n0 1\n255\n" + self.pixels)

    def test_huge_dimensions(self):
        self.reject(b"P6\n999999999999 999999999999\n255\n" + self.pixels)

    def test_noncanonical_header(self):
        self.reject(b"P6\n2\t1\n255\n" + self.pixels)

    def test_header_comment(self):
        self.reject(b"P6\n#not QEMU canonical\n2 1\n255\n" + self.pixels)

    def test_oversized_bytes(self):
        self.reject(b"x" * (MAX_PPM_BYTES + 1))

    def test_missing_header(self):
        self.reject(self.pixels)


if __name__ == "__main__":
    unittest.main()
