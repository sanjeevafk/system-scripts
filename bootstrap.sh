#!/usr/bin/env bash
# ==============================================================================
# Script Name: bootstrap.sh
# Description: Modular bootstrap script for system-scripts developer environment.
#              Installs core tools, Nerd fonts, symlinks configs, sets up
#              CLI automation tools and AI agent integrations.
# ==============================================================================

set -euo pipefail

info() { echo -e "\x1b[32m[INFO]\x1b[0m $*"; }
warn() { echo -e "\x1b[33m[WARN]\x1b[0m $*"; }
error() { echo -e "\x1b[31m[ERROR]\x1b[0m $*"; exit 1; }

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

# ------------------------------------------------------------------------------
# Step 1: Detect Distro & Install Core Packages
# ------------------------------------------------------------------------------
info "Detecting system package manager..."

PACKAGES=("rclone" "tesseract-ocr" "fastfetch" "curl" "unzip" "nodejs" "chafa")

if command -v apt-get >/dev/null 2>&1; then
    info "Detected Debian/Ubuntu-based system (apt)."
    sudo apt-get update
    sudo apt-get install -y "${PACKAGES[@]}"
elif command -v dnf >/dev/null 2>&1; then
    info "Detected Fedora/RHEL-based system (dnf)."
    sudo dnf install -y rclone tesseract fastfetch curl unzip nodejs chafa
elif command -v pacman >/dev/null 2>&1; then
    info "Detected Arch-based system (pacman)."
    sudo pacman -Sy --noconfirm rclone tesseract fastfetch curl unzip nodejs chafa
else
    warn "Unsupported package manager. Please install the following manually:"
    warn "  rclone, tesseract, fastfetch, curl, unzip, nodejs, chafa"
fi

# ------------------------------------------------------------------------------
# Step 2: Install JetBrainsMono Nerd Font
# ------------------------------------------------------------------------------
info "Installing JetBrainsMono Nerd Font..."
FONT_DIR="$HOME/.local/share/fonts"
mkdir -p "$FONT_DIR"

if [ ! -f "$FONT_DIR/JetBrainsMonoNerdFont-Regular.ttf" ]; then
    info "Downloading JetBrainsMono Nerd Font..."
    curl -fLo /tmp/JetBrainsMono.zip https://github.com/ryanoasis/nerd-fonts/releases/latest/download/JetBrainsMono.zip
    info "Extracting font files..."
    unzip -o /tmp/JetBrainsMono.zip -d "$FONT_DIR"
    rm -f /tmp/JetBrainsMono.zip
    
    if command -v fc-cache >/dev/null 2>&1; then
        info "Updating font cache..."
        fc-cache -f
    fi
else
    info "JetBrainsMono Nerd Font already installed, skipping."
fi

# ------------------------------------------------------------------------------
# Step 3: Symlink Core Configurations & CLI Tools
# ------------------------------------------------------------------------------
info "Setting up configuration symlinks..."

# Fastfetch configuration
if [ -d "$DIR/configs/fastfetch" ]; then
    mkdir -p "$HOME/.config/fastfetch"
    ln -sfn "$DIR/configs/fastfetch/config.jsonc" "$HOME/.config/fastfetch/config.jsonc"
    ln -sfn "$DIR/configs/fastfetch/logos" "$HOME/.config/fastfetch/logos"
    info "Linked Fastfetch configs."
fi

# Antigravity CLI statusline
if [ -f "$DIR/agent-tools/antigravity/statusline.js" ]; then
    mkdir -p "$HOME/.gemini/antigravity-cli"
    ln -sfn "$DIR/agent-tools/antigravity/statusline.js" "$HOME/.gemini/antigravity-cli/statusline.js"
    info "Linked Antigravity statusline script."
fi

# CLI Tools
mkdir -p "$HOME/.local/bin"

if [ -f "$DIR/tools/email/email-tool" ]; then
    ln -sfn "$DIR/tools/email/email-tool" "$HOME/.local/bin/email-tool"
    chmod +x "$DIR/tools/email/email-tool"
    info "Linked Email CLI tool."
fi

if [ -f "$DIR/tools/diagrams/render-diagram" ]; then
    ln -sfn "$DIR/tools/diagrams/render-diagram" "$HOME/.local/bin/render-diagram"
    chmod +x "$DIR/tools/diagrams/render-diagram"
    info "Linked render-diagram CLI tool."
