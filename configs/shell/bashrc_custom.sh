#!/usr/bin/env bash
# ==============================================================================
# bashrc_custom.sh — Modular Shell Customizations & Tool Aliases
# Sourced by ~/.bashrc or ~/.zshrc via bootstrap.sh
# ==============================================================================

# Direnv: auto-load .envrc per directory (no subshell)
if command -v direnv &>/dev/null; then
    _direnv_hook() {
        local previous_exit_status=$?;
        if [[ -f .envrc || -f ../.envrc || -f ../../.envrc || -n "$DIRENV_DIR" ]]; then
            trap -- '' SIGINT;
            eval "$(direnv export bash)";
            trap - SIGINT;
        fi
        return $previous_exit_status;
    };
    if ! [[ "${PROMPT_COMMAND:-}" =~ _direnv_hook ]]; then
        PROMPT_COMMAND="_direnv_hook${PROMPT_COMMAND:+;$PROMPT_COMMAND}"
    fi
fi

# Resolve repo root directory
CONFIG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd "$CONFIG_DIR/../.." && pwd -P)"

# CLI Tool Aliases
alias skills='global-skills'
alias backup-library='bash "$REPO_ROOT/tools/backup/sync_library.sh"'
alias sync-saved='python3 "$REPO_ROOT/tools/saved-posts/sync_saved_posts.py"'
alias sync-bookmarks='bash "$REPO_ROOT/tools/bookmarks-sync/run_cron_sync.sh"'
alias organize-stars='python3 "$REPO_ROOT/tools/bookmarks-sync/organize_github_stars.py"'
alias saved='reach-saved'

# Run fastfetch on shell open
command -v fastfetch &>/dev/null && fastfetch

# PATH extensions
export PATH="$HOME/.npm-global/bin:$HOME/.agent-reach-venv/bin:$HOME/.local/bin:$PATH"
