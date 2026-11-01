/* Host-only adversarial tests for the Nexus Phase 0 mapping-rights prototype. */
#include <stdint.h>
#include <stdio.h>
#include "../mapping_rights.h"

static enum nexus_mapping_status expected(uint32_t rights, int nx)
{
    if (nx != 0 && nx != 1)
        return NEXUS_MAP_INVALID;
    if ((rights & ~7u) != 0u || (rights & NEXUS_MAP_READ) == 0u ||
        ((rights & NEXUS_MAP_WRITE) && (rights & NEXUS_MAP_EXECUTE)))
        return NEXUS_MAP_INVALID;
    if (nx == 0 && !(rights & NEXUS_MAP_EXECUTE))
        return NEXUS_MAP_UNSUPPORTED;
    return NEXUS_MAP_OK;
}

int main(void)
{
    const uint32_t high_bits[] = { 0xffffffffu, 0x80000001u, 0x7fffffffu,
                                   0x00010001u, 0x80000005u };
    unsigned cases = 0;
    for (uint32_t rights = 0; rights < 256; ++rights) {
        for (int nx = -1; nx <= 2; ++nx) {
            enum nexus_mapping_status got = nexus_mapping_validate(rights, nx);
            enum nexus_mapping_status want = expected(rights, nx);
            if (got != want) {
                fprintf(stderr, "FAIL rights=%u nx=%d got=%d want=%d\n",
                        rights, nx, got, want);
                return 1;
            }
            ++cases;
        }
    }
    for (unsigned i = 0; i < sizeof(high_bits)/sizeof(high_bits[0]); ++i) {
        for (int nx = -1; nx <= 2; ++nx) {
            if (nexus_mapping_validate(high_bits[i], nx) != NEXUS_MAP_INVALID)
                return 1;
            ++cases;
        }
    }
    printf("mapping NX input validation: PASS (%u cases)\n", cases);
    return 0;
}
