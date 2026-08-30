#!/usr/bin/env python3
"""
Unified Cross-Platform Bookmarks, Notes & GitHub Stars Sync Engine
Author: Sanjeev Kumar S
Description: Automatically pulls saved items from LinkedIn, WhatsApp, and GitHub Stars,
             organizes/deduplicates against existing archives, syncs to native lists,
             and pushes updates to GitHub.
"""

import subprocess
import json
import time
import re
import os
import sys

BASE_DIR = "/home/sanjeev/dotfiles/docs-scripts"
LINKEDIN_FILE = os.path.join(BASE_DIR, "linkedin_bookmarks.json")
WHATSAPP_FILE = os.path.join(BASE_DIR, "whatsapp_self_notes.json")
GITHUB_STARS_JSON = os.path.join(BASE_DIR, "github_starred_lists.json")
GITHUB_STARS_MD = os.path.join(BASE_DIR, "github_starred_lists.md")
LOG_FILE = os.path.expanduser("~/.opencli/sync.log")

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

GITHUB_LIST_DEFINITIONS = [
    {
        "name": "AI & Autonomous Agents",
        "description": "Autonomous AI agents, LLM architectures, harness design, MCP servers, and cognitive workflows.",
        "keywords": ["agent", "mcp", "llm", "rag", "langchain", "langgraph", "autogpt", "crewai", "prompt", "transformer", "vllm", "ollama", "model-context-protocol", "claude", "gpt", "openai", "diffusion", "inference", "embedding", "fine-tuning", "deepseek", "anthropic", "copilot", "gemini", "whisper", "neural", "pytorch", "huggingface", "ai-"]
    },
    {
        "name": "Systems, OS & Compilers",
        "description": "Kernel development, embedded systems, RTOS, compilers, LLVM, WebAssembly, and low-level engineering.",
        "keywords": ["kernel", "operating system", "osdev", "driver", "firmware", "embedded", "compiler", "llvm", "ebpf", "wasm", "webassembly", "assembly", "emulator", "rtos", "zephyr", "linux", "qemu", "risc-v", "x86"]
    },
    {
        "name": "DevTools & Terminal CLI",
        "description": "High-efficiency developer tools, terminal user interfaces, shell configurations, and CLI engines.",
        "keywords": ["cli", "terminal", "devtools", "dotfiles", "shell", "zsh", "bash", "tmux", "neovim", "vim", "git", "opencli", "fastfetch", "tui", "productivity", "formatter", "linter"]
    },
    {
        "name": "Distributed Systems & Infra",
        "description": "Databases, consensus algorithms, high-throughput storage, networking, VPNs, and container infra.",
        "keywords": ["database", "distributed", "raft", "paxos", "postgres", "redis", "sqlite", "kafka", "storage", "cloud", "kubernetes", "docker", "networking", "network", "vpn", "wireguard", "proxy", "server", "microservice", "clickhouse", "s3"]
    },
    {
        "name": "Security & Reverse Engineering",
        "description": "Cybersecurity, reverse engineering, sandboxing, authentication, exploit research, and OpSec.",
        "keywords": ["security", "vulnerability", "hack", "pentest", "auth", "exploit", "reverse-engineering", "pwn", "cyber", "malware", "deobfuscate", "sandbox", "crypto", "opsec", "forensics"]
    },
    {
        "name": "Fullstack Web & UI Engineering",
        "description": "Modern frontend frameworks, UI components, Electron apps, design systems, and web architectures.",
        "keywords": ["react", "nextjs", "vue", "tailwind", "frontend", "ui", "css", "web", "svelte", "electron", "fullstack", "api", "shadcn", "radix", "canvas", "threejs", "webgl", "html5", "svg", "diagram"]
    },
    {
        "name": "CS Foundations & Curriculums",
        "description": "Computer science fundamentals, algorithm practice, interview roadmaps, papers, and books.",
        "keywords": ["algorithm", "leetcode", "interview", "cs", "curriculum", "education", "learning", "awesome", "papers", "book", "guide", "roadmap", "cheatsheet", "notes", "tutorial", "first-principle"]
    }
]

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{ts}] {msg}"
    print(entry)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry + "\n")

