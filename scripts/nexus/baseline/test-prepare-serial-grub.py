#!/usr/bin/env python3
"""Host-only fail-closed tests for generated BIOS GRUB serial diagnostics."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('prepare-serial-grub.py')
spec = importlib.util.spec_from_file_location('serial_grub', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

BASE = '''if [ "$grub_platform" = "efi" ]; then
    set bl_path="/efi/BOOT/grub"
else
    set bl_path="/boot/grub"
fi
set timeout=5
set default=0
menuentry "AROS64 with native Gfx" {
    multiboot2 /boot/pc/bootstrap.xz ATA=32bit $bootstrap_flags
    module2 /boot/pc/kernel.xz
}
menuentry "other" {
    multiboot2 /boot/pc/bootstrap.xz ATA=32bit $bootstrap_flags
}
'''


class TestGrub(unittest.TestCase):
    def test_default_only_and_idempotent(self):
        data = BASE.encode()
        new = module.transform(data)
        self.assertNotEqual(new, data)
        self.assertEqual(new.count(b'debug=serial'), 1)
        self.assertEqual(new.split(b'menuentry "other"')[1], data.split(b'menuentry "other"')[1])
        self.assertEqual(module.transform(new), new)
        self.assertEqual(module.transform(new, check=True), new)
        with self.assertRaises(ValueError):
            module.transform(data, check=True)

    def test_adversarial(self):
        bad = [
            BASE.replace('set default=0', 'set default=1'),
            BASE.replace('set default=0', 'set default=0\nset default=0'),
            BASE.replace('set default=0', 'set default=$saved_entry'),
            BASE.replace('set default=0', 'set default=0\nload_env saved_entry'),
            BASE.replace('set default=0', 'set default=0\nconfigfile /other.cfg'),
            BASE.replace('set default=0', 'set default=0\nsource /other.cfg'),
            BASE.replace('set default=0', 'set default=0\neval "$cmd"'),
            BASE.replace('set default=0', 'set default=0\nchainloader /boot'),
            BASE.replace('set default=0', 'set default=0\nsubmenu "other" {'),
            BASE.replace('set default=0', 'set default=0; set default=1'),
            BASE.replace('set default=0', 'set default=0\nmenuentry "evil" {\n multiboot2 /bad\n}'),
            BASE.replace('set default=0', 'set default=0\nif false; then'),
            BASE.replace('    module2 /boot/pc/kernel.xz', '    if false; then\n    module2 /boot/pc/kernel.xz'),
            BASE.replace('    module2 /boot/pc/kernel.xz', '    echo bypass\n    module2 /boot/pc/kernel.xz'),
            BASE.replace('    multiboot2 /boot/pc/bootstrap.xz ATA=32bit $bootstrap_flags', '    multiboot2 /boot/pc/bootstrap.xz ATA=32bit $bootstrap_flags extra=unsafe', 1),
            BASE.replace('    module2 /boot/pc/kernel.xz', '    multiboot2 /boot/pc/bootstrap.xz\n    module2 /boot/pc/kernel.xz'),
            BASE.replace('    multiboot2 /boot/pc/bootstrap.xz ATA=32bit $bootstrap_flags', '    multiboot2 /boot/pc/bootstrap.xz ATA=32bit debug=screen', 1),
            BASE.replace('    multiboot2 /boot/pc/bootstrap.xz ATA=32bit $bootstrap_flags', '    multiboot2 /boot/pc/bootstrap.xz ATA=32bit debug=serial debug=serial', 1),
            BASE.replace('    multiboot2 /boot/pc/bootstrap.xz ATA=32bit $bootstrap_flags', '    multiboot2 /boot/pc/bootstrap.xz ATA=32bit debug debug=serial', 1),
            BASE.replace('    multiboot2 /boot/pc/bootstrap.xz ATA=32bit $bootstrap_flags', '    multiboot2 /boot/pc/other.xz ATA=32bit', 1),
            BASE.replace('menuentry "AROS64 with native Gfx"', 'menuentry "AROS64 different"'),
            BASE.replace('set timeout=5', 'set timeout=5\nfunction malicious {'),
            BASE.replace('set timeout=5', 'set timeout=5\ntrue; configfile /evil'),
            BASE.replace('set timeout=5', 'set timeout=5\n`source /evil`'),
            BASE.replace('\n', '\r\n'),
            BASE.rstrip('\n'),
            BASE + '\x00',
            BASE * 15000,
        ]
        for index, item in enumerate(bad):
            with self.subTest(index=index):
                with self.assertRaises((ValueError, UnicodeError)):
                    module.transform(item.encode())

    def test_cli_symlink_and_no_mutation_on_failure(self):
        with tempfile.TemporaryDirectory() as root:
            f = Path(root) / 'grub.cfg'
            f.write_text(BASE)
            link = Path(root) / 'link'
            link.symlink_to(f)
            p = subprocess.run([sys.executable, str(SCRIPT), '--apply', str(link)], capture_output=True)
            self.assertNotEqual(p.returncode, 0)
            self.assertEqual(f.read_text(), BASE)
            f.write_text(BASE.replace('set default=0', 'set default=1'))
            p = subprocess.run([sys.executable, str(SCRIPT), '--apply', str(f)], capture_output=True)
            self.assertNotEqual(p.returncode, 0)
            self.assertEqual(f.read_text(), BASE.replace('set default=0', 'set default=1'))
            f.write_text(BASE)
            p = subprocess.run([sys.executable, str(SCRIPT), '--apply', str(f)], capture_output=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            p = subprocess.run([sys.executable, str(SCRIPT), '--check', str(f)], capture_output=True)
            self.assertEqual(p.returncode, 0, p.stderr)

    def test_actual_g1_fixture_if_available(self):
        fixture = os.getenv('NEXUS_GRUB_REAL_FIXTURE')
        if not fixture:
            self.skipTest('real ISO GRUB fixture not provided (synthetic tests still run)')
        original = Path(fixture).read_bytes()
        modified = module.transform(original)
        self.assertEqual(modified.count(b'debug=serial'), 1)
        self.assertEqual(module.transform(modified, check=True), modified)
        self.assertEqual(module.transform(modified), modified)
        self.assertEqual(original.count(b'debug=serial'), 0)
        old_lines, new_lines = original.splitlines(), modified.splitlines()
        self.assertEqual(len(old_lines), len(new_lines))
        self.assertEqual(sum(a != b for a, b in zip(old_lines, new_lines)), 1)


if __name__ == '__main__':
    unittest.main()
