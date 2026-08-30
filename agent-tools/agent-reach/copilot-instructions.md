# GitHub Copilot — Agent Reach Instructions

You have internet access via Agent Reach. Use these tools directly when the user
asks you to search, read, or summarise content from the web or social platforms.

## Quick Reference

| User asks about         | Run this                                          |
|-------------------------|---------------------------------------------------|
| Any webpage / URL       | `curl https://r.jina.ai/<URL>`                    |
| Medium reading list     | `medium list -n 20`                                |
| Medium read article     | `medium read <URL>` (unpaywalls via Freedium)      |
| YouTube video           | `yt-dlp --write-auto-sub --skip-download <URL>`   |
| GitHub repo/issue/PR    | `gh repo view <owner>/<repo>` / `gh issue list`   |
| Twitter/X search        | `twitter search "<query>"`                        |
| Twitter bookmarks       | `twitter bookmarks -n 20 --full-text`             |
| Twitter user timeline   | `twitter user <handle>`                           |
| Twitter thread          | `twitter show <tweet-url>`                        |
| Bilibili search/video   | `bili search "<query>"` / `bili video <bvid>`     |
| RSS feed                | Use feedparser (Python) or curl the feed URL      |
| V2EX topics             | `curl https://www.v2ex.com/api/topics/hot.json`   |
| Web semantic search     | `npx mcporter@latest run exa -- search "<query>"` |

## Twitter/X Auth

Twitter credentials are in the environment (set in ~/.bashrc):
- `TWITTER_AUTH_TOKEN` — session token
- `TWITTER_CT0` — CSRF token

These are set automatically in any shell that sources ~/.bashrc. No extra setup needed.

## GitHub Auth

Already authenticated via `gh auth login`. Use `gh` commands freely.

## Tool Locations

- `twitter`     → `~/.local/bin/twitter`   (twitter-cli via uv)
- `yt-dlp`      → `/usr/bin/yt-dlp`
- `gh`          → `/usr/bin/gh`
- `agent-reach` → `~/.agent-reach-venv/bin/agent-reach`
- `mcporter`    → `~/.npm-global/bin/mcporter`

## Health Check

```bash
source ~/.agent-reach-venv/bin/activate && agent-reach doctor
```

## Notes

- Never ask the user for Twitter cookies — they're already configured.
- For pages that need JS rendering, prefer `curl https://r.jina.ai/<URL>` over raw curl.
- Credentials are stored locally in `~/.agent-reach/config.yaml`, never uploaded.