def run_opencli_eval(session, js_code):
    cmd = ['opencli', 'browser', session, 'eval', js_code]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        return {'error': res.stderr}
    lines = res.stdout.strip().split('\n')
    json_str = ''
    collect = False
    for l in lines:
        if l.startswith('{') or l.startswith('['):
            collect = True
        if collect:
            json_str += l + '\n'
    try:
        return json.loads(json_str.strip())
    except:
        return {'raw': res.stdout}

def sync_linkedin():
    log("Syncing LinkedIn saved posts...")
    subprocess.run(['opencli', 'browser', 'linkedin', 'open', 'https://www.linkedin.com/my-items/saved-posts/', '--window', 'background'], capture_output=True)
    time.sleep(4)

    for _ in range(3):
        run_opencli_eval('linkedin', 'window.scrollTo(0, document.body.scrollHeight);')
        time.sleep(1.5)

    raw_items = run_opencli_eval('linkedin', """
    (() => {
      const cards = Array.from(document.querySelectorAll('.workflow-results-container li')).filter(li => !li.classList.contains('search-reusables__primary-filter'));
      return cards.map((c, index) => {
        const text = c.innerText.trim();
        const lines = text.split('\\n').map(s => s.trim()).filter(Boolean);
        const allLinks = Array.from(c.querySelectorAll('a')).map(a => a.href);
        const postLink = allLinks.find(l => l.includes('/feed/update/') || l.includes('/posts/')) || allLinks.find(l => l.includes('/in/')) || '';
        const authorLink = allLinks.find(l => l.includes('/in/')) || '';
        const authorEl = c.querySelector('.entity-result__title-text a, a.app-aware-link, h3, .t-bold');
        const author = lines[0] || (authorEl ? authorEl.innerText.trim() : 'Unknown');
        const role = lines[3] || lines[2] || '';
        let postedAt = '';
        const timeMatch = lines.find(l => /^(\\d+[dwmy]|\\d+\\s*(day|week|month|year)s?\\s*ago)/i.test(l));
        if (timeMatch) postedAt = timeMatch;
        const snippet = lines.slice(4).join(' ');
        return { index: index + 1, author, author_profile: authorLink, role, posted_at: postedAt, snippet, post_url: postLink, raw_text: text };
      });
    })()
    """)

    if not isinstance(raw_items, list):
        log(f"LinkedIn extraction returned non-list: {raw_items}")
        return 0

    existing = {"bookmarks": []}
    if os.path.exists(LINKEDIN_FILE):
        with open(LINKEDIN_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)

    seen = {b.get('post_url') or (b.get('author', '') + b.get('content', '')[:30]) for b in existing.get('bookmarks', [])}
    new_count = 0

    for item in raw_items:
        dedup_key = item.get('post_url') or (item.get('author') + item.get('snippet')[:30])
        if dedup_key not in seen:
            seen.add(dedup_key)
            hashtags = re.findall(r'#([a-zA-Z0-9_-]+)', item.get('snippet', '') + ' ' + item.get('raw_text', ''))
            search_blob = f"{item.get('author')} {item.get('role')} {item.get('snippet')} {' '.join(hashtags)}".lower()
            existing['bookmarks'].insert(0, {
                "id": len(existing['bookmarks']) + 1,
                "author": item.get('author'),
                "author_profile": item.get('author_profile'),
                "author_headline": item.get('role'),
                "posted_at": item.get('posted_at'),
                "post_url": item.get('post_url'),
                "content": item.get('snippet'),
                "hashtags": list(set(hashtags)),
                "search_index": search_blob
            })
            new_count += 1

    for i, b in enumerate(existing['bookmarks']):
        b['id'] = i + 1

    existing['metadata'] = {
        "source": "LinkedIn Saved Posts & Bookmarks",
        "last_synced_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_bookmarks": len(existing['bookmarks']),
        "account_owner": "Sanjeev Kumar",
        "account_id": "1352024121"
    }

    with open(LINKEDIN_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)

    log(f"LinkedIn sync complete: {new_count} new bookmarks added (Total: {len(existing['bookmarks'])})")
    return new_count

