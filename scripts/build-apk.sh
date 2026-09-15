#!/usr/bin/env bash
set -euo pipefail

ZAID_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 "$ZAID_ROOT/scripts/build.py" "$@"
