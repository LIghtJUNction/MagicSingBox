# 配置维护

维护 `config.source.json`，然后执行：

```sh
python3 generate.py
python3 generate.py --check
python3 -m unittest discover -s tests
```

`config.json` 是生成后的独立 sing-box 配置，随模块发布；设备不需要 Python。提交配置修改时同时提交源文件和生成文件。不要仅修改生成文件。

源文件将重复的 selector 选项提取到 `selector_profiles`，将本地规则定义简化为 tag → path 映射。生成器只合并相邻且服务器相同的纯 rule_set DNS 规则，不跨越例外，不调整路由优先级。

## 默认 DNS 出口

未匹配显式分类的域名使用 `dns.final: doh-cloudflare`，查询通过该服务器的 `detour: proxy` 发送。代理不可用或模板尚无节点时，这条默认解析路径随代理失败，不自动回落到直连 DNS。现有国内分类、LAN/Tailnet 和 Direct 模式的 DNS 规则仍优先匹配。

代理节点域名继续通过 `route.default_domain_resolver: bootstrap-local-dns` 引导解析。这个本地加密解析器保留独立的直连路径，使建立代理连接不依赖尚未建立的代理。`tests/test_routing_policy.py` 覆盖未知域名、显式模式和无节点默认；`tests/test_dns_routing_priority.py` 覆盖引导解析与规则次序。真实查询与 Android 流量验收由 MagicNet 的运行时测试记录。

## 指定目标阻断

模板使用原生 `action: "reject"` 拒绝以下目标，TCP 和 UDP 均适用：

| 完整域名 | 目标端口 |
| --- | --- |
| `flash.sec.miui.com` | 全部 |
| `fraud-detection.engine.miui.com` | 全部 |
| `eps.caict.ac.cn` | 全部 |
| `gateway-papa.cloud.weizhi.com` | 全部 |
| `dm.wo.com.cn` | `18080` |

域名采用精确匹配；父域、子域及相似名称沿用其他规则。`dm.wo.com.cn` 的其他端口也沿用其他规则。模板中的 DNS 捕获和嗅探先执行，指定目标阻断随后执行，优先于 Direct/Global 模式、LAN、应用和国内分类规则。这两条拒绝规则独立于广告组及社区名单开关；DNS 服务器选择沿用原配置。

规则适用于进入 sing-box 且能识别到目标域名的流量。`tests/test_routing_policy.py` 检查匹配范围、端口、优先级及 DNS 捕获；这些配置测试不代表真机流量验证，也不说明上述域名的实际业务用途。

## 大陆教育站点默认直连

规则模式下，下列域名及其子域名优先使用 `cn-direct`（默认 `direct`），DNS 使用既有的本地加密解析器 `bootstrap-local-dns`。两侧使用同一份 16 项后缀清单，不新增 selector、DNS server 或下载依赖。

| 范围 | 域名后缀 | 官方来源 |
| --- | --- | --- |
| 学校与教育科研域名空间 | `edu.cn` | [CERNIC](https://www.nic.edu.cn/home.html) |
| 教育部 | `moe.gov.cn` | [政府门户年度报表](https://www.moe.gov.cn/jyb_xxgk/s5743/s5744/A01/202601/t20260130_1427931.html) |
| 学信网 | `chsi.com.cn` | [网站介绍](https://www.chsi.com.cn/about/about_site.shtml) |
| 国家智慧教育平台 | `smartedu.cn` | [平台域名规范](https://hudong.moe.gov.cn/srcsite/A16/s3342/202208/t20220819_653868.html) |
| 教育考试报名 | `neea.cn` | [中国教育考试网](https://www.neea.edu.cn/) |
| 国家大学生就业服务 | `ncss.cn` | [平台介绍](https://gyu.ncss.cn/intro) |
| 中国大学 MOOC | `icourse163.org` | [关于我们](https://www.icourse163.org/about/aboutus.htm) |
| 爱课程 | `icourses.cn` | [服务说明](https://www.icourses.cn/webInfo?type=contactUs) |
| 学堂在线 | `xuetangx.com` | [官方平台](https://next.xuetangx.com/) |
| 雨课堂 | `yuketang.cn` | [使用帮助](https://www.yuketang.cn/static/html/faq.html) |
| 超星、学习通 | `chaoxing.com` | [官方学习通介绍](https://apps.chaoxing.com/d/app/198.html) |
| 智慧树 | `zhihuishu.com` | [官方平台](https://www.zhihuishu.com/) |
| 教育资讯 | `eol.cn` | [教育在线](https://www.eol.cn/) |
| 知网 | `cnki.net` | [官方论文管理服务说明](https://co2.cnki.net/User/agreement.html) |
| 万方 | `wanfangdata.com.cn` | [官方平台](https://www.wanfangdata.com.cn/) |
| 维普 | `cqvip.com` | [官方平台](https://www.cqvip.com/) |

教育路由位于目标端口 `853` 的 `dns-guard` 之后，教育 DNS 位于 DoH/IP 检测分类之后，二者都先于后续国外学术、AI、游戏、开发和媒体分类。既有指定目标拒绝、Direct/Global 模式、LAN、应用与用户增量、广告及 DNS 防护保持优先。用户仍可手选 `cn-direct` 的出口；教育路由省略 `action`，按普通业务规则参与应用策略重建。

后缀按域名边界匹配；全球 `.edu`、`.edu.hk`、`.edu.tw`、相似拼写或在教育域名后附加其他域名的名称不属于这份清单。学校独立域名和第三方共享 CDN 沿用其他既有规则。官方来源用于核对域名与服务范围，不代表已验证视频、下载或真实设备的全链路直连。

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

DNS 侧改用 MagicNetRules 的 `service-wechat-dns.srs`，它只由 Blackmatrix WeChat 域名源生成，并在规则构建阶段剔除非域名项；该规则继续交给 `bootstrap-local-dns`。路由层仍保留 `karing-acl4ssr-wechat.srs` 的域名 + IP 能力。不要用 `evaluate + match_response` 机械迁移 Karing 规则里的 IP；那会把它们变成真正的 DNS 响应路由条件，改变现有语义。