def sync_whatsapp():
    log("Syncing WhatsApp self-messages...")
    
    # 1. Try high-speed native wacli first (0 browser overhead)
    wacli_bin = os.path.expanduser("~/.local/bin/wacli")
    if os.path.exists(wacli_bin):
        doc = subprocess.run([wacli_bin, 'doctor'], capture_output=True, text=True)
        if 'AUTHENTICATED     true' in doc.stdout:
            # Find self JID
            jid_match = re.search(r'LINKED_JID\s+([a-zA-Z0-9_@.-]+)', doc.stdout)
            self_jid = jid_match.group(1) if jid_match else "918925536470@s.whatsapp.net"
            
            res = subprocess.run([wacli_bin, 'messages', 'list', '--chat', self_jid, '--read-only', '--limit', '150', '--json'], capture_output=True, text=True)
            if res.returncode == 0:
                try:
                    data = json.loads(res.stdout)
                    msgs = data.get('data', {}).get('messages', [])
                    raw_items = []
                    for m in msgs:
                        text = (m.get('Text') or '').strip()
                        doc_title = (m.get('Filename') or '').strip()
                        content = text or doc_title
                        if content and (content.startswith('http') or 'pdf' in content.lower() or doc_title):
                            raw_items.append({
                                'meta': m.get('Timestamp', ''),
                                'content': content,
                                'docTitle': doc_title,
                                'links': [content] if content.startswith('http') else []
                            })
                    return process_and_save_whatsapp(raw_items, source="wacli (native)")
                except Exception as e:
                    log(f"wacli parse error: {e}")

    # 2. Fallback to OpenCLI browser bridge if wacli is unlinked
    log("Falling back to OpenCLI browser bridge for WhatsApp...")
    subprocess.run(['opencli', 'browser', 'whatsapp', 'open', 'https://web.whatsapp.com', '--window', 'background'], capture_output=True)
    time.sleep(4)

    run_opencli_eval('whatsapp', """
    (() => {
      const rows = Array.from(document.querySelectorAll('#pane-side [role=\"row\"], #pane-side [role=\"listitem\"], div[data-testid=\"cell-frame-container\"]'));
      const selfRow = rows.find(r => r.innerText.includes('(You)') || r.innerText.includes('You'));
      if (selfRow) {
        const clickTarget = selfRow.querySelector('div') || selfRow;
        clickTarget.click();
      }
    })()
    """)
    time.sleep(2)

    raw_msgs = run_opencli_eval('whatsapp', """
    (() => {
      const msgContainers = Array.from(document.querySelectorAll('[data-id], .message-in, .message-out, div[role=\"row\"]'));
      const extracted = [];
      for (const c of msgContainers) {
        const textEl = c.querySelector('.copyable-text, span.selectable-text, .selectable-text');
        const meta = c.querySelector('[data-pre-plain-text]')?.getAttribute('data-pre-plain-text') || '';
        const text = textEl ? textEl.innerText.trim() : '';
        const docTitle = c.querySelector('span[title], div[title]')?.getAttribute('title') || '';
        const links = Array.from(c.querySelectorAll('a')).map(a => a.href);
        const content = text || docTitle || links[0] || '';
        if (content && (content.includes('http') || content.toLowerCase().includes('pdf') || docTitle)) {
          extracted.push({ meta, content, docTitle, links });
        }
      }
      return extracted;
    })()
    """)

    if isinstance(raw_msgs, list):
        return process_and_save_whatsapp(raw_msgs, source="OpenCLI (browser)")
    return 0

