# Network Namespace & VPN Isolation Kit

A production-grade Linux network engineering kit designed to isolate, route, and test applications through isolated network namespaces, WireGuard tunnels, and proxy circuits without affecting the host operating system.

---

## Directory Structure

```text
vpn/
├── README.md           # Documentation & architectural overview
├── vpn_namespace.py    # Production Linux network namespace WireGuard orchestrator
└── proxy_launcher.py   # Multi-threaded HTTP/residential proxy auto-finder & launcher
```

---

## Components

### 1. Network Namespace Orchestrator (`vpn_namespace.py`)
A production-grade Python CLI tool that builds an isolated Linux network namespace (`vpn_ns`) running native WireGuard:

* **Host Isolation:** Host default routing table, interfaces (`eth0`/`wlan0`), and general internet access remain 100% untouched.
* **Dynamic Subnet Selection:** Automatically inspects host routing tables and selects an unallocated RFC1918 subnet (`192.168.100.0/24` to `192.168.250.0/24`) for `veth` linking.
* **Host NAT & Whitelisting:** Configures `nftables`/`iptables` masquerading and inserts explicit forwarding whitelist rules at the top of the host `FORWARD` chain to bypass default `DROP` policies.
* **Strict Kill-Switch:** Configures a default `DROP` policy inside `vpn_ns`. Traffic can *only* leave the namespace via `wg0` or through the encrypted WireGuard UDP endpoint port on `veth-ns`. If the VPN drops, all traffic in the namespace is immediately blocked to prevent leaks.
* **Kernel Handshake Verification:** Queries `wg show wg0 latest-handshakes` to confirm an active cryptographic handshake exchange before declaring success.
* **Robust Rollback:** Employs `try/finally` block management to restore `net.ipv4.ip_forward` sysctl values and tear down virtual links automatically if setup fails.

### 2. Smart Proxy Launcher (`proxy_launcher.py`)
A multi-threaded Python launcher that fetches, tests, and caches high-speed HTTP/Residential ISP proxies and executes target commands routed through `HTTP_PROXY` / `HTTPS_PROXY` environment variables.

---

## Usage

### WireGuard Network Namespace Orchestrator

```bash
# Start namespace using a WireGuard configuration file
sudo python3 vpn_namespace.py start /path/to/wg0.conf

# Execute any command inside the VPN namespace as your normal user
sudo ip netns exec vpn_ns runuser -u $USER -- curl https://ipinfo.io

# Stop the VPN namespace and restore host network rules
sudo python3 vpn_namespace.py stop
```

### Proxy Launcher

```bash
# Execute any command routed through a low-latency proxy
./proxy_launcher.py curl https://ifconfig.me
./proxy_launcher.py python3 my_script.py
```
