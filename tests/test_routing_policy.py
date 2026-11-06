"""Policy regressions. Rule-set memberships are synthetic, not live SRS data."""
import json
import unittest
from itertools import product
from pathlib import Path

from test_dns_routing_priority import first_action, values

ROOT = Path(__file__).resolve().parents[1]
CN_TAGS = ("lyc-geosite-cn", "metacubex-geosite-cn", "karing-acl4ssr-china-domain")
BLOCKED_DOMAINS = (
    "flash.sec.miui.com",
    "fraud-detection.engine.miui.com",
    "eps.caict.ac.cn",
    "gateway-papa.cloud.weizhi.com",
)
PORT_BLOCK_DOMAIN = "dm.wo.com.cn"
EDUCATION_SUFFIXES = (
    "edu.cn", "moe.gov.cn", "chsi.com.cn", "smartedu.cn", "neea.cn", "ncss.cn",
    "icourse163.org", "icourses.cn", "xuetangx.com", "yuketang.cn", "chaoxing.com",
    "zhihuishu.com", "eol.cn", "cnki.net", "wanfangdata.com.cn", "cqvip.com",
)


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

    def test_explicit_blocks_precede_modes_apps_and_classifiers(self):
        conflicting = CN_TAGS + ("lyc-geoip-cn", "lyc-geosite-ads", "meta-google-play")
        targets = list(product(BLOCKED_DOMAINS, (1, 80, 443, 853, 18080, 65535)))
        targets.append((PORT_BLOCK_DOMAIN, 18080))
        for (domain, port), mode, network, inbound in product(
            targets, ("Rule", "Direct", "Global"), ("tcp", "udp"),
            ("tun-in", "mixed-in", "ebpf-in"),
        ):
            with self.subTest(domain=domain, port=port, mode=mode,
                              network=network, inbound=inbound):
                self.assertEqual(first_action(
                    self.config, domain=domain, port=port, mode=mode,
                    network=network, inbound=inbound, tags=conflicting,
                    package="com.android.vending",
                ), "reject")

    def test_explicit_blocks_keep_exact_host_boundaries(self):
        for domain, network in product(BLOCKED_DOMAINS + (PORT_BLOCK_DOMAIN,), ("tcp", "udp")):
            neighbors = (domain.split(".", 1)[1], "sub." + domain,
                         "not" + domain, domain + ".example.invalid")
            for neighbor in neighbors:
                with self.subTest(domain=neighbor, network=network):
                    self.assertEqual(first_action(
                        self.config, domain=neighbor, port=18080,
                        network=network, tags=CN_TAGS,
                    ), "cn-direct")

    def test_port_scoped_block_preserves_other_ports_and_dns(self):
        for port, network, (mode, expected) in product(
            (1, 80, 443, 18079, 18081, 65535), ("tcp", "udp"),
            (("Rule", "cn-direct"), ("Direct", "direct"), ("Global", "select")),
        ):
            with self.subTest(port=port, network=network, mode=mode):
                self.assertEqual(first_action(
                    self.config, domain=PORT_BLOCK_DOMAIN, port=port,
                    network=network, mode=mode, tags=CN_TAGS,
                ), expected)
        self.assertEqual(dns_target(self.config, PORT_BLOCK_DOMAIN), "bootstrap-local-dns")

    def test_dns_capture_still_precedes_explicit_blocks(self):
        for domain, mode, network in product(
            BLOCKED_DOMAINS + (PORT_BLOCK_DOMAIN,),
            ("Rule", "Direct", "Global"), ("tcp", "udp"),
        ):
            with self.subTest(domain=domain, mode=mode, network=network):
                self.assertEqual(first_action(
                    self.config, domain=domain, port=53, mode=mode, network=network,
                ), "hijack-dns")
                self.assertEqual(first_action(
                    self.config, domain=domain, port=18080, protocol="dns",
                    mode=mode, network=network,
                ), "hijack-dns")

    def test_education_roots_and_subdomains_use_domestic_route_and_dns(self):
        domains = [prefix + suffix for suffix, prefix in product(
            EDUCATION_SUFFIXES, ("", "www.", "campus.portal."),
        )] + ["www.pku.edu.cn", "sso.tsinghua.edu.cn", "vpn.sjtu.edu.cn"]
        for domain, network in product(domains, ("tcp", "udp")):
            with self.subTest(domain=domain, network=network):
                self.assertEqual(first_action(self.config, domain=domain, network=network), "cn-direct")
                self.assertEqual(dns_target(self.config, domain), "bootstrap-local-dns")

    def test_education_precedes_later_proxy_classifiers(self):
        categories = (
            "meta-category-scholar-!cn", "meta-category-ai-!cn", "meta-category-games-!cn",
            "meta-category-dev", "meta-category-media", "meta-category-entertainment",
            "meta-category-communication", "meta-category-social-media-!cn",
            "metacubex-geosite-geolocation-not-cn", "meta-gitlab", "meta-huggingface",
            "meta-docker", "meta-npmjs",
        )
        for suffix, category in product(EDUCATION_SUFFIXES, categories):
            domain = "www." + suffix
            with self.subTest(domain=domain, category=category):
                self.assertEqual(first_action(self.config, domain=domain, tags=(category,)), "cn-direct")
                self.assertEqual(dns_target(self.config, domain, (category,)), "bootstrap-local-dns")

    def test_education_does_not_capture_foreign_or_lookalike_domains(self):
        domains = ["mit.edu", "cuhk.edu.hk", "ntu.edu.tw", "ox.ac.uk", "example.school"]
        for suffix in EDUCATION_SUFFIXES:
            domains.extend(("not" + suffix, suffix + ".example.invalid", suffix + "-other.invalid"))
        for domain in domains:
            with self.subTest(domain=domain):
                # A foreign-scholar membership makes an accidental education
                # match visible even for lookalikes under the generic .cn suffix.
                tags = ("meta-category-scholar-!cn",)
                self.assertEqual(first_action(self.config, domain=domain, tags=tags), "proxy-rule")
                self.assertEqual(dns_target(self.config, domain, tags), "doh-google")

    def test_education_preserves_modes_and_front_loaded_guards(self):
        for domain in ("www.pku.edu.cn", "www.icourse163.org"):
            for mode, route, dns in (("Direct", "direct", "bootstrap-local-dns"),
                                     ("Global", "select", "doh-cloudflare")):
                with self.subTest(domain=domain, mode=mode):
                    self.assertEqual(first_action(self.config, domain=domain, mode=mode), route)
                    self.assertEqual(dns_target(self.config, domain, mode=mode), dns)
            self.assertEqual(first_action(self.config, domain=domain, address="192.168.1.10"), "lan")
            self.assertEqual(first_action(self.config, domain=domain, port=53), "hijack-dns")
            self.assertEqual(first_action(self.config, domain=domain, port=853), "dns-guard")
            self.assertEqual(first_action(self.config, domain=domain,
                                          package="com.android.vending"), "google-proxy")
            for tag, route, dns in (("lyc-geosite-ads", "ad-block", "doh-cloudflare"),
                                    ("meta-category-doh", "dns-guard", "doh-cloudflare"),
                                    ("meta-google", "google-proxy", "doh-google")):
                with self.subTest(domain=domain, guard=tag):
                    self.assertEqual(first_action(self.config, domain=domain, tags=(tag,)), route)
                    self.assertEqual(dns_target(self.config, domain, (tag,)), dns)

    def test_education_route_and_dns_share_the_bounded_suffix_inventory(self):
        for config in (self.config, json.loads((ROOT / "config.source.json").read_text(encoding="utf-8"))):
            route = [rule for rule in config["route"]["rules"] if "edu.cn" in rule.get("domain_suffix", [])]
            dns = [rule for rule in config["dns"]["rules"] if "edu.cn" in rule.get("domain_suffix", [])]
            self.assertEqual(route, [{"domain_suffix": list(EDUCATION_SUFFIXES), "outbound": "cn-direct"}])
            self.assertEqual(dns, [{"domain_suffix": list(EDUCATION_SUFFIXES), "server": "bootstrap-local-dns"}])
        domestic = next(outbound for outbound in self.config["outbounds"] if outbound["tag"] == "cn-direct")
        self.assertEqual(domestic["default"], "direct")

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
