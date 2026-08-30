#!/usr/bin/env bash
# setup.sh — Quick installer for system-scripts
# Usage: curl -fsSL <url>/setup.sh | bash
#    or: ./setup.sh [--help] [--dry-run]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Bootstrap system-scripts on this machine.

Options:
  -h, --help      Show this help and exit.
  -n, --dry-run   Print what would be done, but make no changes.

Examples:
  $0              Run full install.
  $0 --dry-run    Preview install steps.
EOF
}

DRY_RUN=false
for arg in "$@"; do
    case "$arg" in
        -h|--help)  usage; exit 0 ;;
        -n|--dry-run) DRY_RUN=true ;;
        *) echo "Unknown argument: $arg" >&2; usage >&2; exit 1 ;;
    esac
done

if [ "$DRY_RUN" = true ]; then
    echo "[dry-run] Would execute: $SCRIPT_DIR/bootstrap.sh"
    echo "[dry-run] No changes made."
    exit 0
fi

if [ ! -f "$SCRIPT_DIR/bootstrap.sh" ]; then
    echo "Error: bootstrap.sh not found at $SCRIPT_DIR" >&2
    exit 1
fi

chmod +x "$SCRIPT_DIR/bootstrap.sh"
exec "$SCRIPT_DIR/bootstrap.sh"