def process_and_save_whatsapp(raw_msgs, source="WhatsApp"):
    existing = {"resources": []}
    if os.path.exists(WHATSAPP_FILE):
        with open(WHATSAPP_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)

    seen = {r.get('content') for r in existing.get('resources', [])}
    new_count = 0

    for item in raw_msgs:
        content = item.get('content', '').strip()
        if content and content not in seen:
            seen.add(content)
            meta = item.get('meta', '').strip()
            time_match = re.search(r'\[(.*?)\]', meta)
            timestamp = time_match.group(1) if time_match else meta
            urls = item.get('links', [])
            found_urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', content)
            all_urls = list(set(urls + found_urls))
            
            c = content.lower()
            if any(k in c for k in ['arxiv', 'alphaxiv', 'agents', 'ai', 'kv-cache', 'llm', 'cs229', 'vizuara', 'inference', 'k3']):
                category = 'AI & Agentic Systems'
            elif any(k in c for k in ['kernel', 'littleos', '539', 'rivet', 'internals-for-interns', 'complexsystems', 'origin.kernel']):
                category = 'Systems & OS Engineering'
            elif any(k in c for k in ['kleppmann', 'distributed', 'consensus', 'database']):
                category = 'Distributed Systems'
            elif any(k in c for k in ['teachyourselfcs', 'bradpenney', 'breakscale', 'interviewprep']):
                category = 'CS Fundamentals & Interview Prep'
            elif any(k in c for k in ['shoebpatel', 'hack-ai', 'techxiv', 'byern', 'lukata']):
                category = 'Security & DevTools'
            else:
                category = 'Reference / Spreadsheets'

            existing['resources'].insert(0, {
                "id": len(existing['resources']) + 1,
                "timestamp": timestamp,
                "category": category,
                "content": content,
                "urls": all_urls,
                "has_document": bool(item.get('docTitle')),
                "document_title": item.get('docTitle', ''),
                "search_index": f"{content} {category} {timestamp}".lower()
            })
            new_count += 1

    for i, r in enumerate(existing['resources']):
        r['id'] = i + 1

    existing['metadata'] = {
        "source": f"WhatsApp Self Notes ({source})",
        "last_synced_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_curated_resources": len(existing['resources']),
        "account_owner": "Sanjeev Kumar"
    }

    with open(WHATSAPP_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)

    log(f"WhatsApp sync complete via {source}: {new_count} new notes added (Total: {len(existing['resources'])})")
    return new_count

def categorize_github_repo(r):
    text = (r.get('full_name', '') + ' ' + (r.get('description') or '') + ' ' + ' '.join(r.get('topics') or [])).lower()
    lang = (r.get('language') or '').lower()
    
    best_cat = None
    max_score = 0
    for defn in GITHUB_LIST_DEFINITIONS:
        score = 0
        for kw in defn['keywords']:
            if kw in text:
                score += 10
            if r.get('topics') and any(kw in t.lower() for t in r.get('topics')):
                score += 15
        if score > max_score:
            max_score = score
            best_cat = defn['name']
            
    if not best_cat or max_score == 0:
        if lang in ['c', 'rust', 'c++', 'assembly']:
            best_cat = 'Systems, OS & Compilers'
        elif lang in ['typescript', 'javascript', 'html', 'css']:
            best_cat = 'Fullstack Web & UI Engineering'
        elif lang in ['python', 'jupyter notebook']:
            best_cat = 'AI & Autonomous Agents'
        else:
            best_cat = 'DevTools & Terminal CLI'
    return best_cat

