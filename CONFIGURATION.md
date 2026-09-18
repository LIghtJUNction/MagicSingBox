# 配置维护

维护 `config.source.json`，然后执行：

```sh
python3 generate.py
python3 generate.py --check
python3 -m unittest discover -s tests
```

`config.json` 是生成后的独立 sing-box 配置，随模块发布；设备不需要 Python。提交配置修改时同时提交源文件和生成文件。不要仅修改生成文件。

源文件将重复的 selector 选项提取到 `selector_profiles`，将本地规则定义简化为 tag → path 映射。生成器只合并相邻且服务器相同的纯 rule_set DNS 规则，不跨越例外，不调整路由优先级。

## 服务规则来源

上游：<https://github.com/MetaCubeX/meta-rules-dat/tree/sing/geo/geosite>

本次已通过 GitHub raw 获取对应 JSON 核实的服务：

- 开发：Hugging Face、GitLab、Docker、npmjs → `dev-proxy`；GitHub → `github-proxy`
- 协作/社区：Notion、Slack、Reddit → 原有通信规则出口；Discord → `discord-proxy`
- 媒体：Spotify、Netflix、YouTube → 各自的 `<service>-proxy` 独立出口

Hugging Face 的模型下载使用开发出口，不强制套用聊天 AI 的地区限制。以上服务同时加入对应 DNS 规则，沿用原分类的解析策略。

`rules/metacubex-service-<name>.srs` 由主仓库 `hooks/pre-build/5450.update_sing_box_rules.sh` 从同一上游的 `sing/geo/geosite/<name>.srs` 打包。新增服务不再需要同步修改 shell 白名单。构建时仍须成功下载/校验实际 SRS 文件；源码测试不能替代真机连通性验证。

Google、YouTube、GitHub、Discord、Netflix、Spotify、X/Twitter、WhatsApp 分别使用独立代理组，默认代理。Telegram 保留域名和 IP 双规则；新增 Twitter、WhatsApp 上游规则。Gemini、Google Play 和 Google 登录规则先于广告规则，保证登录、Play 与 Gemini 不被广告分类误伤；更宽泛的 YouTube 与 Google 总规则位于广告规则之后，让广告域名仍可被拦截；DNS 保持同序。规则随 MagicNet 构建打包，更新订阅只更新节点。

## sing-box 1.14 DNS 地址过滤兼容

`karing-acl4ssr-wechat.srs` 同时包含域名与 IP 匹配项。它仍用于路由层的微信直连判断，但不得直接用于 `dns.rules`：sing-box 1.14 起会把规则集中的 `ip_cidr` 视为旧式 DNS 响应地址过滤，并输出弃用警告，1.16 将移除这种隐式行为。

DNS 侧仅保留该规则集当前对应的微信域名后缀，并继续交给 `bootstrap-local-dns`。不要用 `evaluate + match_response` 机械迁移这里的 9 个 IP；那会把它们变成真正的 DNS 响应路由条件，改变现有的域名分类语义。

