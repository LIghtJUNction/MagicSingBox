"""Configuration-order regressions; memberships below are synthetic, not live SRS data."""
import ipaddress
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def values(value):
    return value if isinstance(value, list) else [value]


def first_action(config, *, tags=(), domain="", address="203.0.113.99", port=443,
                 network="tcp", mode="Rule", protocol="", package="", inbound="tun-in"):
    """Model only the current template's flat matchers; fail on unknown fields."""
    known = {"action", "outbound", "inbound", "port", "network", "protocol",
             "clash_mode", "domain", "domain_suffix", "ip_cidr", "ip_is_private",
             "package_name", "rule_set"}
    for rule in config["route"]["rules"]:
        if set(rule) - known:
            raise AssertionError(f"Unsupported test matcher: {set(rule) - known}")
        # Sniff is non-terminal. Tests supply protocol metadata explicitly.
        if rule.get("action") == "sniff":
            continue
        metadata = {"inbound": inbound, "port": port, "network": network,
                    "protocol": protocol, "clash_mode": mode, "package_name": package}
        if any(key in rule and value not in values(rule[key])
               for key, value in metadata.items()):
            continue
        if "domain" in rule and domain not in values(rule["domain"]):
            continue
        if "domain_suffix" in rule and not any(
            domain == suffix or domain.endswith("." + suffix)
            for suffix in values(rule["domain_suffix"])
        ):
            continue
        if "ip_cidr" in rule and not any(
            ipaddress.ip_address(address) in ipaddress.ip_network(cidr)
            for cidr in values(rule["ip_cidr"])
        ):
            continue
        if rule.get("ip_is_private") and not any(
            ipaddress.ip_address(address) in ipaddress.ip_network(cidr)
            for cidr in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "fc00::/7")
        ):
            continue
        if "rule_set" in rule and not set(values(rule["rule_set"])) & set(tags):
            continue
        return rule.get("action", rule.get("outbound"))
    return config["route"]["final"]


class DnsRoutingPriorityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))

    def test_port_53_precedes_sniff_modes_lan_and_packages(self):
        self.assertEqual(self.config["route"]["rules"][0],
                         {"port": 53, "action": "hijack-dns"})
        for inbound in ("tun-in", "mixed-in", "ebpf-in"):
            for network in ("tcp", "udp"):
                for mode in ("Rule", "Direct", "Global"):
                    with self.subTest(inbound=inbound, network=network, mode=mode):
                        self.assertEqual(first_action(
                            self.config, inbound=inbound, port=53, network=network,
                            mode=mode, address="192.168.1.1", package="com.android.vending"
                        ), "hijack-dns")

    def test_nonstandard_dns_keeps_protocol_fallback(self):
        for network in ("tcp", "udp"):
            self.assertEqual(first_action(self.config, port=5353, protocol="dns",
                                          network=network), "hijack-dns")
        self.assertEqual(first_action(self.config, port=853), "dns-guard")
        self.assertEqual(first_action(self.config), "final")

    def test_foreign_domain_precedes_each_cn_ip_fallback(self):
        for tag in ("lyc-geoip-cn", "metacubex-geoip-cn", "karing-acl4ssr-china-ip"):
            with self.subTest(tag=tag):
                self.assertEqual(first_action(self.config, domain="foreign.example.invalid",
                    tags=("metacubex-geosite-geolocation-not-cn", tag)), "proxy-rule")

    def test_bare_ip_and_unknown_fallbacks_remain(self):
        self.assertEqual(first_action(self.config, tags=("lyc-geoip-cn",)), "cn-direct")
        self.assertEqual(first_action(self.config, tags=("lyc-geoip-telegram",)), "telegram-proxy")
        self.assertEqual(first_action(self.config), "final")
        self.assertEqual(first_action(self.config, address="192.168.1.1"), "lan")

    def test_explicit_domains_and_modes_keep_precedence(self):
        generic = ("metacubex-geosite-geolocation-not-cn", "lyc-geoip-cn")
        for tag, target in (("meta-google-play", "google-proxy"),
                            ("meta-google-gemini", "ai-gemini"),
                            ("meta-openai", "ai-chatgpt"),
                            ("lyc-geosite-ads", "ad-block"),
                            ("lyc-geosite-cn", "cn-direct")):
            with self.subTest(tag=tag):
                self.assertEqual(first_action(self.config, tags=generic + (tag,)), target)
        self.assertEqual(first_action(self.config, tags=generic, mode="Direct"), "direct")
        self.assertEqual(first_action(self.config, tags=generic, mode="Global"), "select")

    def test_bootstrap_and_cache_policy_stay_nonrecursive(self):
        servers = {server["tag"]: server for server in self.config["dns"]["servers"]}
        bootstrap = servers["bootstrap-local-dns"]
        self.assertNotIn("detour", bootstrap)
        ipaddress.ip_address(bootstrap["server"])
        self.assertEqual(self.config["route"]["default_domain_resolver"], "bootstrap-local-dns")
        self.assertEqual(self.config["dns"]["final"], "bootstrap-local-dns")
        self.assertNotIn("independent_cache", self.config["dns"])
        for server in servers.values():
            if server["type"] == "https":
                self.assertTrue(server["tls"]["enabled"])
                self.assertTrue(server["tls"]["server_name"])
        for rule in self.config["dns"]["rules"]:
            self.assertFalse(set(rule) & {"ip_cidr", "ip_is_private", "rule_set_ip_cidr_accept_empty"})


if __name__ == "__main__":
    unittest.main()
