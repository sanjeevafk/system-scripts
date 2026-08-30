# system-scripts — Claude Code Guide

This document helps Claude Code (and other AI coding assistants) understand the project's structure, conventions, and key commands.

## Project Overview

`system-scripts` is a modular Linux dotfiles and automation tooling repository. It bootstraps a developer machine with shell config, CLI tools, AI agent integrations, and theming.

The repo is intentionally single-user focused. It has no CI/CD or automated tests — reproducibility across machines is the primary goal.

## Repository Layout

```
system-scripts/
├── bootstrap.sh          # Main machine bootstrapper (run once on a fresh machine)
├── setup.sh              # Thin wrapper around bootstrap.sh with --dry-run support
├── bashrc_custom.sh      # Shell aliases, PATH additions, fastfetch, direnv hook
├── gitconfig             # Git identity template (fill in your name and email)
├── sync_library.sh       # rclone-powered cloud sync with auto-archiving
├── scripts/
│   ├── email-tool        # Python CLI for sending and managing email (IMAP/SMTP)
│   ├── reach-saved       # Python CLI to search saved bookmarks library
│   ├── sync_saved_posts.py  # Bookmark sync hook (Instagram/YouTube/Twitter → JSON)
│   ├── render-diagram    # Mermaid diagram renderer
│   ├── konsole-wrapper.sh   # Smart KDE Konsole tab reuse script
│   └── extract_screenshots.py  # Screenshot metadata extractor
├── fastfetch/            # Fastfetch config (ASCII logo, module order)
├── agent-reach/          # AI agent internet access layer config
│   ├── agent-reach.toml  # Platform credentials and settings
│   └── copilot-instructions.md  # Instructions for GitHub Copilot
├── vpn/                  # VPN network namespace & proxy scripts
│   ├── proxy_launcher.py # Process proxy launcher
│   └── vpn_namespace.py  # VPN netns setup/teardown
├── .config/              # App-level config files (KDE, GTK, Konsole, Kvantum)
└── data/                 # Shared data store (bookmarks JSON, etc.)
```

## Key Commands

```bash
# Bootstrap a fresh machine (installs packages, symlinks configs, injects shell source)
./bootstrap.sh

# Quick setup with --dry-run support
./setup.sh [--dry-run]

# Sync local library to cloud storage
./sync_library.sh

# Send an email
scripts/email-tool send --from "you@example.com" --to "dest@example.com" \
  --subject "Subject" --body "Body"

# Search saved bookmarks
scripts/reach-saved "keyword"

# Render a Mermaid diagram
echo 'graph LR; A-->B' | scripts/render-diagram mermaid
```

## Coding Conventions

- **Shell scripts**: Bash, `set -euo pipefail`, double-quote variables, guard binaries with `command -v`.
- **Python scripts**: Python 3.8+, `from __future__ import annotations`, type hints preferred, graceful import fallbacks.
- **Error handling**: Print errors to `stderr` (`>&2`), exit non-zero on failure.
- **No hardcoded paths**: Use `$HOME`, `${BASH_SOURCE[0]}`, or `os.path.expanduser("~")`.
- **No hardcoded credentials**: Use example config files (`.example`) and environment variables.

## Configuration Files

| File | Purpose |
|---|---|
| `gitconfig` | Git template — fill in `[user]` before running bootstrap |
| `.config/email/config.json.example` | Email tool config template |
| `agent-reach/agent-reach.toml` | AI agent platform credentials |

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SYNC_LOCAL_DIR` | `$HOME/Documents/Library` | Source directory for sync |
| `SYNC_REMOTE` | `mylibrary:Library` | rclone remote target |

## Common Patterns

- Scripts in `scripts/` are designed to be added to `$PATH` by `bashrc_custom.sh`.
- `bootstrap.sh` sources `bashrc_custom.sh` into `~/.bashrc` and `~/.zshrc`.
- The `agent-reach/` directory is independent — it does not require the rest of the repo.
- `vpn/` requires `ip`, `iptables` or `nftables`, and WireGuard tools for namespace routing.

## Adding a New Script

1. Create the script in `scripts/`.
2. Make it executable: `chmod +x scripts/my-script`.
3. Document it in `README.md`.
4. If it needs config, add a `.config/my-script/config.json.example`.