fi

if [ -f "$DIR/tools/saved-posts/reach-saved" ]; then
    ln -sfn "$DIR/tools/saved-posts/reach-saved" "$HOME/.local/bin/reach-saved"
    chmod +x "$DIR/tools/saved-posts/reach-saved"
    info "Linked reach-saved CLI tool."
fi

# ------------------------------------------------------------------------------
# Step 4: Conditionally Link Desktop & Theme Configurations
# ------------------------------------------------------------------------------
if command -v konsole >/dev/null 2>&1 || [ -d "$HOME/.config" ]; then
    info "Setting up desktop theme configurations..."
    
    # GTK settings
    mkdir -p "$HOME/.config/gtk-3.0" "$HOME/.config/gtk-4.0" "$HOME/.config/Kvantum"
    [ -f "$DIR/configs/desktop/gtk/settings.ini" ] && ln -sfn "$DIR/configs/desktop/gtk/settings.ini" "$HOME/.config/gtk-3.0/settings.ini"
    [ -f "$DIR/configs/desktop/gtk/settings.ini" ] && ln -sfn "$DIR/configs/desktop/gtk/settings.ini" "$HOME/.config/gtk-4.0/settings.ini"
    [ -f "$DIR/configs/desktop/kvantum/kvantum.kvconfig" ] && ln -sfn "$DIR/configs/desktop/kvantum/kvantum.kvconfig" "$HOME/.config/Kvantum/kvantum.kvconfig"
    
    # KWin & Konsole settings
    [ -f "$DIR/configs/desktop/konsolerc" ] && ln -sfn "$DIR/configs/desktop/konsolerc" "$HOME/.config/konsolerc"
    [ -f "$DIR/configs/desktop/kwinrc" ] && ln -sfn "$DIR/configs/desktop/kwinrc" "$HOME/.config/kwinrc"
    
    # Local color schemes & Konsole profiles
    mkdir -p "$HOME/.local/share/color-schemes" "$HOME/.local/share/konsole" "$HOME/.local/share/kxmlgui5/konsole" "$HOME/.local/share/applications"
    [ -f "$DIR/configs/desktop/konsole/VSCodeDarkModern.colors" ] && ln -sfn "$DIR/configs/desktop/konsole/VSCodeDarkModern.colors" "$HOME/.local/share/color-schemes/VSCodeDarkModern.colors"
    [ -f "$DIR/configs/desktop/konsole/VSCodeDarkModern.colorscheme" ] && ln -sfn "$DIR/configs/desktop/konsole/VSCodeDarkModern.colorscheme" "$HOME/.local/share/konsole/VSCodeDarkModern.colorscheme"
    [ -f "$DIR/configs/desktop/konsole/VSCodeDarkModern.profile" ] && ln -sfn "$DIR/configs/desktop/konsole/VSCodeDarkModern.profile" "$HOME/.local/share/konsole/VSCodeDarkModern.profile"
    [ -f "$DIR/configs/desktop/konsole/konsoleui.rc" ] && ln -sfn "$DIR/configs/desktop/konsole/konsoleui.rc" "$HOME/.local/share/kxmlgui5/konsole/konsoleui.rc"
    [ -f "$DIR/configs/desktop/konsole/sessionui.rc" ] && ln -sfn "$DIR/configs/desktop/konsole/sessionui.rc" "$HOME/.local/share/kxmlgui5/konsole/sessionui.rc"
    [ -f "$DIR/configs/desktop/konsole/org.kde.konsole.desktop" ] && ln -sfn "$DIR/configs/desktop/konsole/org.kde.konsole.desktop" "$HOME/.local/share/applications/org.kde.konsole.desktop"

    # Single-instance Konsole wrapper
    if [ -f "$DIR/tools/terminal/konsole-wrapper.sh" ] && sudo -v 2>/dev/null; then
        sudo cp "$DIR/tools/terminal/konsole-wrapper.sh" /usr/local/bin/konsole
        sudo chmod +x /usr/local/bin/konsole
    fi
    
    info "Linked theme & desktop configurations."
fi

# ------------------------------------------------------------------------------
# Step 5: Shell & Git Config
# ------------------------------------------------------------------------------
SHELL_CONFIGS=("$HOME/.bashrc" "$HOME/.zshrc")

