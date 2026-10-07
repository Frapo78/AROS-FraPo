#!/usr/bin/env bash
#
# Validate the Nexus agent/process contract and prove that key degradations are
# detected. This is process tooling, not an OS/runtime test.
#
set -euo pipefail

die()
{
    printf 'nexus-agent-contract: ERROR: %s\n' "$*" >&2
    return 1
}

require_file()
{
    root="$1"
    file="$2"
    [ -f "$root/$file" ] || die "missing required file: $file"
}

require_pattern()
{
    root="$1"
    file="$2"
    pattern="$3"
    grep -q -- "$pattern" "$root/$file" ||
        die "missing required contract pattern in $file: $pattern"
}

check_contract()
{
    root="$1"

    for file in         AGENTS.md         docs/nexus/VERIFICATION_MODEL.md         docs/nexus/REVIEW_PROTOCOL.md         .github/ISSUE_TEMPLATE/nexus_engineering_task.md         .github/pull_request_template.md
    do
        require_file "$root" "$file" || return 1
    done

    lines="$(wc -l < "$root/AGENTS.md")"
    [ "$lines" -le 300 ] ||
        die "AGENTS.md exceeds 300 lines: $lines" || return 1

    require_pattern "$root" AGENTS.md 'NO TEST, EXPLAIN WHY' || return 1
    require_pattern "$root" AGENTS.md 'No L1-L5 claim is accepted on AI review alone' || return 1
    require_pattern "$root" AGENTS.md 'one logical integrator' || return 1

    require_pattern "$root" docs/nexus/VERIFICATION_MODEL.md 'H1 — mandatory human technical review' || return 1
    require_pattern "$root" docs/nexus/VERIFICATION_MODEL.md 'E6 — physical hardware' || return 1
    require_pattern "$root" docs/nexus/VERIFICATION_MODEL.md 'AI-only review is not sufficient' || return 1

    require_pattern "$root" docs/nexus/REVIEW_PROTOCOL.md 'Review 3 — Evidence Red Team' || return 1
    require_pattern "$root" docs/nexus/REVIEW_PROTOCOL.md 'NO TEST, EXPLAIN WHY' || return 1

    require_pattern "$root" .github/ISSUE_TEMPLATE/nexus_engineering_task.md '## Acceptance criteria' || return 1
    require_pattern "$root" .github/ISSUE_TEMPLATE/nexus_engineering_task.md '## Negative / red-team criteria' || return 1
    require_pattern "$root" .github/ISSUE_TEMPLATE/nexus_engineering_task.md '## Review 3 test plan' || return 1

    require_pattern "$root" .github/pull_request_template.md '## Review 3 — Evidence Red Team' || return 1
    require_pattern "$root" .github/pull_request_template.md 'NO TEST, EXPLAIN WHY' || return 1
    require_pattern "$root" .github/pull_request_template.md '## Human / hardware gate' || return 1

    return 0
}

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git -C "$script_dir" rev-parse --show-toplevel 2>/dev/null)" ||
    {
        printf 'nexus-agent-contract: ERROR: not inside repository\n' >&2
        exit 1
    }

check_contract "$repo_root"

if [ "${1:-}" != "--selftest" ]; then
    printf 'nexus-agent-contract: PASS\n'
    exit 0
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

mkdir -p     "$tmp/docs/nexus"     "$tmp/.github/ISSUE_TEMPLATE"     "$tmp/.github"

cp "$repo_root/AGENTS.md" "$tmp/AGENTS.md"
cp "$repo_root/docs/nexus/VERIFICATION_MODEL.md" "$tmp/docs/nexus/VERIFICATION_MODEL.md"
cp "$repo_root/docs/nexus/REVIEW_PROTOCOL.md" "$tmp/docs/nexus/REVIEW_PROTOCOL.md"
cp "$repo_root/.github/ISSUE_TEMPLATE/nexus_engineering_task.md"     "$tmp/.github/ISSUE_TEMPLATE/nexus_engineering_task.md"
cp "$repo_root/.github/pull_request_template.md"     "$tmp/.github/pull_request_template.md"

check_contract "$tmp" ||
    {
        printf 'nexus-agent-contract: ERROR: pristine self-test fixture failed\n' >&2
        exit 1
    }

# Adversarial case 1: remove the mandatory red-team fallback rule.
sed -i '/NO TEST, EXPLAIN WHY/d' "$tmp/AGENTS.md"
if check_contract "$tmp" >/dev/null 2>&1; then
    printf 'nexus-agent-contract: ERROR: failed to detect missing NO TEST rule\n' >&2
    exit 1
fi
cp "$repo_root/AGENTS.md" "$tmp/AGENTS.md"

# Adversarial case 2: remove acceptance criteria from the task template.
sed -i '/## Acceptance criteria/d' "$tmp/.github/ISSUE_TEMPLATE/nexus_engineering_task.md"
if check_contract "$tmp" >/dev/null 2>&1; then
    printf 'nexus-agent-contract: ERROR: failed to detect missing acceptance criteria\n' >&2
    exit 1
fi
cp "$repo_root/.github/ISSUE_TEMPLATE/nexus_engineering_task.md"     "$tmp/.github/ISSUE_TEMPLATE/nexus_engineering_task.md"

# Adversarial case 3: make the supposedly concise agent brief too large.
i=0
while [ "$i" -lt 100 ]; do
    printf 'red-team-padding-%s\n' "$i" >> "$tmp/AGENTS.md"
    i=$((i + 1))
done
if check_contract "$tmp" >/dev/null 2>&1; then
    printf 'nexus-agent-contract: ERROR: failed to detect oversized AGENTS.md\n' >&2
    exit 1
fi

printf 'nexus-agent-contract self-test: PASS\n'
