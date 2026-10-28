# Surge 规则集

| 文件 | 内容 | 建议策略 |
| --- | --- | --- |
| [Anthropic.list](Anthropic.list) | Claude / Anthropic 域名，登录、遥测、客服依赖，API 入站 IP 段与自有 ASN | AI |
| [OpenAI.list](OpenAI.list) | ChatGPT / OpenAI 域名，登录、验证、支付、遥测依赖，ChatGPT Voice 官方 IP 清单 | AI |
| [Downloads-CDN.list](Downloads-CDN.list) | 系统更新与大文件下载 CDN | Download |

## 引用

```ini
[Rule]
RULE-SET, https://raw.githubusercontent.com/sean-root/network/main/rules/surge/Anthropic.list, AI, update-interval=43200
RULE-SET, https://raw.githubusercontent.com/sean-root/network/main/rules/surge/OpenAI.list, AI, update-interval=43200
RULE-SET, https://raw.githubusercontent.com/sean-root/network/main/rules/surge/Downloads-CDN.list, Download, update-interval=43200
```

## 说明

- IP 类规则已逐条带 `no-resolve`，`RULE-SET` 行无需再加。
- ChatGPT Voice IP 段由 [GitHub Action](../../.github/workflows/update-chatgpt-voice.yml) 每天从 `chatgpt-voice.json` 自动同步，请勿手动编辑该段。
- 已包含 [blackmatrix7](https://github.com/blackmatrix7/ios_rule_script/tree/master/rule/Surge) 同名规则集的条目（OpenAI 中的 `IP-ASN,20473` 除外，该 ASN 为 Vultr 全段），可与其并用，本仓库规则集放在前面。
- 数据来源：
  - [Network recommendations for ChatGPT errors on web and apps](https://help.openai.com/en/articles/9247338-network-recommendations-for-chatgpt-errors-on-web-and-apps)
  - [chatgpt-voice.json](https://openai.com/chatgpt-voice.json)
  - [Claude Desktop telemetry and egress](https://claude.com/docs/third-party/claude-desktop/telemetry)
  - [Anthropic IP addresses](https://platform.claude.com/docs/en/api/ip-addresses)
- 内容与 [`../mihomo/`](../mihomo/) 下的同名 `.yaml` 一致，修改时需同步。
