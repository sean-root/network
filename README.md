# network

Surge 与 Mihomo 使用的规则集。

| 目录 | 内容 |
| --- | --- |
| [rules/surge/](rules/surge/) | Surge 规则集（`.list`） |
| [rules/mihomo/](rules/mihomo/) | Mihomo 规则集（`.yaml`），与 Surge 版内容一致 |
| [sources/](sources/) | AI 规则集中手工维护的部分 |
| [scripts/](scripts/) | 生成 AI 规则集的脚本 |

## AI 规则集如何生成

`Anthropic` 与 `OpenAI` 规则集由 [scripts/build-ai-rules.py](scripts/build-ai-rules.py) 生成，[GitHub Action](.github/workflows/update-ai-rules.yml) 每天 UTC 02:17 运行一次并提交；规则没有变化时也会提交（只更新文件头的 `UPDATED`），用来确认任务正常运行。

各来源按下列顺序合并，重复条目只保留第一次出现的位置，被更宽规则覆盖的条目（例如已被 `DOMAIN-SUFFIX,openai.com` 覆盖的子域名、被更大网段包含的 IP 段）会去掉：

1. 手工维护：[`sources/`](sources/)
2. 官方页面
   - OpenAI：[Network recommendations for ChatGPT errors on web and apps](https://help.openai.com/en/articles/9247338-network-recommendations-for-chatgpt-errors-on-web-and-apps)、[chatgpt-voice.json](https://openai.com/chatgpt-voice.json)
   - Anthropic：[IP addresses](https://platform.claude.com/docs/en/api/ip-addresses)、[Claude Code network configuration](https://code.claude.com/docs/en/network-config)、[Claude Desktop telemetry and egress](https://claude.com/docs/third-party/claude-desktop/telemetry)、[Claude Science network requirements](https://claude.com/docs/claude-science/network-requirements)。Claude 文档只收录 Anthropic 自有域名和遥测、人机验证类服务，云厂商、GitHub、软件包仓库、通用 CDN、搜索 API 不收录。
3. BGP 路由：通过 [RIPEstat](https://stat.ripe.net/) 查询 `sources/` 中各 `IP-ASN` 当前宣告的 IP 段
4. [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community) 的 `anthropic`、`openai`
5. 社区：[ip.net.coffee](https://ip.net.coffee/claude/site.html)（仅 Anthropic）
6. [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) 的 `Anthropic`、`OpenAI`，其中 `IP-ASN,20473` 不收录：该 ASN 属于 Vultr，收录会让所有 Vultr 服务器的流量都命中 OpenAI 规则

任一来源获取失败或结果明显异常时，脚本不会写入文件，Action 运行失败。
