#!/usr/bin/env python3
"""
vpn_namespace.py

A production-grade, secure network namespace orchestration script designed to run
isolated applications (such as browsers, bots, or CLI tools) through a WireGuard tunnel.

This script implements:
1. Unused RFC1918 subnet detection to prevent collisions with the host.
2. Network namespaces (vpn_ns) and virtual ethernet pairs (veth).
3. System forwarding restoration (reads and restores net.ipv4.ip_forward).
4. Dual firewall support (native nftables with isolated tables, falling back to iptables).
5. Dynamic namespace kill-switch (iptables inside the namespace) preventing IP leaks.
6. Handshake verification via the native WireGuard command (wg show).
7. Single-command user execution using 'runuser' instead of nested 'sudo'.
8. Robust try/finally failure rollbacks.
9. Whitelisting host forwarding rules to bypass default DROP policies.
"""

import sys
import os
import re
import socket
import subprocess
import shutil
import time

NAMESPACE = "vpn_ns"
INTERFACE = "wg0"
VETH_HOST = "veth-host"
VETH_NS = "veth-ns"

# State files to persist dynamic runtime values between start/stop sessions
FORWARD_STATE_FILE = "/tmp/vpn_namespace_forward.state"
SUBNET_STATE_FILE = "/tmp/vpn_namespace_subnet.state"

def run_cmd(args, check=True, input_data=None):
    """Executes a command safely using subprocess argument lists to prevent shell injection."""
    try:
        res = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            input=input_data
        )
        if check and res.returncode != 0:
            print(f"[-] Command failed: {' '.join(args)}")
            print(f"    Stdout: {res.stdout.strip()}")
            print(f"    Stderr: {res.stderr.strip()}")
            raise subprocess.CalledProcessError(res.returncode, args, output=res.stdout, stderr=res.stderr)
        return res
    except Exception as e:
        if check:
            print(f"[-] Execution error running command {' '.join(args)}: {e}")
            raise e
        return None

