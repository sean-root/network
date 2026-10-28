# Mihomo 规则集

| 文件 | 内容 | 建议策略 |
| --- | --- | --- |
| [Anthropic.yaml](Anthropic.yaml) | Claude / Anthropic 域名，登录、遥测、客服依赖，自有 IP 段与 ASN | AI |
| [OpenAI.yaml](OpenAI.yaml) | ChatGPT / OpenAI 域名，登录、验证、支付、遥测依赖，自有 ASN，ChatGPT Voice IP | AI |
| [Downloads-CDN.yaml](Downloads-CDN.yaml) | 系统更新与大文件下载 CDN | Download |

## 引用

```yaml
rule-providers:
  Anthropic:     { type: http, behavior: classical, interval: 43200, path: "./rules/Anthropic.yaml",     url: "https://raw.githubusercontent.com/sean-root/network/main/rules/mihomo/Anthropic.yaml" }
  OpenAI:        { type: http, behavior: classical, interval: 43200, path: "./rules/OpenAI.yaml",        url: "https://raw.githubusercontent.com/sean-root/network/main/rules/mihomo/OpenAI.yaml" }
  Downloads-CDN: { type: http, behavior: classical, interval: 43200, path: "./rules/Downloads-CDN.yaml", url: "https://raw.githubusercontent.com/sean-root/network/main/rules/mihomo/Downloads-CDN.yaml" }

rules:
  - RULE-SET,Anthropic,🤖 AI
  - RULE-SET,OpenAI,🤖 AI
  - RULE-SET,Downloads-CDN,📥 Download
```

## 说明

- `Anthropic.yaml`、`OpenAI.yaml` 已整合官方文档、BGP 路由、v2fly、ip.net.coffee 与 blackmatrix7，单独使用即可，无需再引用 blackmatrix7 的 Anthropic / OpenAI 规则集。数据来源与生成方式见[仓库说明](../../README.md#ai-规则集如何生成)。
- 这两个文件每天自动生成，请勿手动编辑；需要增减规则时修改 [`sources/`](../../sources/)。
- `behavior` 必须为 `classical`：文件中混有域名、域名正则、IP-CIDR 与 IP-ASN 规则，IP 类规则已逐条带 `no-resolve`。
- `IP-ASN` 规则依赖 ASN 数据库，需在 `geox-url` 中配置 `asn`。
- 内容与 [`../surge/`](../surge/) 下的同名 `.list` 一致，唯一区别是域名正则规则在本版使用 `DOMAIN-REGEX`。
- `Downloads-CDN.yaml` 为手工维护。
