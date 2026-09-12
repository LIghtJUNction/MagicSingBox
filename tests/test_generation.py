import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("generate", ROOT / "generate.py")
assert SPEC is not None and SPEC.loader is not None
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)


class GenerationTests(unittest.TestCase):
    def setUp(self):
        self.source = json.loads((ROOT / "config.source.json").read_text())
        self.config = GENERATOR.generate(self.source)

    def test_checked_in_config_is_current(self):
        self.assertEqual(self.config, json.loads((ROOT / "config.json").read_text()))

    def test_all_references_exist(self):
        tags = [r["tag"] for r in self.config["route"]["rule_set"]]
        self.assertEqual(len(tags), len(set(tags)))
        outbounds = {o["tag"] for o in self.config["outbounds"]}
        for section in ("dns", "route"):
            for rule in self.config[section]["rules"]:
                self.assertTrue(set(rule.get("rule_set", [])) <= set(tags))
                if "outbound" in rule:
                    self.assertIn(rule["outbound"], outbounds)

    def test_services_have_consistent_dns_and_route(self):
        for service in ("github", "huggingface", "gitlab", "docker", "npmjs"):
            tag = "meta-" + service
            route = next(
                r for r in self.config["route"]["rules"] if tag in r.get("rule_set", [])
            )
            dns = next(
                r for r in self.config["dns"]["rules"] if tag in r.get("rule_set", [])
            )
            self.assertEqual(route["outbound"], "dev-proxy")
            self.assertEqual(dns["server"], "doh-google")

    def test_dns_merge_preserves_order_and_exceptions(self):
        def flatten(rules):
            return [
                dict(rule, rule_set=[tag]) if "rule_set" in rule else rule
                for rule in rules
                for tag in rule.get("rule_set", [None])
            ]

        self.assertEqual(
            flatten(self.source["dns"]["rules"]), flatten(self.config["dns"]["rules"])
        )
        self.assertEqual(self.source["route"]["rules"], self.config["route"]["rules"])

    def test_generation_does_not_mutate_source(self):
        before = json.dumps(self.source)
        GENERATOR.generate(self.source)
        self.assertEqual(before, json.dumps(self.source))
