#!/bin/bash
# ==============================================================================
# Script Name: sync_library.sh
# Description: Synchronizes a local directory to cloud storage using rclone.
#              Includes an automatic archiving system to prevent data loss 
#              from accidental deletions or overwrites.
# Environment Variables:
#   SYNC_SRC      Local source directory (default: $HOME/Documents)
#   RCLONE_REMOTE Remote rclone name (default: gdrive)
#   REMOTE_DEST   Target directory on remote (default: Library)
# ==============================================================================

set -euo pipefail

SYNC_SRC="${SYNC_SRC:-$HOME/Documents}"
RCLONE_REMOTE="${RCLONE_REMOTE:-gdrive}"
REMOTE_DEST="${REMOTE_DEST:-Library}"

if ! command -v rclone >/dev/null 2>&1; then
    echo "Error: rclone is not installed. Run bootstrap.sh first."
    exit 1
fi

if ! rclone listremotes 2>/dev/null | grep -q "^${RCLONE_REMOTE}:$"; then
    echo "Error: rclone remote '${RCLONE_REMOTE}' not configured. Run: rclone config"
    exit 1
fi

echo "Starting synchronization: ${SYNC_SRC} -> ${RCLONE_REMOTE}:${REMOTE_DEST}..."

rclone sync "${SYNC_SRC}" "${RCLONE_REMOTE}:${REMOTE_DEST}" \
  --backup-dir "${RCLONE_REMOTE}:Archive/$(date +%Y-%m-%d)" \
  --size-only \
  --track-renames \
  --fast-list \
  --log-file "$HOME/rclone-backup.log" \
  --log-level INFO \
  --progress

echo "Synchronization complete! Check ~/rclone-backup.log for details."