# 5a. Git config template
if [ ! -f "$HOME/.gitconfig" ] && [ -f "$DIR/configs/git/gitconfig.example" ]; then
    cp "$DIR/configs/git/gitconfig.example" "$HOME/.gitconfig"
    info "Created ~/.gitconfig from template."
fi

# 5b. Source custom shell customizations
CUSTOM_LINE="source $DIR/configs/shell/bashrc_custom.sh"
for shell_file in "${SHELL_CONFIGS[@]}"; do
    if [ -f "$shell_file" ]; then
        if ! grep -qF "$CUSTOM_LINE" "$shell_file"; then
            info "Injecting bashrc_custom.sh into $shell_file..."
            echo -e "\n# System-scripts modular shell customizations\n$CUSTOM_LINE" >> "$shell_file"
        else
            info "bashrc_custom.sh already wired in $shell_file."
        fi
    fi
done

# ------------------------------------------------------------------------------
# Step 6: Agent Reach — AI Internet Access Layer
# ------------------------------------------------------------------------------
if [ -d "$DIR/agent-tools/agent-reach" ]; then
    info "Setting up Agent Reach..."
    
    if [ ! -d "$HOME/.agent-reach-venv" ]; then
        info "Creating Agent Reach venv..."
        python3 -m venv "$HOME/.agent-reach-venv"
        "$HOME/.agent-reach-venv/bin/pip" install \
            https://github.com/Panniantong/agent-reach/archive/main.zip --quiet
        info "Running Agent Reach installer..."
        "$HOME/.agent-reach-venv/bin/agent-reach" install --env=auto || true
    fi

    # Symlink SKILL.md to agent directories
    SKILL_SRC="$DIR/agent-tools/agent-reach/SKILL.md"
    SKILL_REFS_SRC="$DIR/agent-tools/agent-reach/references"
    SKILL_DIRS=(
        "$HOME/.agents/skills/agent-reach"
        "$HOME/.claude/skills/agent-reach"
        "$HOME/.hermes/skills/agent-reach"
        "$HOME/.codex/skills/agent-reach"
    )
    for skill_dir in "${SKILL_DIRS[@]}"; do
        if [ -d "$(dirname "$skill_dir")" ]; then
            mkdir -p "$skill_dir"
            [ -f "$SKILL_SRC" ]      && ln -sfn "$SKILL_SRC"      "$skill_dir/SKILL.md"
            [ -d "$SKILL_REFS_SRC" ] && ln -sfn "$SKILL_REFS_SRC" "$skill_dir/references"
        fi
    done
fi

# ------------------------------------------------------------------------------
# Step 7: OpenCLI Adapters & Automated Bookmarks Sync
# ------------------------------------------------------------------------------
info "Setting up OpenCLI adapters and bookmarks sync..."

if ! command -v opencli >/dev/null 2>&1; then
    mkdir -p "$HOME/.npm-global"
    npm config set prefix "$HOME/.npm-global"
    npm install -g @jackwener/opencli --quiet || true
fi

# Symlink custom WhatsApp adapters
mkdir -p "$HOME/.opencli/clis"
if [ -d "$DIR/tools/bookmarks-sync/clis/whatsapp" ]; then
    ln -sfn "$DIR/tools/bookmarks-sync/clis/whatsapp" "$HOME/.opencli/clis/whatsapp"
    info "Linked custom WhatsApp OpenCLI adapters."
fi

# Symlink sync-bookmarks CLI
mkdir -p "$HOME/.local/bin"
if [ -f "$DIR/tools/bookmarks-sync/run_cron_sync.sh" ]; then
    ln -sfn "$DIR/tools/bookmarks-sync/run_cron_sync.sh" "$HOME/.local/bin/sync-bookmarks"
    chmod +x "$DIR/tools/bookmarks-sync/"*.py "$DIR/tools/bookmarks-sync/"*.sh 2>/dev/null || true
    info "Linked sync-bookmarks CLI -> $HOME/.local/bin/sync-bookmarks"
fi

# Schedule cron job
CRON_CMD="0 */6 * * * $DIR/tools/bookmarks-sync/run_cron_sync.sh"
if command -v crontab >/dev/null 2>&1; then
    if ! crontab -l 2>/dev/null | grep -qF "tools/bookmarks-sync/run_cron_sync.sh"; then
        (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
        info "Installed bookmarks sync cron job."
    fi
fi

info "Restoration complete! Restart your shell or run 'source ~/.bashrc'."
