# MagicNet sing-box rule sets

MagicNet uses local binary `.srs` rule sets so sing-box can start without
runtime rule-set downloads. The pre-build hook
`hooks/pre-build/5450.update_sing_box_rules.sh` refreshes every local file
referenced by `.config/sing-box/config.json`.

Current upstream snapshots:

- `lyc8503/sing-box-rules` `rule-set-geosite`: `b23ddef709fc9e8b5f89a924f22a11c0dc85ce88`
- `lyc8503/sing-box-rules` `rule-set-geoip`: `d0d2c3b82ea6dfbe34ddcbca01fddc97a5749856`
- `MetaCubeX/meta-rules-dat` `sing`: `673e451d3caaec11c14905d0e48312e555e7b1aa`
- `Yuu518/sing-box-rules` `rule_set`: `040d185670f96ed503e274641bba4093b23e879b`
- `DDCHlsq/sing-ruleset` `ruleset`: `bcbf9d73bf571dac5e92993756ea572e0173c1ae`
- `razaxq/dns-blocklists-sing-box` `rule-set`: `d9b788608bee54c519ffcf8ea107329940a90573`
- `KaringX/karing-ruleset` `sing`: `1c960260812100c0724d11399ff99ee460196655`

Bundled rule-set families:

- lyc8503 base geosite/geoip: private, ads, CN, AI, dev, media, games,
  social, Telegram, GFW, and geolocation-not-CN.
- MetaCubeX base split: `cn`, `geoip-cn`, and `geolocation-!cn`.
- Yuu518 enhanced split: `pcdn-cn`, `stream-global`, and `category-ai-!cn`.
- DDCHlsq fine split: `direct`, `proxy`, and `gfw`.
- HaGeZi DNS blocklists: `hagezi-light`, `hagezi-normal`, and
  `hagezi-anti-piracy`.
- Karing client-oriented ACL4SSR sets: AI, proxy-lite, proxy-GFW, ad block,
  China domain/IP, and proxy media.
