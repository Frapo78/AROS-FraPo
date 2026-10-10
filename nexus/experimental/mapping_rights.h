/* Nexus Phase 0: pure mapping-rights contract, NOT a page-table implementation.
 * No CR3 writes, MMU ownership, privilege transition or AROS ABI change.
 */
#ifndef NEXUS_MAPPING_RIGHTS_H
#define NEXUS_MAPPING_RIGHTS_H

#include <stdint.h>

enum nexus_mapping_right {
    NEXUS_MAP_READ = 1u << 0,
    NEXUS_MAP_WRITE = 1u << 1,
    NEXUS_MAP_EXECUTE = 1u << 2
};

enum nexus_mapping_status {
    NEXUS_MAP_OK = 0,
    NEXUS_MAP_INVALID = -1,
    NEXUS_MAP_UNSUPPORTED = -2
};

/* A conservative validation policy for future protected-native mappings.
 * AROS legacy mappings MUST NOT be passed through this validator implicitly.
 * No successful result here constitutes a hardware isolation guarantee.
 */
static inline enum nexus_mapping_status
nexus_mapping_validate(uint32_t rights, int hardware_nx_supported)
{
    const uint32_t allowed = NEXUS_MAP_READ | NEXUS_MAP_WRITE | NEXUS_MAP_EXECUTE;
    if ((rights & ~allowed) != 0u || (rights & NEXUS_MAP_READ) == 0u)
        return NEXUS_MAP_INVALID;
    if ((rights & NEXUS_MAP_WRITE) && (rights & NEXUS_MAP_EXECUTE))
        return NEXUS_MAP_INVALID;
    if (!hardware_nx_supported && !(rights & NEXUS_MAP_EXECUTE))
        return NEXUS_MAP_UNSUPPORTED;
    return NEXUS_MAP_OK;
}

#endif
