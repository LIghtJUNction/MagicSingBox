# Upstream rule-set sources

MagicNet packages local rule files so startup does not depend on GitHub access.
The template contains classifier references rather than service domain/IP lists.

- MetaCubeX/meta-rules-dat, branch `sing`: named AI services, Apple/iCloud,
  Microsoft/Bing, developers, gaming downloads, games, media/entertainment,
  social/communication, Telegram, connectivity, DNS providers and IP diagnostics.
- lyc8503/sing-box-rules: China domains/IPs, advertising and Telegram IPs.
- KaringX/karing-ruleset: WeChat and China domain/IP classifiers.
- razaxq/dns-blocklists-sing-box: HaGeZi light advertising/tracking list.
- SukkaLab/ruleset.skk.moe, branch `master`, `sing-box/ip/ai.json`:
  ChatGPT Voice IPs. The generator in SukkaW/Surge reads OpenAI's published feed.

`5450.update_sing_box_rules.sh` resolves immutable revisions and refreshes
referenced binary rules. `5460.update_chatgpt_voice_rules.sh` validates and
atomically refreshes the local Voice JSON rule set without rewriting config.
Resolved revisions are recorded in the build state. Rule data updates with a
new build, not with ordinary subscription refresh.

Only mode selection, app choices, local/reserved address policy and classifier
ordering remain in the template. See MagicNet's `docs/maintained-routing.md`
for routing priorities and first-match validation.
