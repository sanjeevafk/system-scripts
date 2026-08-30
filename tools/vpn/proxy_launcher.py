#!/usr/bin/env python3
"""
proxy_launcher.py — Fast multi-threaded residential/HTTP proxy finder and process launcher.
Finds low-latency proxy servers and executes any command routed through them.
"""
from __future__ import annotations

import concurrent.futures
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

CACHE_FILE = os.path.expanduser("~/.proxy_launcher_cache.json")

PROXY_SOURCES = [
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
]

def test_proxy(proxy: str) -> dict | None:
    proxy_url = f"http://{proxy}"
    proxy_handler = urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url})
    opener = urllib.request.build_opener(proxy_handler)
    try:
        start_time = time.time()
        req = urllib.request.Request("https://cloudflare.com", headers={"User-Agent": "Mozilla/5.0"})
        res = opener.open(req, timeout=3)
        latency = round((time.time() - start_time) * 1000)
        if res.status == 200:
            req_ip = urllib.request.Request("https://ipinfo.io/json", headers={"User-Agent": "curl/7.68.0"})
            res_ip = opener.open(req_ip, timeout=3)
            data = json.loads(res_ip.read().decode("utf-8"))
            country = data.get("country", "")
            org = data.get("org", "")
            if country in ["US", "CA", "GB", "DE", "FR", "NL"]:
                return {"proxy": proxy, "country": country, "org": org, "latency": latency}
    except Exception:
        pass
    return None

def get_working_proxy() -> str | None:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                cached = json.load(f)
                proxy_info = cached.get("proxy_info")
                if proxy_info and (time.time() - cached.get("timestamp", 0) < 3600):
                    res = test_proxy(proxy_info["proxy"])
                    if res:
                        print(f"[+] Using cached proxy: {res['proxy']} [{res['country']}] ({res['org']}) - {res['latency']}ms")
                        return res["proxy"]
        except Exception:
            pass

    print("[*] Finding high-speed HTTP proxy...")
    all_proxies: list[str] = []
    for src in PROXY_SOURCES:
        try:
            req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
            data = urllib.request.urlopen(req, timeout=4).read().decode("utf-8").splitlines()
            all_proxies.extend([line.strip() for line in data if ":" in line])
        except Exception:
            pass

    all_proxies = list(set(all_proxies))
    print(f"[*] Testing {len(all_proxies[:300])} proxies...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=35) as executor:
        futures = [executor.submit(test_proxy, p) for p in all_proxies[:300]]
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                print(f"[+] Found working proxy: {res['proxy']} [{res['country']}] ({res['org']}) - {res['latency']}ms")
                try:
                    with open(CACHE_FILE, "w") as f:
                        json.dump({"proxy_info": res, "timestamp": time.time()}, f)
                except Exception:
                    pass
                executor.shutdown(wait=False, cancel_futures=True)
                return res["proxy"]

    return None

def main():
    if len(sys.argv) < 2:
        print("Usage: proxy_launcher.py <command> [args...]")
        print("Example: proxy_launcher.py curl https://ifconfig.me")
        sys.exit(1)

    proxy = get_working_proxy()
    env = os.environ.copy()
    if proxy:
        env["HTTP_PROXY"] = f"http://{proxy}"
        env["HTTPS_PROXY"] = f"http://{proxy}"
        env["http_proxy"] = f"http://{proxy}"
        env["https_proxy"] = f"http://{proxy}"
        print(f"[+] Routing command through proxy: {proxy}\n")
    else:
        print("[-] Warning: No working proxy found. Running with direct connection...\n")

    cmd = sys.argv[1]
    binary = shutil.which(cmd) or cmd
    args = [cmd] + sys.argv[2:]
    os.execvpe(binary, args, env)

if __name__ == "__main__":
    main()
