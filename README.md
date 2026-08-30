# system-scripts

> Modular Linux system configuration, developer dotfiles, CLI automation tools, and AI agent environment tooling. Bootstrap any fresh machine with one command.

## Quickstart

```bash
git clone https://github.com/sanjeevafk/system-scripts.git ~/system-scripts
cd ~/system-scripts
./setup.sh
```

After running setup, open a new shell for changes to take effect.

## What's Included

| Category | Path | Description |
|---|---|---|
| **Installer** | `bootstrap.sh` / `setup.sh` | One-click machine bootstrap for Ubuntu, Debian, Fedora, and Arch |
| **Configs** | `configs/shell/` | Shell aliases, PATH extensions, fastfetch, direnv hook |
| **Configs** | `configs/git/` | Git identity template, gh CLI credential helper |
| **Configs** | `configs/desktop/` | KDE, GTK, Kvantum, and Konsole theme configurations |
| **Configs** | `configs/fastfetch/` | Terminal system info banner configuration and logos |
| **Tools** | `tools/bookmarks-sync/` | Cross-platform sync engine (LinkedIn, WhatsApp, GitHub Stars) |
| **Tools** | `tools/email/` | Multi-account CLI email tool (IMAP/SMTP, alias sending) |
| **Tools** | `tools/saved-posts/` | Semantic search and library sync across saved social bookmarks |
| **Tools** | `tools/vpn/` | Linux network namespace isolation and VPN proxy launcher |
| **Tools** | `tools/diagrams/` | Mermaid diagram rendering from the terminal |
| **Tools** | `tools/terminal/` | Single-instance Konsole tab wrapper and screenshot utilities |
| **Tools** | `tools/backup/` | Automated cloud storage backup and archiving with rclone |
| **AI Agents** | `agent-tools/agent-reach/` | AI agent web browsing, social search, and MCP tools |
| **AI Agents** | `agent-tools/antigravity/` | Real-time agent status line and shell environment bindings |

## Prerequisites

- **OS:** Debian/Ubuntu, Fedora, or Arch Linux
- **Shell:** Bash or Zsh
- **Required:** `git`, `curl`
- **Optional:** `rclone` (for cloud sync), `gh` (for GitHub CLI), `fastfetch` (for welcome banner)

## Installation

### Full Install (recommended)

```bash
./setup.sh
```

### Preview Changes First

```bash
./setup.sh --dry-run
```

## Key CLI Tools

### `sync-bookmarks` & `organize-stars`

```bash
# Sync saved posts across LinkedIn, WhatsApp self-notes, and GitHub Stars
sync-bookmarks

# Organize all your GitHub starred repositories into 7 native GitHub lists
organize-stars
```

### `email-tool`

```bash
email-tool send --from "you@yourdomain.com" --to "user@example.com" \
  --subject "Hello" --body "Message text"
```

### `reach-saved`

```bash
saved "machine learning papers"
saved --platform instagram --limit 20
```

### `render-diagram`

```bash
echo 'graph LR; A-->B-->C' | render-diagram mermaid
render-diagram mermaid path/to/diagram.mmd
```

## Repository Structure

```
system-scripts/
├── bootstrap.sh              # Main automated installer
├── setup.sh                  # Interactive wrapper (--dry-run support)
├── configs/                  # Configuration templates
│   ├── desktop/              # GTK, Konsole, Kvantum, KWin
│   ├── fastfetch/            # System banner configs & logos
│   ├── git/                  # Gitconfig template
│   └── shell/                # Modular shell customizations & aliases
├── tools/                    # Standalone automation tools
│   ├── backup/               # Rclone cloud synchronization
│   ├── bookmarks-sync/       # LinkedIn, WhatsApp & GitHub Stars sync engine
│   ├── diagrams/             # Terminal diagram rendering
│   ├── email/                # Email CLI client
│   ├── saved-posts/          # Universal bookmark query engine
│   ├── terminal/             # Tab wrappers & screenshot extractors
│   └── vpn/                  # Network namespace isolation
└── agent-tools/              # AI Agent extensions & MCP tools
    ├── agent-reach/          # Agent internet access layer
    └── antigravity/          # Agent CLI status line integrations
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT License — see [LICENSE](LICENSE).
