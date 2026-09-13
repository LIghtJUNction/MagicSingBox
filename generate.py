#!/usr/bin/env python3
"""Expand config.source.json into the deployable, standalone config.json."""

import argparse
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def generate(source):
    config = copy.deepcopy(source)
    profiles = config.pop("selector_profiles")
    for outbound in config["outbounds"]:
        if "profile" in outbound:
            choices = profiles[outbound.pop("profile")]
            outbound.update(type="selector", outbounds=choices, default=choices[0])
    config["route"]["rule_set"] = [
        {
            "type": "local",
            "tag": tag,
            "format": "source" if path.endswith(".json") else "binary",
            "path": path,
        }
        for tag, path in config["route"]["rule_set"].items()
    ]
    # Only adjacent pure rule-set DNS rules may be merged. Never move rules
    # across exceptions (e.g. Bing CN before Bing, local DNS before global).
    merged = []
    for rule in config["dns"]["rules"]:
        if (
            merged
            and set(rule) == {"rule_set", "server"}
            and set(merged[-1]) == set(rule)
            and merged[-1]["server"] == rule["server"]
        ):
            merged[-1]["rule_set"].extend(rule["rule_set"])
        else:
            merged.append(rule)
    config["dns"]["rules"] = merged
    return config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        source = json.loads((ROOT / "config.source.json").read_text())
        rendered = json.dumps(generate(source), ensure_ascii=False, indent=2) + "\n"
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Invalid configuration source: {error}\n")
    target = ROOT / "config.json"
    if args.check:
        if target.read_text() != rendered:
            parser.exit(1, "config.json is stale; run python3 generate.py\n")
    else:
        temporary = target.with_suffix(".json.tmp")
        temporary.write_text(rendered)
        temporary.replace(target)


if __name__ == "__main__":
    main()
