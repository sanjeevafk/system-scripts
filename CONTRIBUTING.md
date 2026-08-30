# Contributing to system-scripts

Thanks for your interest in contributing.

## Principles

- **Reproducibility first.** The repo should work on a fresh Debian/Ubuntu, Fedora, or Arch machine without manual intervention.
- **No hardcoded credentials or paths.** Use `$HOME`, environment variables, and `.example` config files.
- **Fail loudly.** Scripts should exit with a non-zero code and a clear `stderr` message when something is wrong.

## Reporting Bugs

1. Check existing issues first.
2. Open an issue with:
   - OS and version
   - Steps to reproduce
   - Expected vs actual behavior
   - Relevant error output

## Proposing Changes

1. Fork the repository.
2. Create a branch: `git checkout -b fix/short-description`.
3. Make your changes following the conventions below.
4. Test manually on a clean shell session.
5. Open a pull request with a clear description of the change.

## Code Conventions

### Shell Scripts

```bash
#!/usr/bin/env bash
set -euo pipefail

# Guard against missing binaries
if ! command -v rclone >/dev/null 2>&1; then
    echo "Error: rclone is not installed." >&2
    exit 1
fi
```

- Use `set -euo pipefail` at the top.
- Double-quote all variable expansions: `"$VAR"`, not `$VAR`.
- Check required binaries before using them.
- Print errors to `stderr`, not `stdout`.

### Python Scripts

```python
#!/usr/bin/env python3
from __future__ import annotations
```

- Require Python 3.8+.
- Use `from __future__ import annotations` for forward references.
- Add type hints on public functions.
- Use `sys.exit(1)` with a message to `sys.stderr` on errors.
- Handle optional imports gracefully (use try/except with a flag).

### Documentation

- Follow plain, direct English (ASD-STE100 style).
- One idea per sentence. Keep sentences under 25 words.
- Update `README.md` when adding new scripts or configuration.

## What Not to Submit

- Hardcoded personal emails, usernames, or API tokens.
- Absolute paths like `/home/yourname/...` — use `$HOME` instead.
- Platform-specific code without a documented fallback.
- Dependencies that require accounts or paid services without a free alternative.
