import json
import unittest
from pathlib import Path


CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.json"


def domain_suffix_matches(domain, suffix):
    return domain == suffix or domain.endswith(f".{suffix}")


class RoutingConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    def test_google_family_precedes_advertising(self):
        for section in ("route", "dns"):
            rules = self.config[section]["rules"]
            ads = next(i for i, r in enumerate(rules) if "lyc-geosite-ads" in r.get("rule_set", []))
            protected = [
                next(i for i, r in enumerate(rules) if tag in r.get("rule_set", []))
                for tag in ("meta-google-gemini", "meta-google-play", "meta-youtube", "meta-google")
            ]
            protected.append(
                next(i for i, r in enumerate(rules) if "android.clients.google.com" in r.get("domain", []))
            )
            self.assertTrue(all(index < ads for index in protected))

        route_rules = self.config["route"]["rules"]
        expected = {
            "meta-google-gemini": "ai-gemini",
            "meta-google-play": "google-proxy",
            "meta-youtube": "youtube-proxy",
            "meta-google": "google-proxy",
        }
        for tag, outbound in expected.items():
            rule = next(r for r in route_rules if tag in r.get("rule_set", []))
            self.assertEqual(rule["outbound"], outbound)

    def test_icloud_domains_reach_icloud_selector(self):
        rules = self.config["route"]["rules"]
        icloud_index, icloud_rule = next(
            (index, rule)
            for index, rule in enumerate(rules)
            if rule.get("outbound") == "icloud"
        )

        if icloud_rule.get("rule_set") == ["meta-icloud"]:
            apple_index = next(i for i, r in enumerate(rules) if r.get("rule_set") == ["meta-apple"])
            self.assertLess(icloud_index, apple_index)
            return

        for domain in icloud_rule["domain_suffix"]:
            shadowing_rules = [
                (index, rule["outbound"], suffix)
                for index, rule in enumerate(rules[:icloud_index])
                for suffix in rule.get("domain_suffix", [])
                if "outbound" in rule and domain_suffix_matches(domain, suffix)
            ]
            self.assertEqual(
                [],
                shadowing_rules,
                f"{domain} is claimed before the dedicated iCloud rule",
            )


if __name__ == "__main__":
    unittest.main()
