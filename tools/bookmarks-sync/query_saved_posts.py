#!/usr/bin/env python3
"""
Saved Posts & Collections - Fast Semantic & Keyword Query Tool
Description: Allows fast search and retrieval across saved posts
             by keyword, topic, author, or fuzzy semantic matching.
"""

import os
import sys
import json
import argparse
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = os.path.join(SCRIPT_DIR, "data/saved_posts.json")
DB_PATH = os.environ.get("SAVED_POSTS_DB", DEFAULT_DB)


def load_database():
    if not os.path.exists(DB_PATH):
        print(f"❌ Error: Database not found at {DB_PATH}")
        sys.exit(1)
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def search_posts(query: str, author: str = None, post_type: str = None, limit: int = 10):
    posts = load_database()
    terms = [t.lower() for t in query.split() if len(t) > 1]
    
    results = []
    
    for p in posts:
        caption = p.get("caption", "").lower()
        username = p.get("username", "").lower()
        full_name = p.get("full_name", "").lower()
        ptype = p.get("type", "").lower()
        
        if author and author.lower() not in username and author.lower() not in full_name:
            continue
            
        if post_type and post_type.lower() not in ptype:
            continue
            
        # Score relevance
        score = 0
        text_corpus = f"{caption} {username} {full_name}"
        
        for t in terms:
            if t in text_corpus:
                score += 10
            if t in caption:
                score += 15
            if t in username:
                score += 20
                
        # Regex exact phrase bonus
        if query.lower() in text_corpus:
            score += 50
            
        if score > 0:
            results.append((score, p))
            
    # Sort by relevance score
    results.sort(key=lambda x: x[0], reverse=True)
    return [p for score, p in results[:limit]]


def main():
    parser = argparse.ArgumentParser(description="Query Saved Posts Database")
    parser.add_argument("query", nargs="?", default="", help="Keywords or topic to search (e.g. 'shader', 'cursor', 'caching')")
    parser.add_argument("--author", "-a", default=None, help="Filter by creator username")
    parser.add_argument("--type", "-t", default=None, help="Filter by media type (Reel, Carousel, Image)")
    parser.add_argument("--limit", "-n", type=int, default=10, help="Maximum number of results to display")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    
    args = parser.parse_args()
    
    if not args.query and not args.author:
        parser.print_help()
        sys.exit(0)
        
    matches = search_posts(args.query, author=args.author, post_type=args.type, limit=args.limit)
    
    if args.json:
        print(json.dumps(matches, indent=2, ensure_ascii=False))
        return
        
    print(f"\n🔍 Found {len(matches)} relevant saved posts for query: '{args.query}'\n" + "="*65)
    
    for i, p in enumerate(matches, 1):
        cap_lines = [l.strip() for l in p.get("caption", "").split("\n") if l.strip()]
        snippet = cap_lines[0] if cap_lines else "No caption"
        if len(snippet) > 100:
            snippet = snippet[:97] + "..."
            
        print(f"\n[{i}] 👤 @{p.get('username', 'user')} ({p.get('full_name') or 'Creator'}) · [{p.get('type', 'Post')}]")
        print(f"    🔗 Link: {p.get('url', '')}")
        print(f"    📝 Summary: {snippet}")
        if len(cap_lines) > 1:
            more = " ".join(cap_lines[1:3])
            if len(more) > 120:
                more = more[:117] + "..."
            print(f"    💡 Details: {more}")
            
    print("\n" + "="*65 + "\n")


if __name__ == "__main__":
    main()
