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

    def test_icloud_domains_reach_icloud_selector(self):
        rules = self.config["route"]["rules"]
        icloud_index, icloud_rule = next(
            (index, rule)
            for index, rule in enumerate(rules)
            if rule.get("outbound") == "icloud"
        )

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
