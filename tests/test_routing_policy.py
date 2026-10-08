"""Policy regressions. Rule-set memberships are synthetic, not live SRS data."""
import json
import unittest
from pathlib import Path

from test_dns_routing_priority import first_action, values

ROOT = Path(__file__).resolve().parents[1]
CN_TAGS = ("lyc-geosite-cn", "metacubex-geosite-cn", "karing-acl4ssr-china-domain")


def dns_target(config, domain="", tags=(), mode="Rule", protocol=""):
    """Evaluate this template's domain-only DNS rules; reject unknown matchers."""
    for rule in config["dns"]["rules"]:
        unknown = set(rule) - {"domain", "domain_suffix", "rule_set", "clash_mode", "protocol", "server"}
        if unknown:
            raise AssertionError(f"Unsupported DNS matcher: {unknown}")
        if "clash_mode" in rule and rule["clash_mode"] != mode:
            continue
        if "protocol" in rule and protocol not in values(rule["protocol"]):
            continue
        if "domain" in rule and domain not in values(rule["domain"]):
            continue
        if "domain_suffix" in rule and not any(
            domain == suffix or domain.endswith("." + suffix)
            for suffix in values(rule["domain_suffix"])
        ):
            continue
        if "rule_set" in rule and not set(values(rule["rule_set"])) & set(tags):
            continue
        return rule["server"]
    return config["dns"]["final"]


class RoutingPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))

    def test_lmm_uses_proxy_and_remote_dns_in_every_mode(self):
        conflicting = CN_TAGS + ("lyc-geoip-cn", "meta-category-dev", "lyc-geosite-ads", "meta-tencent")
        for domain in ("lmm.best", "api.lmm.best", "msg.lmm.best", "donate.lmm.best", "nested.api.lmm.best"):
            for mode in ("Rule", "Direct", "Global"):
                for network in ("tcp", "udp"):
                    with self.subTest(domain=domain, mode=mode, network=network):
                        self.assertEqual(first_action(self.config, domain=domain, tags=conflicting,
                            mode=mode, network=network, package="com.android.vending"), "proxy")
                        self.assertEqual(dns_target(self.config, domain, conflicting, mode), "doh-cloudflare")
        server = next(s for s in self.config["dns"]["servers"] if s["tag"] == "doh-cloudflare")
        self.assertEqual(server["detour"], "proxy")

    def test_lmm_suffix_has_a_domain_boundary(self):
        for domain in ("notlmm.best", "lmm.best.evil.invalid", "lmm.best-other.invalid"):
            with self.subTest(domain=domain):
                self.assertEqual(first_action(self.config, domain=domain, tags=CN_TAGS), "cn-direct")
                self.assertEqual(dns_target(self.config, domain, CN_TAGS), "bootstrap-local-dns")
                self.assertEqual(first_action(self.config, domain=domain, mode="Direct"), "direct")
                self.assertEqual(first_action(self.config, domain=domain, mode="Global"), "select")

    def test_dns_capture_still_precedes_lmm(self):
        for mode in ("Rule", "Direct", "Global"):
            for network in ("tcp", "udp"):
                self.assertEqual(first_action(self.config, domain="api.lmm.best", port=53,
                    mode=mode, network=network), "hijack-dns")
        self.assertEqual(first_action(self.config, domain="api.lmm.best", port=5353,
            protocol="dns"), "hijack-dns")

    def test_unconfigured_lmm_proxy_cannot_fall_back_to_direct(self):
        proxy = next(o for o in self.config["outbounds"] if o["tag"] == "proxy")
        self.assertEqual(proxy["default"], "block")
        self.assertEqual(proxy["outbounds"], ["block"])

    def test_explicit_foreign_services_precede_generic_cn(self):
        services = (("meta-category-ai-!cn", "ai-proxy"), ("meta-notion", "social-proxy"),
                    ("meta-slack", "social-proxy"), ("meta-reddit", "social-proxy"),
                    ("meta-category-social-media-!cn", "social-proxy"))
        for tag, target in services:
            for cn_tag in CN_TAGS:
                with self.subTest(tag=tag, cn_tag=cn_tag):
                    tags = (tag, cn_tag)
                    self.assertEqual(first_action(self.config, domain="overlap.example.cn", tags=tags), target)
                    self.assertEqual(dns_target(self.config, "overlap.example.cn", tags), "doh-google")

    def test_broad_developer_and_communication_categories_do_not_override_cn(self):
        for category in ("meta-category-dev", "meta-category-communication"):
            for cn_tag in CN_TAGS:
                tags = (category, cn_tag)
                with self.subTest(category=category, cn_tag=cn_tag):
                    self.assertEqual(first_action(self.config, tags=tags), "cn-direct")
                    self.assertEqual(dns_target(self.config, tags=tags), "bootstrap-local-dns")
        self.assertEqual(first_action(self.config, tags=("meta-category-dev",)), "dev-proxy")
        self.assertEqual(dns_target(self.config, tags=("meta-category-dev",)), "doh-google")
        for service in ("meta-huggingface", "meta-gitlab", "meta-docker", "meta-npmjs"):
            tags = (service,) + CN_TAGS
            self.assertEqual(first_action(self.config, tags=tags), "dev-proxy")
            self.assertEqual(dns_target(self.config, tags=tags), "doh-google")

    def test_cn_internationalized_suffixes_use_dns_wire_labels(self):
        for suffix in ("中国", "公司", "网络"):
            domain = "example." + suffix.encode("idna").decode("ascii")
            with self.subTest(domain=domain):
                self.assertEqual(first_action(self.config, domain=domain), "cn-direct")
                self.assertEqual(dns_target(self.config, domain), "bootstrap-local-dns")

    def test_bootstrap_and_domestic_dns_stay_direct(self):
        self.assertEqual(self.config["route"]["default_domain_resolver"], "bootstrap-local-dns")
        bootstrap = next(s for s in self.config["dns"]["servers"] if s["tag"] == "bootstrap-local-dns")
        self.assertNotIn("detour", bootstrap)
        for domain in ("router.home.arpa", "host.lan", "example.cn"):
            self.assertEqual(dns_target(self.config, domain), "bootstrap-local-dns")


if __name__ == "__main__":
    unittest.main()
