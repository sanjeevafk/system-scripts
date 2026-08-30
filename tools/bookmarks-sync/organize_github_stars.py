#!/usr/bin/env python3
"""
Populate Native GitHub Star Lists via GraphQL
Author: VoidCommit / Sanjeev Kumar S
Description: Dynamically fetches your starred GitHub repos, categorizes them,
             and assigns them to native GitHub Star Lists via GraphQL.
"""

import subprocess
import json
import time
import sys

LIST_DEFINITIONS = [
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

def run_graphql(query_str, variables=None):
    payload = {"query": query_str}
    if variables:
        payload["variables"] = variables
    res = subprocess.run(['gh', 'api', 'graphql', '--input', '-'], input=json.dumps(payload), text=True, capture_output=True)
    if res.returncode != 0:
        return {"error": res.stderr}
    try:
        return json.loads(res.stdout)
    except:
        return {"raw": res.stdout}

def fetch_existing_lists():
    query = """
    query {
      viewer {
        lists(first: 30) {
          nodes {
            id
            name
            description
          }
        }
      }
    }
    """
    res = run_graphql(query)
    lists = res.get("data", {}).get("viewer", {}).get("lists", {}).get("nodes", [])
    return {l["name"]: l["id"] for l in lists}

def create_list(name, description):
    query = """
    mutation($name: String!, $description: String!) {
      createUserList(input: {name: $name, description: $description, isPrivate: false}) {
        list {
          id
          name
        }
      }
    }
    """
    res = run_graphql(query, {"name": name, "description": description})
    lst = res.get("data", {}).get("createUserList", {}).get("list")
    if lst:
        return lst["id"]
    print(f"Failed to create list {name}: {res}")
    return None

def add_repo_to_list(repo_id, list_id):
    query = """
    mutation($itemId: ID!, $listIds: [ID!]!) {
      updateUserListsForItem(input: {itemId: $itemId, listIds: $listIds}) {
        clientMutationId
      }
    }
    """
    return run_graphql(query, {"itemId": repo_id, "listIds": [list_id]})

def categorize_repo(r):
    text = (r.get('full_name', '') + ' ' + (r.get('description') or '') + ' ' + ' '.join(r.get('topics') or [])).lower()
    lang = (r.get('language') or '').lower()
    
    best_cat = None
    max_score = 0
    for defn in LIST_DEFINITIONS:
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

def main():
    print("=== Populating Native GitHub Star Lists ===")
    
    # Fetch all starred repos directly from GitHub CLI
    print("Fetching starred repositories from GitHub...")
    res = subprocess.run(['gh', 'api', 'user/starred?per_page=100', '--paginate'], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error fetching stars: {res.stderr}")
        sys.exit(1)
        
    repos = json.loads(res.stdout)
    print(f"Loaded {len(repos)} starred repositories.")
    
    existing_lists = fetch_existing_lists()
    print(f"Existing lists on GitHub: {list(existing_lists.keys())}")
    
    list_id_map = {}
    for defn in LIST_DEFINITIONS:
        name = defn["name"]
        if name in existing_lists:
            list_id_map[name] = existing_lists[name]
            print(f"Using list '{name}' ({list_id_map[name]})")
        else:
            print(f"Creating list on GitHub: '{name}'...")
            new_id = create_list(name, defn["description"])
            if new_id:
                list_id_map[name] = new_id
                print(f" Created list '{name}' -> {new_id}")
            time.sleep(0.5)
            
    print(f"\nAll 7 Lists Ready: {list_id_map}")
    print(f"\nAssigning {len(repos)} repositories into their GitHub Star Lists...")
    
    success_count = 0
    error_count = 0
    
    for idx, r in enumerate(repos, 1):
        cat = categorize_repo(r)
        target_list_id = list_id_map.get(cat)
        repo_id = r.get('node_id')
        
        if target_list_id and repo_id:
            res = add_repo_to_list(repo_id, target_list_id)
            if 'error' in res or (res.get('errors')):
                error_count += 1
                print(f"[{idx}/{len(repos)}] ❌ Error {r['full_name']} -> {cat}")
            else:
                success_count += 1
                if idx % 10 == 0 or idx == len(repos):
                    print(f"[{idx}/{len(repos)}]  Synced {r['full_name']} -> [{cat}]")
        time.sleep(0.15)
        
    print(f"\n=== Organization Complete! ===")
    print(f"Successfully assigned {success_count} repositories across 7 lists on GitHub.")
    if error_count > 0:
        print(f"Errors encountered: {error_count}")

if __name__ == "__main__":
    main()
