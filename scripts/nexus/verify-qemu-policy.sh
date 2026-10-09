#!/usr/bin/env bash
#
# Enforce the resource-aware Nexus QEMU GitHub Actions policy.
#
set -euo pipefail

die()
{
    printf 'nexus-qemu-policy: ERROR: %s\n' "$*" >&2
    return 1
}

require_pattern()
{
    file="$1"
    pattern="$2"
    grep -Fq -- "$pattern" "$file" ||
        die "missing required QEMU policy pattern: $pattern"
}

reject_pattern()
{
    file="$1"
    pattern="$2"
    if grep -Eq -- "$pattern" "$file"; then
        die "forbidden QEMU policy pattern present: $pattern"
    fi
}

check_policy()
{
    root="$1"
    workflow="$root/.github/workflows/nexus-qemu.yml"

    [ -f "$workflow" ] || die "missing QEMU workflow: $workflow" || return 1

    require_pattern "$workflow" "  workflow_dispatch:" || return 1
    require_pattern "$workflow" "  pull_request:" || return 1
    require_pattern "$workflow" "      - ready_for_review" || return 1
    require_pattern "$workflow" "  cancel-in-progress: true" || return 1
    require_pattern "$workflow" "    timeout-minutes: 60" || return 1
    require_pattern "$workflow" "      NEXUS_QEMU_CPUS: '1'" || return 1
    require_pattern "$workflow" "      BUILDTHREADS: '2'" || return 1
    require_pattern "$workflow" "      NEXUS_QEMU_TIMEOUT_SECONDS: '60'" || return 1
    require_pattern "$workflow" "      NEXUS_QEMU_EXPECT_MARKER: 'AROS64 - The AROS Research OS'" || return 1
    require_pattern "$workflow" "            qemu-system-x86" || return 1
    require_pattern "$workflow" "          retention-days: 3" || return 1

    reject_pattern "$workflow" '^  push:' || return 1
    reject_pattern "$workflow" '^  schedule:' || return 1
    reject_pattern "$workflow" '^[[:space:]]*-[[:space:]]+synchronize[[:space:]]*$' || return 1
    reject_pattern "$workflow" '^[[:space:]]*matrix:' || return 1
    reject_pattern "$workflow" 'cron:' || return 1

    upload_section="$(
        awk '
            /- name: Upload short-lived QEMU evidence/ { capture=1 }
            capture { print }
        ' "$workflow"
    )"

    if printf '%s\n' "$upload_section" | grep -Eq '\.iso([[:space:]]|$)|aros-pc-x86_64\.iso'; then
        die "QEMU workflow must not upload the ISO by default"
        return 1
    fi

    return 0
}

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git -C "$script_dir" rev-parse --show-toplevel 2>/dev/null)" ||
    {
        printf 'nexus-qemu-policy: ERROR: not inside repository\n' >&2
        exit 1
    }

check_policy "$repo_root"

if [ "${1:-}" != "--selftest" ]; then
    printf 'nexus-qemu-policy: PASS\n'
    exit 0
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/.github/workflows"

source_workflow="$repo_root/.github/workflows/nexus-qemu.yml"
fixture="$tmp/.github/workflows/nexus-qemu.yml"

reset_fixture()
{
    cp "$source_workflow" "$fixture"
}

expect_fixture_failure()
{
    label="$1"
    if check_policy "$tmp" >/dev/null 2>&1; then
        printf 'nexus-qemu-policy: ERROR: failed to detect %s\n' "$label" >&2
        exit 1
    fi
}

reset_fixture
check_policy "$tmp" ||
    {
        printf 'nexus-qemu-policy: ERROR: pristine fixture failed\n' >&2
        exit 1
    }

reset_fixture
python3 - "$fixture" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text()
s = s.replace("on:\n", "on:\n  push:\n", 1)
p.write_text(s)
PY
expect_fixture_failure "automatic push trigger"

reset_fixture
python3 - "$fixture" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text().replace("      - ready_for_review\n", "      - synchronize\n", 1)
p.write_text(s)
PY
expect_fixture_failure "synchronize trigger"

reset_fixture
python3 - "$fixture" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text().replace("    runs-on: ubuntu-latest\n", "    strategy:\n      matrix:\n        cpu: [1, 2, 4]\n    runs-on: ubuntu-latest\n", 1)
p.write_text(s)
PY
expect_fixture_failure "automatic matrix"

reset_fixture
python3 - "$fixture" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text().replace("      NEXUS_QEMU_CPUS: '1'\n", "      NEXUS_QEMU_CPUS: '4'\n", 1)
p.write_text(s)
PY
expect_fixture_failure "multi-vCPU default"

printf 'nexus-qemu-policy self-test: PASS\n'
