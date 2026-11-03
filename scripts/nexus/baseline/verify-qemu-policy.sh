#!/usr/bin/env bash
# Lightweight wrapper for the QEMU resource-policy verifier.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "$0")" && pwd -P)"
exec python3 "$script_dir/verify-qemu-policy.py" "$@"
