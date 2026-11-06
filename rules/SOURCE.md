# Upstream rule-set sources

MagicNet packages local rule files so startup does not depend on GitHub access.
Shared service domain/IP datasets are referenced through maintained classifiers.

- MetaCubeX/meta-rules-dat, branch `sing`: named AI services, Apple/iCloud,
  Microsoft/Bing, developers, gaming downloads, games, media/entertainment,
  social/communication, Telegram, connectivity, DNS providers and IP diagnostics.
- lyc8503/sing-box-rules: China domains/IPs, advertising and Telegram IPs.
- KaringX/karing-ruleset: WeChat and China domain/IP classifiers.
- razaxq/dns-blocklists-sing-box: HaGeZi light advertising/tracking list.

`5450.update_sing_box_rules.sh` installs referenced binary rules from the
reviewed MagicNetRules Release pin after verifying its manifest and checksums.
Rule data updates with a new build, not with ordinary subscription refresh.
ChatGPT uses the existing OpenAI domain classifier and app routing; connections
without either match follow the remaining routing policy.

The template keeps mode selection, app choices, local/reserved address policy,
explicit host rejects, bounded education-domain defaults and classifier ordering.
See `CONFIGURATION.md` for the education inventory and official sources, and
MagicNet's `docs/maintained-routing.md` for first-match validation.
