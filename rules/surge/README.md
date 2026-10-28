# Surge 规则集

| 文件 | 内容 | 建议策略 |
| --- | --- | --- |
| [Anthropic.list](Anthropic.list) | Claude / Anthropic 域名，登录、遥测、客服依赖，自有 IP 段与 ASN | AI |
| [OpenAI.list](OpenAI.list) | ChatGPT / OpenAI 域名，登录、验证、支付、遥测依赖，自有 ASN，ChatGPT Voice IP | AI |
| [Downloads-CDN.list](Downloads-CDN.list) | 系统更新与大文件下载 CDN | Download |

## 引用

```ini
[Rule]
RULE-SET, https://raw.githubusercontent.com/sean-root/network/main/rules/surge/Anthropic.list, AI, update-interval=43200
RULE-SET, https://raw.githubusercontent.com/sean-root/network/main/rules/surge/OpenAI.list, AI, update-interval=43200
RULE-SET, https://raw.githubusercontent.com/sean-root/network/main/rules/surge/Downloads-CDN.list, Download, update-interval=43200
```

## 说明

- `Anthropic.list`、`OpenAI.list` 已整合官方文档、BGP 路由、v2fly、ip.net.coffee 与 blackmatrix7，单独使用即可，无需再引用 blackmatrix7 的 Anthropic / OpenAI 规则集。数据来源与生成方式见[仓库说明](../../README.md#ai-规则集如何生成)。
- 这两个文件每天自动生成，请勿手动编辑；需要增减规则时修改 [`sources/`](../../sources/)。
- IP 类规则已逐条带 `no-resolve`，`RULE-SET` 行无需再加。
- 内容与 [`../mihomo/`](../mihomo/) 下的同名 `.yaml` 一致，唯一区别是域名正则规则在本版改写为 `DOMAIN-WILDCARD`。
- `Downloads-CDN.list` 为手工维护。
