"""Local-link DNS contracts; no live multicast or Android network is exercised."""
import ipaddress
import json
import unittest
from itertools import product
from pathlib import Path

from test_routing_policy import dns_target

ROOT = Path(__file__).resolve().parents[1]
MDNS_SUFFIXES = (
    "local", "254.169.in-addr.arpa",
    "8.e.f.ip6.arpa", "9.e.f.ip6.arpa", "a.e.f.ip6.arpa", "b.e.f.ip6.arpa",
)
MODES = ("Rule", "Direct", "Global")


class MDNSPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.configs = [json.loads((ROOT / name).read_text(encoding="utf-8"))
                       for name in ("config.source.json", "config.json")]

    def test_local_names_and_link_local_ptr_precede_public_dns_in_every_mode(self):
        names = MDNS_SUFFIXES + ("printer.local", "_ipp._tcp.local") + tuple(
            ipaddress.ip_address(address).reverse_pointer
            for address in ("169.254.0.1", "169.254.255.254", "fe80::1",
                            "fe90::1", "fea0::1", "febf:ffff::1")
        )
        conflicting_tags = ("lyc-geosite-cn", "lyc-geosite-ads", "meta-google")
        for config, name, mode in product(self.configs, names, MODES):
            with self.subTest(name=name, mode=mode):
                self.assertEqual(dns_target(config, name, conflicting_tags, mode), "lan-mdns")

    def test_suffix_boundaries_preserve_public_proxy_dns(self):
        names = ["unknown.example.invalid", "localdomain", "printer.localhost"]
        for suffix in MDNS_SUFFIXES:
            names.extend(("not" + suffix, suffix + ".example.invalid"))
        names.extend(ipaddress.ip_address(address).reverse_pointer for address in (
            "169.253.255.254", "169.255.0.1", "192.168.1.1", "fe7f::1", "fec0::1", "fd00::1",
        ))
        for config, name, mode in product(self.configs, names, MODES):
            with self.subTest(name=name, mode=mode):
                expected = "bootstrap-local-dns" if mode == "Direct" else "doh-cloudflare"
                self.assertEqual(dns_target(config, name, mode=mode), expected)

    def test_mdns_is_a_terminal_native_transport_without_a_public_resolver(self):
        for config in self.configs:
            servers = {server["tag"]: server for server in config["dns"]["servers"]}
            self.assertEqual(servers["lan-mdns"], {"type": "mdns", "tag": "lan-mdns"})
            mdns_rules = [rule for rule in config["dns"]["rules"]
                          if rule.get("server") == "lan-mdns"]
            self.assertEqual(mdns_rules, [{"domain_suffix": list(MDNS_SUFFIXES), "server": "lan-mdns"}])
            self.assertEqual(config["dns"]["rules"][0], mdns_rules[0])
            self.assertEqual(config["dns"]["final"], "doh-cloudflare")
            self.assertEqual(servers["doh-cloudflare"]["detour"], "proxy")
            self.assertEqual(config["route"]["default_domain_resolver"], "bootstrap-local-dns")

    def test_other_lan_and_tailnet_names_keep_the_existing_policy(self):
        for config, name, mode in product(
            self.configs, ("home.arpa", "nas.home.arpa", "router.lan", "host.ts.net", "tailscale.net"), MODES,
        ):
            with self.subTest(name=name, mode=mode):
                expected = "doh-cloudflare" if mode == "Global" else "bootstrap-local-dns"
                self.assertEqual(dns_target(config, name, mode=mode), expected)


if __name__ == "__main__":
    unittest.main()
