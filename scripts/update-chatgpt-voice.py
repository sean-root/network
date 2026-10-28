#!/usr/bin/env python3
"""Sync the ChatGPT Voice IP section of the OpenAI rule sets with chatgpt-voice.json."""
import json
import pathlib
import re
import urllib.request

SOURCE = "https://openai.com/chatgpt-voice.json"
HEADER = "# ChatGPT Voice：官方 IP 清单 https://openai.com/chatgpt-voice.json"
ROOT = pathlib.Path(__file__).resolve().parent.parent
TARGETS = {
    ROOT / "rules/surge/OpenAI.list": "",
    ROOT / "rules/mihomo/OpenAI.yaml": "  - ",
}


def fetch_rules():
    request = urllib.request.Request(SOURCE, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        prefixes = json.load(response)["prefixes"]
    rules = []
    for prefix in prefixes:
        if "ipv4Prefix" in prefix:
            rules.append(f"IP-CIDR,{prefix['ipv4Prefix']},no-resolve")
        elif "ipv6Prefix" in prefix:
            rules.append(f"IP-CIDR6,{prefix['ipv6Prefix']},no-resolve")
    if not rules:
        raise SystemExit(f"{SOURCE} returned no prefixes")
    return rules


def rewrite(path, item_prefix, rules):
    text = path.read_text(encoding="utf-8")
    head, found, _ = text.partition(HEADER)
    if not found:
        raise SystemExit(f"{path}: voice section header not found")
    text = head + HEADER + "\n" + "".join(f"{item_prefix}{rule}\n" for rule in rules)
    lines = text.splitlines()
    if item_prefix:
        total = sum(1 for line in lines if line.startswith(item_prefix))
    else:
        total = sum(1 for line in lines if line.strip() and not line.startswith("#"))
    text = re.sub(r"^# TOTAL: \d+$", f"# TOTAL: {total}", text, count=1, flags=re.M)
    changed = text != path.read_text(encoding="utf-8")
    if changed:
        path.write_text(text, encoding="utf-8")
    print(f"{path.relative_to(ROOT)}: {len(rules)} voice prefixes, {total} rules{'' if changed else ' (unchanged)'}")


def main():
    rules = fetch_rules()
    for path, item_prefix in TARGETS.items():
        rewrite(path, item_prefix, rules)


if __name__ == "__main__":
    main()
