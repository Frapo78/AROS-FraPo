/* Standalone host test. This does not exercise the AROS kernel or hardware MMU. */
#include <stdio.h>
#define CHECK(expr) do { \
    if (!(expr)) { \
        fprintf(stderr, "FAIL at line %d: %s\n", __LINE__, #expr); \
        return 1; \
    } \
} while (0)
#include "../mapping_rights.h"

int main(void)
{
    CHECK(nexus_mapping_validate(NEXUS_MAP_READ, 1) == NEXUS_MAP_OK);
    CHECK(nexus_mapping_validate(NEXUS_MAP_READ | NEXUS_MAP_WRITE, 1) == NEXUS_MAP_OK);
    CHECK(nexus_mapping_validate(NEXUS_MAP_READ | NEXUS_MAP_EXECUTE, 1) == NEXUS_MAP_OK);
    CHECK(nexus_mapping_validate(0, 1) == NEXUS_MAP_INVALID);
    CHECK(nexus_mapping_validate(NEXUS_MAP_WRITE, 1) == NEXUS_MAP_INVALID);
    CHECK(nexus_mapping_validate(NEXUS_MAP_READ | NEXUS_MAP_WRITE | NEXUS_MAP_EXECUTE, 1) == NEXUS_MAP_INVALID);
    CHECK(nexus_mapping_validate(NEXUS_MAP_READ | (1u << 31), 1) == NEXUS_MAP_INVALID);
    CHECK(nexus_mapping_validate(NEXUS_MAP_READ, 0) == NEXUS_MAP_UNSUPPORTED);
    CHECK(nexus_mapping_validate(NEXUS_MAP_READ | NEXUS_MAP_EXECUTE, 0) == NEXUS_MAP_OK);
    puts("nexus mapping-rights: PASS");
    return 0;
}
