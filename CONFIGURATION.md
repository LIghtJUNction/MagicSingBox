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

- 开发：GitHub、Hugging Face、GitLab、Docker、npmjs → `dev-proxy`
- 协作/社区：Notion、Discord、Slack、Reddit → 原有通信规则出口
- 媒体：Spotify、Netflix、YouTube → 原有媒体规则出口

Hugging Face 的模型下载使用开发出口，不强制套用聊天 AI 的地区限制。以上服务同时加入对应 DNS 规则，沿用原分类的解析策略。

`rules/metacubex-service-<name>.srs` 由主仓库 `hooks/pre-build/5450.update_sing_box_rules.sh` 从同一上游的 `sing/geo/geosite/<name>.srs` 打包。新增服务不再需要同步修改 shell 白名单。构建时仍须成功下载/校验实际 SRS 文件；源码测试不能替代真机连通性验证。
