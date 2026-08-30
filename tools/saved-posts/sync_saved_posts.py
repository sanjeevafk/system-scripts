#!/usr/bin/env python3
"""
Agent Reach - High-Speed Multi-Platform Saved Bookmarks Sync Hook
Description: Incrementally syncs saved posts and videos from Instagram, YouTube Watch Later,
             and Twitter into the unified ~/.agent-reach/data/saved_bookmarks.json library.
"""

import os
import sys
import json
import time
import hashlib
import re

try:
    from curl_cffi import requests
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False
    import requests

DATA_PATH = os.path.expanduser("~/.agent-reach/data/saved_bookmarks.json")
CONFIG_PATH = os.path.expanduser("~/.agent-reach/config.yaml")


def load_config_val(key_name):
    env_val = os.getenv(key_name.upper())
    if env_val:
        return env_val
        
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            content = f.read()
            m = re.search(rf'{key_name}:\s*"([^"]+)"|{key_name}:\s*\'([^\']+)\'|{key_name}:\s*([^\n]+)', content)
            if m:
                return (m.group(1) or m.group(2) or m.group(3)).strip()
    return None


def sync_instagram():
    print("\n📸 [Instagram] Checking for new saved posts...")
    cookie = load_config_val("instagram_cookie")
    if not cookie:
        print("  ⚠️ No Instagram cookie found in config.")
        return []

    csrf_m = re.search(r'csrftoken=([^;]+)', cookie)
    csrf_token = csrf_m.group(1) if csrf_m else ""

    headers = {
        "Cookie": cookie,
        "Referer": "https://www.instagram.com/",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "X-CSRFToken": csrf_token,
        "X-IG-App-ID": "936619743392459",
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "*/*"
    }

    seen_ids = set()
    existing_posts = []
    if os.path.exists(DATA_PATH):
        try:
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                existing_posts = json.load(f)
                for p in existing_posts:
                    if p.get("platform") == "instagram" or "instagram.com" in p.get("url", ""):
                        seen_ids.add(str(p.get("id")))
                        seen_ids.add(str(p.get("code")))
        except Exception:
            pass

    new_posts = []
    max_id = None
    page = 0
    hit_existing = False

    while not hit_existing and page < 10:
        page += 1
        url = "https://www.instagram.com/api/v1/feed/saved/posts/"
        if max_id:
            url += f"?max_id={max_id}"

        try:
            req_kwargs = {"headers": headers, "timeout": 20}
            if HAS_CURL_CFFI:
                req_kwargs["impersonate"] = "chrome120"
            r = requests.get(url, **req_kwargs)
            if r.status_code != 200:
                break
            data = r.json()
            items = data.get("items", [])
            if not items:
                break

            for it in items:
                media = it.get("media", it)
                media_id = str(media.get("id"))
                code = media.get("code")

                if media_id in seen_ids or code in seen_ids:
                    hit_existing = True
                    break

                seen_ids.add(media_id)
                media_type = "Reel" if media.get("media_type") == 2 else ("Carousel" if media.get("media_type") == 8 else "Image")
                user = media.get("user", {})
                username = user.get("username", "Unknown")
                full_name = user.get("full_name", "")

                cap_obj = media.get("caption")
                caption = cap_obj.get("text", "") if cap_obj else ""
                url_link = f"https://www.instagram.com/reel/{code}/" if media_type == "Reel" else f"https://www.instagram.com/p/{code}/"

                new_posts.append({
                    "platform": "instagram",
                    "code": code,
                    "url": url_link,
                    "username": username,
                    "full_name": full_name,
                    "type": media_type,
                    "caption": caption.strip(),
                    "id": media_id,
                    "synced_at": time.strftime("%Y-%m-%d %H:%M:%S")
                })

            max_id = data.get("next_max_id")
            if not max_id or not data.get("more_available"):
                break
            time.sleep(0.5)
        except Exception:
            break

    print(f"  ✅ Instagram: {len(new_posts)} new items synced.")
    return new_posts