def sync_github_stars():
    log("Syncing GitHub starred repositories...")
    res = subprocess.run(['gh', 'api', 'user/starred?per_page=30'], capture_output=True, text=True)
    if res.returncode != 0:
        log(f"GitHub API error: {res.stderr}")
        return 0

    recent_stars = json.loads(res.stdout)
    
    existing = {"lists": []}
    if os.path.exists(GITHUB_STARS_JSON):
        with open(GITHUB_STARS_JSON, "r", encoding="utf-8") as f:
            existing = json.load(f)

    seen_repos = set()
    for l in existing.get("lists", []):
        for r in l.get("repositories", []):
            seen_repos.add(r.get("full_name"))

    new_repos = [r for r in recent_stars if r.get("full_name") not in seen_repos]
    if not new_repos:
        log("No newly starred repositories detected.")
        return 0

    log(f"Detected {len(new_repos)} newly starred repositories. Fetching GitHub List IDs...")
    
    # Query list IDs via GraphQL
    list_query = 'query { viewer { lists(first: 20) { nodes { id name } } } }'
    gql_res = subprocess.run(['gh', 'api', 'graphql', '--input', '-'], input=json.dumps({"query": list_query}), capture_output=True, text=True)
    list_map = {}
    if gql_res.returncode == 0:
        data = json.loads(gql_res.stdout)
        list_map = {node["name"]: node["id"] for node in data.get("data", {}).get("viewer", {}).get("lists", {}).get("nodes", [])}

    for r in new_repos:
        cat = categorize_github_repo(r)
        target_list_id = list_map.get(cat)
        repo_id = r.get("node_id")
        
        # Add to native GitHub list
        if target_list_id and repo_id:
            assign_query = {
                "query": "mutation($itemId: ID!, $listIds: [ID!]!) { updateUserListsForItem(input: {itemId: $itemId, listIds: $listIds}) { clientMutationId } }",
                "variables": {"itemId": repo_id, "listIds": [target_list_id]}
            }
            subprocess.run(['gh', 'api', 'graphql', '--input', '-'], input=json.dumps(assign_query), capture_output=True)

        # Add to local structure
        for l in existing.get("lists", []):
            if l.get("name") == cat:
                l["repositories"].insert(0, {
                    "full_name": r["full_name"],
                    "url": r["html_url"],
                    "description": r.get("description") or "",
                    "language": r.get("language") or "Unknown",
                    "stars": r.get("stargazers_count", 0),
                    "topics": r.get("topics", [])
                })
                l["count"] = len(l["repositories"])

    # Update metadata
    total_starred = sum(l["count"] for l in existing.get("lists", []))
    existing["metadata"] = {
        "source": "GitHub Stars (sanjeevafk)",
        "total_starred": total_starred,
        "last_synced_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "categories": {l["name"]: l["count"] for l in existing.get("lists", [])}
    }

    with open(GITHUB_STARS_JSON, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)

    # Regenerate markdown
    with open(GITHUB_STARS_MD, "w", encoding="utf-8") as f:
        f.write("# 🌟 GitHub Starred Repositories - Curated Collections\n\n")
        f.write(f"> **Account:** [@sanjeevafk](https://github.com/sanjeevafk) | **Total Starred:** {total_starred} | **Last Updated:** {time.strftime('%B %d, %Y')}\n\n")
        for l in existing.get("lists", []):
            f.write(f"## {l['name']} ({l['count']} repositories)\n\n")
            f.write(f"*{l.get('description', '')}*\n\n")
            for repo in sorted(l.get("repositories", []), key=lambda x: x.get("stars", 0), reverse=True):
                desc = (repo.get("description") or "No description provided").strip().replace("\n", " ")
                lang = f" `{repo.get('language')}`" if repo.get("language") else ""
                f.write(f"- [**{repo['full_name']}**]({repo['url']}){lang} (★ {repo.get('stars', 0):,}) — {desc}\n")
            f.write("\n---\n\n")

    log(f"GitHub Stars sync complete: {len(new_repos)} new repos categorized and synced (Total: {total_starred})")
    return len(new_repos)

def git_push_if_changed(total_new):
    if total_new == 0:
        log("No new items to push to GitHub.")
        return
    log(f"Pushing {total_new} new items to GitHub dotfiles repo...")
    cwd = "/home/sanjeev/dotfiles"
    subprocess.run(['git', 'add', 'docs-scripts/linkedin_bookmarks.json', 'docs-scripts/whatsapp_self_notes.json', 'docs-scripts/github_starred_lists.json', 'docs-scripts/github_starred_lists.md'], cwd=cwd)
    subprocess.run(['git', 'commit', '-m', f"chore(sync): automated sync of {total_new} new bookmarks/notes/stars"], cwd=cwd)
    res = subprocess.run(['git', 'push', 'origin', 'main'], cwd=cwd, capture_output=True, text=True)
    if res.returncode == 0:
        log("Successfully pushed updates to GitHub.")
    else:
        log(f"Git push warning/error: {res.stderr}")

def main():
    log("=== Starting Unified Cross-Platform Sync Job ===")
    
    # 1. Sync GitHub Stars
    new_gh = sync_github_stars()

    # 2. Sync LinkedIn & WhatsApp via OpenCLI
    new_li = 0
    new_wa = 0
    doc = subprocess.run(['opencli', 'doctor'], capture_output=True, text=True)
    if 'connected' in doc.stdout:
        new_li = sync_linkedin()
        new_wa = sync_whatsapp()
    else:
        log("Notice: OpenCLI browser extension not connected. Skipping browser-based sync for LinkedIn/WhatsApp.")

    git_push_if_changed(new_gh + new_li + new_wa)
    log("=== Sync Job Finished ===")

if __name__ == "__main__":
    main()