def get_firewall_provider():
    """Detects whether modern nftables is available or if we must fall back to legacy iptables."""
    nft_check = subprocess.run(["which", "nft"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return "nftables" if nft_check.returncode == 0 else "iptables"

def find_unused_subnet():
    """Scans host routing tables to find an unused /24 subnet in the 192.168.X.0 range."""
    res = subprocess.run(["ip", "route"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    routes = res.stdout if res.returncode == 0 else ""
    
    # Try 192.168.100.0/24 to 192.168.250.0/24
    for x in range(100, 251):
        candidate_subnet = f"192.168.{x}.0/24"
        candidate_prefix = f"192.168.{x}."
        if candidate_prefix not in routes:
            return candidate_subnet
    return "192.168.99.0/24"  # Default fallback

def parse_conf(conf_path):
    """Parses a WireGuard .conf file and extracts required network parameters."""
    try:
        with open(conf_path, 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"[-] Error: Failed to read WireGuard config file {conf_path}: {e}")
        sys.exit(1)
    
    def find_val(pattern, text):
        m = re.search(pattern, text, re.IGNORECASE)
        return m.group(1).strip() if m else None

    # Split config into [Interface] and [Peer] sections
    sections = re.split(r'\[(interface|peer)\]', content, flags=re.IGNORECASE)
    
    interface_text = ""
    peer_text = ""
    for i in range(1, len(sections), 2):
        sec_name = sections[i].lower()
        sec_content = sections[i+1]
        if sec_name == "interface":
            interface_text = sec_content
        elif sec_name == "peer":
            peer_text = sec_content

    private_key = find_val(r'PrivateKey\s*=\s*(.+)', interface_text)
    address = find_val(r'Address\s*=\s*(.+)', interface_text)
    dns = find_val(r'DNS\s*=\s*(.+)', interface_text)
    
    public_key = find_val(r'PublicKey\s*=\s*(.+)', peer_text)
    endpoint = find_val(r'Endpoint\s*=\s*(.+)', peer_text)
    allowed_ips = find_val(r'AllowedIPs\s*=\s*(.+)', peer_text)

    if not all([private_key, address, public_key, endpoint]):
        print("[-] Error: Missing required fields in config (PrivateKey, Address, PublicKey, Endpoint).")
        sys.exit(1)

    # Resolve Endpoint hostnames to IP addresses to avoid DNS lookup loops in netns
    endpoint_host, endpoint_port = endpoint.rsplit(":", 1)
    try:
        endpoint_ip = socket.gethostbyname(endpoint_host)
        resolved_endpoint = f"{endpoint_ip}:{endpoint_port}"
    except Exception as e:
        print(f"[-] Error: Could not resolve endpoint hostname {endpoint_host}: {e}")
        sys.exit(1)

    return {
        "private_key": private_key,
        "address": address,
        "dns": dns or "1.1.1.1",
        "public_key": public_key,
        "endpoint_ip": endpoint_ip,
        "endpoint_port": endpoint_port,
        "resolved_endpoint": resolved_endpoint,
        "allowed_ips": allowed_ips or "0.0.0.0/0"
    }

def verify_handshake():
    """Polls the WireGuard state inside the namespace to verify a completed handshake."""
    print("[*] Verifying WireGuard handshake inside namespace...")
    for _ in range(8):
        time.sleep(1.5)
        res = subprocess.run(
            ["ip", "netns", "exec", NAMESPACE, "wg", "show", INTERFACE, "latest-handshakes"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        if res.returncode == 0:
            try:
                parts = res.stdout.strip().split()
                if parts:
                    timestamp = int(parts[-1])
                    if timestamp > 0:
                        # Grab transfer counters as well
                        t_res = subprocess.run(
                            ["ip", "netns", "exec", NAMESPACE, "wg", "show", INTERFACE, "transfer"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                        )
                        transfer_info = t_res.stdout.strip() if t_res.returncode == 0 else "unknown"
                        print(f"[+] Handshake verified! Latest handshake timestamp: {timestamp}")
                        print(f"[+] Interface Transfer metrics: {transfer_info}")
                        return True
            except (ValueError, IndexError):
                pass
    return False

def apply_kill_switch(endpoint_ip, endpoint_port):
    """Applies strict local firewall rules inside the namespace to block all leaks if tunnel drops."""
    print("[+] --- Configuring Namespace Kill-Switch (Firewall) ---")
    
    # 1. Flush existing namespace firewall rules
    run_cmd(["ip", "netns", "exec", NAMESPACE, "iptables", "-F"])
    run_cmd(["ip", "netns", "exec", NAMESPACE, "iptables", "-X"])
    
    # 2. Drop everything by default (strict default-deny policy)
    run_cmd(["ip", "netns", "exec", NAMESPACE, "iptables", "-P", "INPUT", "DROP"])
    run_cmd(["ip", "netns", "exec", NAMESPACE, "iptables", "-P", "FORWARD", "DROP"])
    run_cmd(["ip", "netns", "exec", NAMESPACE, "iptables", "-P", "OUTPUT", "DROP"])
    
    # 3. Allow loopback traffic
    run_cmd(["ip", "netns", "exec", NAMESPACE, "iptables", "-A", "INPUT", "-i", "lo", "-j", "ACCEPT"])
    run_cmd(["ip", "netns", "exec", NAMESPACE, "iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"])
    
    # 4. Allow all traffic over the wireguard tunnel interface
    run_cmd(["ip", "netns", "exec", NAMESPACE, "iptables", "-A", "INPUT", "-i", INTERFACE, "-j", "ACCEPT"])
    run_cmd(["ip", "netns", "exec", NAMESPACE, "iptables", "-A", "OUTPUT", "-o", INTERFACE, "-j", "ACCEPT"])
    
    # 5. Allow ONLY encrypted WireGuard UDP handshake packets to/from veth-ns
    run_cmd([
        "ip", "netns", "exec", NAMESPACE, "iptables", "-A", "OUTPUT", 
        "-o", VETH_NS, "-d", endpoint_ip, "-p", "udp", "--dport", endpoint_port, "-j", "ACCEPT"
    ])
    run_cmd([
        "ip", "netns", "exec", NAMESPACE, "iptables", "-A", "INPUT", 
        "-i", VETH_NS, "-s", endpoint_ip, "-p", "udp", "--sport", endpoint_port, "-j", "ACCEPT"
    ])
    
    # 6. Log dropped packets inside namespace for debugging
    run_cmd(["ip", "netns", "exec", NAMESPACE, "iptables", "-A", "INPUT", "-j", "LOG", "--log-prefix", "NS_DROP_IN: "])
    run_cmd(["ip", "netns", "exec", NAMESPACE, "iptables", "-A", "OUTPUT", "-j", "LOG", "--log-prefix", "NS_DROP_OUT: "])

def start(conf_path):
    if os.getuid() != 0:
        print("[*] Script requires root privileges. Escalating via sudo...")
        os.execvp("sudo", ["sudo", "python3"] + sys.argv)

    if not os.path.exists(conf_path):
        print(f"[-] Config file not found: {conf_path}")
        sys.exit(1)
        
    cfg = parse_conf(conf_path)
    
    # Pre-cleanup in case of a dirty state from previous executions
    stop_vpn(silent=True)
    
    # Auto-detect unused RFC1918 subnet
    subnet = find_unused_subnet()
    subnet_prefix = subnet.rsplit(".", 1)[0]
    host_ip = f"{subnet_prefix}.1"
    ns_ip = f"{subnet_prefix}.2"
    mask = "24"
    
    print(f"[+] Selected unused subnet: {subnet}")
    
    # Persist the chosen subnet so the stop command knows which NAT rules to delete
    with open(SUBNET_STATE_FILE, "w") as f:
        f.write(subnet)
        
    # Read and store original host forwarding state
    try:
        res = subprocess.run(["sysctl", "-n", "net.ipv4.ip_forward"], stdout=subprocess.PIPE, text=True)
        orig_forward = res.stdout.strip()
    except Exception:
        orig_forward = "0"
    with open(FORWARD_STATE_FILE, "w") as f:
        f.write(orig_forward)

    success = False
    try:
        print("[+] --- Step 1: Initializing Isolated Network Namespace ---")
        run_cmd(["ip", "netns", "add", NAMESPACE])
        
        print("[+] --- Step 2: Setting up Virtual Ethernet Link (Veth-Pair) ---")
        run_cmd(["ip", "link", "add", VETH_HOST, "type", "veth", "peer", "name", VETH_NS])
        
        # Move peer interface into the network namespace
        run_cmd(["ip", "link", "set", VETH_NS, "netns", NAMESPACE])
        
        # Configure IPs and bring interfaces up
        run_cmd(["ip", "addr", "add", f"{host_ip}/{mask}", "dev", VETH_HOST])
        run_cmd(["ip", "link", "set", VETH_HOST, "up"])
        
        run_cmd(["ip", "netns", "exec", NAMESPACE, "ip", "addr", "add", f"{ns_ip}/{mask}", "dev", VETH_NS])
        run_cmd(["ip", "netns", "exec", NAMESPACE, "ip", "link", "set", VETH_NS, "up"])
        run_cmd(["ip", "netns", "exec", NAMESPACE, "ip", "link", "set", "lo", "up"])
        
        print("[+] --- Step 3: Configuring Host IP Forwarding, NAT, and Forwarding Whitelist ---")
        run_cmd(["sysctl", "-w", "net.ipv4.ip_forward=1"])
        
        # Insert explicit whitelisting rules at the top of the host's FORWARD chain
        # This is critical on hosts running Tailscale, Docker, or firewalls with default DROP forward policies
        run_cmd(["iptables", "-I", "FORWARD", "-s", subnet, "-j", "ACCEPT"])
        run_cmd(["iptables", "-I", "FORWARD", "-d", subnet, "-j", "ACCEPT"])
        
        fw = get_firewall_provider()
        if fw == "nftables":
            print("[+] Using native nftables for host forwarding NAT...")
            run_cmd(["nft", "add", "table", "ip", "vpn_ns_nat"])
            run_cmd(["nft", "add", "chain", "ip", "vpn_ns_nat", "postrouting", "{ type nat hook postrouting priority srcnat; }"])
            run_cmd(["nft", "add", "rule", "ip", "vpn_ns_nat", "postrouting", "ip", "saddr", subnet, "masquerade"])
        else:
            print("[+] Using legacy iptables for host forwarding NAT...")
            run_cmd(["iptables", "-t", "nat", "-A", "POSTROUTING", "-s", subnet, "-j", "MASQUERADE"])
            
        print("[+] --- Step 4: Routing Endpoint Traffic via Host Link ---")
        # Route namespace internet access to local host gateway temporarily for handshake
        run_cmd(["ip", "netns", "exec", NAMESPACE, "ip", "route", "add", "default", "via", host_ip, "dev", VETH_NS])
        
        print("[+] --- Step 5: Configuring WireGuard Tunnel inside Namespace ---")
        # Create WireGuard device inside namespace
        run_cmd(["ip", "netns", "exec", NAMESPACE, "ip", "link", "add", "dev", INTERFACE, "type", "wireguard"])
        
        # Pass private key securely via stdin to avoid ps leakage
        wg_args = [
            "ip", "netns", "exec", NAMESPACE, 
            "wg", "set", INTERFACE, 
            "private-key", "/dev/stdin", 
            "peer", cfg["public_key"], 
            "endpoint", cfg["resolved_endpoint"], 
            "allowed-ips", cfg["allowed_ips"]
        ]
        run_cmd(wg_args, input_data=cfg["private_key"])
        
        # Configure vpn IP inside namespace
        vpn_ip = cfg["address"].split(",")[0].strip()
        run_cmd(["ip", "netns", "exec", NAMESPACE, "ip", "addr", "add", vpn_ip, "dev", INTERFACE])
        run_cmd(["ip", "netns", "exec", NAMESPACE, "ip", "link", "set", INTERFACE, "up"])
        
        print("[+] --- Step 6: Locking Default Namespace Routes via Tunnel ---")
        # Direct the tunnel handshake UDP packets to the endpoint via veth-ns
        run_cmd(["ip", "netns", "exec", NAMESPACE, "ip", "route", "add", cfg["endpoint_ip"], "via", host_ip, "dev", VETH_NS])
        # Delete temporary default route
        run_cmd(["ip", "netns", "exec", NAMESPACE, "ip", "route", "del", "default", "via", host_ip, "dev", VETH_NS])
        # Force default namespace traffic through wg0 tunnel
        run_cmd(["ip", "netns", "exec", NAMESPACE, "ip", "route", "add", "default", "dev", INTERFACE])
        
        print("[+] --- Step 7: Configuring Isolated Namespace DNS ---")
        dns_dir = f"/etc/netns/{NAMESPACE}"
        os.makedirs(dns_dir, exist_ok=True)
        
        dns_servers = cfg["dns"].split(",")
        resolv_content = "".join([f"nameserver {srv.strip()}\n" for srv in dns_servers])
        with open(f"{dns_dir}/resolv.conf", "w") as resolv_file:
            resolv_file.write(resolv_content)
        os.chmod(f"{dns_dir}/resolv.conf", 0o644)
        
        # Trigger the handshake by sending a single ping to the DNS IP (or 1.1.1.1) in the background.
        # WireGuard is passive and will not handshake until traffic is routed through the interface.
        print("[*] Triggering WireGuard handshake...")
        run_cmd(["ip", "netns", "exec", NAMESPACE, "ping", "-c", "1", "-W", "1", "1.1.1.1"], check=False)
        
        # Verify the handshake
        if not verify_handshake():
            print("[-] Error: WireGuard handshake failed to establish within timeout.")
            raise RuntimeError("WireGuard handshake failed")

        # Apply kill-switch inside the namespace (Strict Drop unless through wg0 or endpoint)
        apply_kill_switch(cfg["endpoint_ip"], cfg["endpoint_port"])
            
        print("[+] --- Step 8: Verifying Interface Connectivity ---")
        test_dns = run_cmd(["ip", "netns", "exec", NAMESPACE, "getent", "hosts", "google.com"], check=False)
        test_ip = run_cmd(["ip", "netns", "exec", NAMESPACE, "curl", "-s", "--connect-timeout", "5", "https://ipinfo.io"], check=False)
        
        if test_dns.returncode == 0 and test_ip.returncode == 0:
            print("[+] Success! VPN namespace is fully connected to the internet.")
            print("[+] Public IP Details inside Namespace:")
            print(test_ip.stdout.strip())
            
            import getpass
            sudo_user = os.environ.get('SUDO_USER') or os.environ.get('USER') or getpass.getuser()
            print(f"\n[+] To execute commands inside this VPN network namespace (avoiding nested sudo):")
            print(f"    sudo ip netns exec {NAMESPACE} runuser -u {sudo_user} -- <command>")
            success = True
        else:
            print("[-] Warning: Handshake succeeded, but external DNS/HTTP checks failed.")
            raise RuntimeError("Connection verification failed")
            
    finally:
        # Automatic rollback on failure
        if not success:
            print("[-] Setup failed. Initiating automatic rollback...")
            stop_vpn(silent=True)
            sys.exit(1)

def stop_vpn(silent=False):
    if os.getuid() != 0:
        print("[*] Script requires root privileges. Escalating via sudo...")
        os.execvp("sudo", ["sudo", "python3"] + sys.argv)

    if not silent:
        print("[+] --- Tearing Down VPN Network Namespace ---")
    
    # 1. Restore original host IP Forwarding value
    if os.path.exists(FORWARD_STATE_FILE):
        try:
            with open(FORWARD_STATE_FILE, "r") as f:
                orig_forward = f.read().strip()
            print(f"[+] Restoring net.ipv4.ip_forward to original value: {orig_forward}")
            run_cmd(["sysctl", "-w", f"net.ipv4.ip_forward={orig_forward}"], check=False)
            os.remove(FORWARD_STATE_FILE)
        except Exception as e:
            if not silent:
                print(f"[-] Warning: Failed to restore IP forwarding: {e}")
                
    # 2. Tear down host forwarding NAT and whitelisted FORWARD filter rules
    subnet = "192.168.99.0/24"  # Default fallback
    if os.path.exists(SUBNET_STATE_FILE):
        try:
            with open(SUBNET_STATE_FILE, "r") as f:
                subnet = f.read().strip()
            os.remove(SUBNET_STATE_FILE)
        except Exception:
            pass
            
    # Remove whitelisted forward rules from host's FORWARD chain
    check_fwd_s = ["iptables", "-C", "FORWARD", "-s", subnet, "-j", "ACCEPT"]
    while subprocess.run(check_fwd_s, stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0:
        run_cmd(["iptables", "-D", "FORWARD", "-s", subnet, "-j", "ACCEPT"], check=False)
        
    check_fwd_d = ["iptables", "-C", "FORWARD", "-d", subnet, "-j", "ACCEPT"]
    while subprocess.run(check_fwd_d, stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0:
        run_cmd(["iptables", "-D", "FORWARD", "-d", subnet, "-j", "ACCEPT"], check=False)

    fw = get_firewall_provider()
    if fw == "nftables":
        run_cmd(["nft", "delete", "table", "ip", "vpn_ns_nat"], check=False)
    else:
        # Loop to clean up any instances of the MASQUERADE rule
        check_args = ["iptables", "-t", "nat", "-C", "POSTROUTING", "-s", subnet, "-j", "MASQUERADE"]
        while subprocess.run(check_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0:
            run_cmd(["iptables", "-t", "nat", "-D", "POSTROUTING", "-s", subnet, "-j", "MASQUERADE"], check=False)
            
    # 3. Delete the network namespace (deleting netns automatically deletes all inside interfaces: wg0, veth-ns)
    # (And deleting veth-ns automatically deletes its host peer veth-host)
    run_cmd(["ip", "netns", "del", NAMESPACE], check=False)
    
    # 4. Clean up netns specific resolv.conf directory
    dns_dir = f"/etc/netns/{NAMESPACE}"
    if os.path.exists(dns_dir):
        shutil.rmtree(dns_dir, ignore_errors=True)
        
    # 5. Backup cleanup for interfaces in case of namespaces failure
    run_cmd(["ip", "link", "del", "dev", VETH_HOST], check=False)
    
    if not silent:
        print("[+] VPN Namespace successfully cleaned up.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 vpn_namespace.py start /path/to/wg0.conf")
        print("  python3 vpn_namespace.py stop")
        sys.exit(1)
        
    action = sys.argv[1].lower()
    if action == "start":
        if len(sys.argv) < 3:
            print("[-] Error: Path to WireGuard config file is required.")
            sys.exit(1)
        start(sys.argv[2])
    elif action == "stop":
        stop_vpn()
    else:
        print(f"[-] Unknown action: {action}")