def sync_youtube():
    print("\n🎥 [YouTube] Checking Watch Later playlist...")
    cookie = load_config_val("youtube_cookie")
    if not cookie:
        print("  ⚠️ No YouTube cookie found in config.")
        return []

    sapisid_m = re.search(r'SAPISID=([^;]+)', cookie)
    sapisid = sapisid_m.group(1) if sapisid_m else ""
    now_sec = int(time.time())
    sapisid_hash = hashlib.sha1(f"{now_sec} {sapisid} https://www.youtube.com".encode()).hexdigest()

    headers = {
        "Cookie": cookie,
        "Authorization": f"SAPISIDHASH {now_sec}_{sapisid_hash}",
        "X-Origin": "https://www.youtube.com",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "X-YouTube-Client-Name": "1",
        "X-YouTube-Client-Version": "2.20260805.01.00"
    }

    seen_ids = set()
    if os.path.exists(DATA_PATH):
        try:
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                for p in json.load(f):
                    if p.get("platform") == "youtube" or "youtube.com" in p.get("url", ""):
                        seen_ids.add(str(p.get("id")))
        except Exception:
            pass

    new_vids = []
    continuation_token = None
    page = 0
    hit_existing = False

    while not hit_existing and page < 5:
        page += 1
        url = "https://www.youtube.com/youtubei/v1/browse?prettyPrint=false"
        payload = {
            "context": {"client": {"clientName": "WEB", "clientVersion": "2.20260805.01.00", "hl": "en", "gl": "IN"}}
        }
        if continuation_token:
            payload["continuation"] = continuation_token
        else:
            payload["browseId"] = "VLWL"

        try:
            req_kwargs = {"json": payload, "headers": headers, "timeout": 20}
            if HAS_CURL_CFFI:
                req_kwargs["impersonate"] = "chrome120"
            r = requests.post(url, **req_kwargs)
            if r.status_code != 200:
                break
            data = r.json()
            extracted_this_page = []
            tokens = []

            def parse_node(obj):
                nonlocal hit_existing
                if isinstance(obj, dict):
                    if "playlistVideoRenderer" in obj:
                        renderer = obj["playlistVideoRenderer"]
                        vid = renderer.get("videoId")
                        if vid in seen_ids:
                            hit_existing = True
                            return
                        seen_ids.add(vid)
                        title = renderer.get("title", {}).get("runs", [{}])[0].get("text", "Untitled")
                        channel = renderer.get("shortBylineText", {}).get("runs", [{}])[0].get("text", "Unknown Channel")
                        length = renderer.get("lengthText", {}).get("simpleText", "")
                        
                        extracted_this_page.append({
                            "platform": "youtube",
                            "code": vid,
                            "id": vid,
                            "url": f"https://www.youtube.com/watch?v={vid}",
                            "title": title,
                            "caption": f"{title} — by {channel} ({length})",
                            "username": channel,
                            "full_name": channel,
                            "type": "Video",
                            "duration": length,
                            "synced_at": time.strftime("%Y-%m-%d %H:%M:%S")
                        })
                    elif "continuationCommand" in obj:
                        tokens.append(obj["continuationCommand"].get("token"))
                    elif "nextContinuationData" in obj:
                        tokens.append(obj["nextContinuationData"].get("continuation"))
                    
                    for k, v in obj.items():
                        parse_node(v)
                elif isinstance(obj, list):
                    for item in obj:
                        parse_node(item)

            parse_node(data)
            new_vids.extend(extracted_this_page)
            continuation_token = tokens[0] if tokens else None
            if not continuation_token or len(extracted_this_page) == 0:
                break
            time.sleep(0.5)
        except Exception:
            break

    print(f"  ✅ YouTube: {len(new_vids)} new items synced.")
    return new_vids


def main():
    print("🚀 Starting Unified Multi-Platform Bookmarks Sync...")
    
    existing_all = []
    if os.path.exists(DATA_PATH):
        try:
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                existing_all = json.load(f)
        except Exception:
            pass

    ig_new = sync_instagram()
    yt_new = sync_youtube()

    total_new = (ig_new or []) + (yt_new or [])
    
    if total_new:
        combined = total_new + existing_all
        os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(combined, f, indent=2, ensure_ascii=False)
        print(f"\n🎉 Sync Complete! Added {len(total_new)} new items. Total Library: {len(combined)} bookmarks.")
    else:
        print(f"\n✅ All platforms up to date. Total Library: {len(existing_all)} bookmarks.")


if __name__ == "__main__":
    main()
