# 2026-09 DNS 与路由更新

此次修改按 sing-box 1.14 系列的稳定版语义检查，不升级 MagicNet 的内核，不套用 1.15 预览版的 TUN 栈迁移。

## 改动

- 路由首条按目标端口 53 执行 `hijack-dns`，不再让普通 TCP/UDP DNS 等待嗅探，也不会先命中 Direct/Global、LAN 或应用规则。保留后面的 `protocol: dns` 接管规则，用于已识别的非标准端口 DNS。不要把 853 或整个 UDP/443 当作明文 DNS 劫持。
- 把 `metacubex-geosite-geolocation-not-cn` 放到末尾 GeoIP 规则之前。已知海外域名不会仅因地址命中国内 GeoIP 就落入 `cn-direct`；更早的国内域名、具体服务、应用和模式选择仍保留原有优先级。
- AliDNS 和 Google DoH 显式声明 `tls.enabled: true`，保留原有服务器 IP、证书主机名和 detour。
- 沿用本仓库此前合入的 `service-wechat-dns` 域名专用规则。混合域名/IP 的 `karing-acl4ssr-wechat` 只用于流量路由，不再用作 DNS 查询分类。MagicNet 集成时必须同时提供 `service-wechat-dns.srs`。

## 保留的策略与限制

`route.default_domain_resolver` 仍是无需代理的 `bootstrap-local-dns`，避免解析代理节点本身时再次依赖代理。默认 `dns.final` 也仍保持原值；这次不把未知域名统一改为海外 DNS，也不宣称完全消除 DNS 泄漏。国内直连、海外服务分流、选择器和订阅节点筛选不变。

局域网和 Tailscale 的现有例外、IPv4 优先/双栈、1400 MTU、mixed 栈、TUN/eBPF 的运行时选择保持不变。没有启用 FakeIP，没有全局禁止 QUIC，没有改动停止服务后的防火墙/路由恢复代码。

此文件是 **MagicNet 的打包模板**，不是已经包含用户节点的手机运行配置。`proxy` 和 AI 选择器在尚未导入订阅时有意默认阻断。不能直接用仓库的 `config.json` 覆盖已生成的设备配置；需要 MagicNet 的规则资源、订阅合并和配置规范化流程。仓库保留的特殊出站还需由现有运行时处理，不能把这里的测试当作上游原生内核的完整兼容认证。

## 验证

```sh
python3 generate.py --check
python3 -m unittest discover -s tests -v
```

新增测试验证规则顺序及冲突场景；规则集命中使用人工构造的成员关系，不冒充在线规则集测试。部署前仍需运行 MagicNet 的实际资源测试、最终配置的 `sing-box check`，并进行设备联网/重启/停用回归。

官方依据：

- https://github.com/SagerNet/sing-box/releases
- https://sing-box.sagernet.org/migration/
- https://sing-box.sagernet.org/configuration/route/rule_action/
- https://sing-box.sagernet.org/configuration/dns/server/https/
