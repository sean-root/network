# Mihomo 规则集

| 文件 | 内容 | 建议策略 |
| --- | --- | --- |
| [Anthropic.yaml](Anthropic.yaml) | Claude / Anthropic 域名，登录、遥测、客服依赖，API 入站 IP 段与自有 ASN | AI |
| [OpenAI.yaml](OpenAI.yaml) | ChatGPT / OpenAI 域名，登录、验证、支付、遥测依赖，ChatGPT Voice 官方 IP 清单 | AI |
| [Downloads-CDN.yaml](Downloads-CDN.yaml) | 系统更新与大文件下载 CDN | Download |

## 引用

```yaml
rule-providers:
  AnthropicExtra: { type: http, behavior: classical, interval: 43200, path: "./rules/AnthropicExtra.yaml", url: "https://raw.githubusercontent.com/sean-root/network/main/rules/mihomo/Anthropic.yaml" }
  OpenAIExtra:    { type: http, behavior: classical, interval: 43200, path: "./rules/OpenAIExtra.yaml",    url: "https://raw.githubusercontent.com/sean-root/network/main/rules/mihomo/OpenAI.yaml" }
  DownloadExtra:  { type: http, behavior: classical, interval: 43200, path: "./rules/DownloadExtra.yaml",  url: "https://raw.githubusercontent.com/sean-root/network/main/rules/mihomo/Downloads-CDN.yaml" }

rules:
  - RULE-SET,AnthropicExtra,🤖 AI
  - RULE-SET,OpenAIExtra,🤖 AI
  - RULE-SET,DownloadExtra,📥 Download
```

## 说明

- `behavior` 必须为 `classical`：文件中混有域名、IP-CIDR 与 IP-ASN 规则，IP 类规则已逐条带 `no-resolve`。
- `IP-ASN` 规则依赖 ASN 数据库，需在 `geox-url` 中配置 `asn`。
- `path` 请使用独立文件名，避免与其他规则集（如 blackmatrix7 的 `Anthropic.yaml`）的缓存互相覆盖。
- 已包含 [blackmatrix7](https://github.com/blackmatrix7/ios_rule_script/tree/master/rule/Clash) 同名规则集的条目（OpenAI 中的 `IP-ASN,20473` 除外，该 ASN 为 Vultr 全段），可与其并用，本仓库规则集放在前面。
- 内容与 [`../surge/`](../surge/) 下的同名 `.list` 一致，修改时需同步。
