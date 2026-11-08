#!/usr/bin/env python3
"""Adversarial host tests for the narrow source-backed AROS PAT audit."""
from __future__ import annotations

import unittest

from audit_upstream_pat import audit_sources, cache_bits, pat_index

MAP = '''
static void set_pde_2m(struct PDE2M *entry, IPTR phys, KRN_MapAttr flags)
{
    struct PDE2M tmp = { 0 };
    tmp.p = (flags & (MAP_Readable | MAP_Writable | MAP_Executable)) ? 1 : 0;
    tmp.us = 1;
    if (flags & MAP_WriteCombine)
        tmp.pat = 1;
    else
    {
        tmp.pwt = (flags & MAP_WriteThrough) ? 1 : 0;
        tmp.pcd = (flags & MAP_CacheInhibit) ? 1 : 0;
    }
    tmp.ps = 1;
}
static void set_pte(struct PTE *entry, IPTR phys, KRN_MapAttr flags)
{
    struct PTE tmp = { 0 };
    tmp.p = (flags & (MAP_Readable | MAP_Writable | MAP_Executable)) ? 1 : 0;
    tmp.us = 1;
    if (flags & MAP_WriteCombine)
        tmp.pat = 1;
    else
    {
        tmp.pwt = (flags & MAP_WriteThrough) ? 1 : 0;
        tmp.pcd = (flags & MAP_CacheInhibit) ? 1 : 0;
    }
}
'''
CPU = '''
void core_CPUSetup(apicid_t cpuNo, APTR cpuGDT, IPTR SystemStack) {
if (cpuid_edx & (1 << 16)) {
    ULONG lo = 0x00070406UL;
    ULONG hi = 0x00070401UL;
    asm volatile ("wrmsr" :: "c"(0x277), "a"(lo), "d"(hi));
}
}
'''
FLAGS = '''typedef enum { MAP_WriteCombine = 0x0008, } KRN_MapAttr;'''


class PatAuditTests(unittest.TestCase):
    def test_source_patterns_pass(self):
        self.assertTrue(audit_sources(MAP, CPU, FLAGS)['passed'])

    def test_oracle_exhaustive_low_flags(self):
        expected = [0, 2, 1, 3, 0, 2, 1, 3] + [4] * 8
        self.assertEqual([pat_index(i) for i in range(16)], expected)
        self.assertEqual(cache_bits(0x0008 | 0x0001), (1, 0, 0))
        self.assertEqual(cache_bits(0x0008 | 0x0002), (1, 0, 0))

    def test_single_mutations_rejected(self):
        mutants = [
            ('flag collision', MAP, CPU, FLAGS.replace('0x0008', '0x0004')),
            ('missing PAT CPU guard', MAP, CPU.replace('1 << 16', '1 << 17'), FLAGS),
            ('different PAT high dword', MAP, CPU.replace('0x00070401UL', '0x00070406UL'), FLAGS),
            ('different PAT low dword', MAP, CPU.replace('0x00070406UL', '0x00070401UL'), FLAGS),
            ('different MSR', MAP, CPU.replace('0x277', '0x276'), FLAGS),
            ('unguarded wrmsr', MAP, CPU.replace('    asm volatile ("wrmsr" :: "c"(0x277), "a"(lo), "d"(hi));', '').replace('}\n}\n', '}\n    asm volatile ("wrmsr" :: "c"(0x277), "a"(lo), "d"(hi));\n}\n'), FLAGS),
            ('no PDE PAT', MAP.replace('tmp.pat = 1;', 'tmp.pat = 0;', 1), CPU, FLAGS),
            ('no PTE PAT', MAP.rsplit('tmp.pat = 1;', 1)[0] + 'tmp.pat = 0;' + MAP.rsplit('tmp.pat = 1;', 1)[1], CPU, FLAGS),
            ('WC/CI reversed precedence', MAP.replace('if (flags & MAP_WriteCombine)', 'if (flags & MAP_CacheInhibit)', 1), CPU, FLAGS),
            ('no legacy PCD', MAP.replace('tmp.pcd = (flags & MAP_CacheInhibit) ? 1 : 0;', 'tmp.pcd = 0;', 1), CPU, FLAGS),
            ('no large-page PS', MAP.replace('tmp.ps = 1;', 'tmp.ps = 0;', 1), CPU, FLAGS),
            ('missing supervisor assumption', MAP.replace('tmp.us = 1;', 'tmp.us = 0;', 1), CPU, FLAGS),
        ]
        for label, mapping, cpu, flags in mutants:
            with self.subTest(label=label):
                self.assertFalse(audit_sources(mapping, cpu, flags)['passed'], label)

    def test_ignored_comment_forgery(self):
        mutation = MAP.replace('tmp.pat = 1;', '/* tmp.pat = 1; */ tmp.pat = 0;', 1)
        self.assertFalse(audit_sources(mutation, CPU, FLAGS)['passed'])

    def test_duplicate_function_rejected(self):
        self.assertFalse(audit_sources(MAP + MAP, CPU, FLAGS)['passed'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
