/* Standalone host test. This does not exercise the AROS kernel or hardware MMU. */
#include <assert.h>
#include <stdio.h>
#include "../mapping_rights.h"

int main(void)
{
    assert(nexus_mapping_validate(NEXUS_MAP_READ, 1) == NEXUS_MAP_OK);
    assert(nexus_mapping_validate(NEXUS_MAP_READ | NEXUS_MAP_WRITE, 1) == NEXUS_MAP_OK);
    assert(nexus_mapping_validate(NEXUS_MAP_READ | NEXUS_MAP_EXECUTE, 1) == NEXUS_MAP_OK);
    assert(nexus_mapping_validate(0, 1) == NEXUS_MAP_INVALID);
    assert(nexus_mapping_validate(NEXUS_MAP_WRITE, 1) == NEXUS_MAP_INVALID);
    assert(nexus_mapping_validate(NEXUS_MAP_READ | NEXUS_MAP_WRITE | NEXUS_MAP_EXECUTE, 1) == NEXUS_MAP_INVALID);
    assert(nexus_mapping_validate(NEXUS_MAP_READ | (1u << 31), 1) == NEXUS_MAP_INVALID);
    assert(nexus_mapping_validate(NEXUS_MAP_READ, 0) == NEXUS_MAP_UNSUPPORTED);
    assert(nexus_mapping_validate(NEXUS_MAP_READ | NEXUS_MAP_EXECUTE, 0) == NEXUS_MAP_OK);
    puts("nexus mapping-rights: PASS");
    return 0;
}
