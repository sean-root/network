#!/usr/bin/env python3
"""Build the Anthropic and OpenAI rule sets for Surge and Mihomo.

Sources are merged in order (the first occurrence of a rule wins): the manual list in
sources/, official pages, RIPEstat BGP data, v2fly domain-list-community,
ip.net.coffee and blackmatrix7. Any fetch failure or implausible result aborts the
build without touching the generated files.
"""
import dataclasses
import datetime
import html
import ipaddress
import json
import pathlib
import re
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
REPO = "https://github.com/sean-root/network"
USER_AGENT = "Mozilla/5.0 (compatible; sean-root-network rule builder)"

IP_TYPES = ("IP-CIDR", "IP-CIDR6", "IP-ASN")
RULE_LINE = re.compile(r"^(DOMAIN(?:-SUFFIX|-KEYWORD|-WILDCARD|-REGEX)?|IP-CIDR6?|IP-ASN),([^,\s]+)")
HOST = r"[a-z0-9-]+(?:\.[a-z0-9-]+)+"

# IP-ASN,20473 is Vultr as a whole; blackmatrix7 lists it under OpenAI.
EXCLUDED = {("IP-ASN", "20473")}

OPENAI_HELP = "https://help.openai.com/en/articles/9247338-network-recommendations-for-chatgpt-errors-on-web-and-apps"
OPENAI_VOICE = "https://openai.com/chatgpt-voice.json"
ANTHROPIC_IPS = "https://platform.claude.com/docs/en/api/ip-addresses"
CLAUDE_DOCS = (
    "https://code.claude.com/docs/en/network-config",
    "https://claude.com/docs/third-party/claude-desktop/telemetry",
    "https://claude.com/docs/claude-science/network-requirements",
)
NET_COFFEE = "https://ip.net.coffee/claude/site.html"
V2FLY = "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/{}"
V2FLY_PAGE = "https://github.com/v2fly/domain-list-community/blob/master/data/{}"
BM7 = "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Surge/{0}/{0}.list"
BM7_PAGE = "https://github.com/blackmatrix7/ios_rule_script/tree/master/rule/Surge/{}"
RIPESTAT = "https://stat.ripe.net/data/announced-prefixes/data.json?resource=AS{}&sourceapp=sean-root-network"

# Third-party hosts from the Claude docs that are kept; everything else that is not
# Anthropic-owned (cloud providers, GitHub, package registries, CDNs) is skipped.
CLAUDE_THIRD_PARTY = ("sentry.io", "hcaptcha.com", "statsig.com", "statsigapi.net",
                      "intercom.io", "intercomcdn.com", "sift.com", "usefathom.com")
ANTHROPIC_OWNED = ("anthropic.com", "claude.ai", "claude.com", "claude.app", "clau.de",
                   "claudeusercontent.com", "claudemcpcontent.com", "claudemcpclient.com")


@dataclasses.dataclass
class Section:
    title: str
    rules: list
    lines: list = None  # manual sections keep their comments: str or rule tuple


def fail(message):
    raise SystemExit(f"error: {message}")


def require(condition, message):
    if not condition:
        fail(message)


def fetch(url, attempts=3, optional=False):
    for attempt in range(1, attempts + 1):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.read().decode("utf-8", "replace")
        except Exception as exc:  # noqa: BLE001
            if attempt == attempts:
                if optional:
                    return ""
                fail(f"fetch {url}: {exc}")
            time.sleep(5 * attempt)


def normalize(kind, value):
    if kind in ("IP-CIDR", "IP-CIDR6"):
        network = ipaddress.ip_network(value, strict=False)
        return ("IP-CIDR" if network.version == 4 else "IP-CIDR6"), str(network)
    if kind == "IP-ASN":
        return kind, value.upper().removeprefix("AS")
    if kind == "DOMAIN-REGEX":
        return kind, value
    return kind, value.lower().strip(".")


def parse_rules(text):
    rules = []
    for line in text.splitlines():
        match = RULE_LINE.match(line.strip().lstrip("-").strip())
        if match:
            rules.append(normalize(*match.groups()))
    return rules


def html_to_text(page):
    return html.unescape(re.sub(r"<[^>]+>", "\n", page))


def host_rule(token):
    wildcard = token.startswith("*.")
    return ("DOMAIN-SUFFIX" if wildcard else "DOMAIN"), token.removeprefix("*.")


def under(host, suffixes):
    return any(host == s or host.endswith("." + s) for s in suffixes)


# ---------------------------------------------------------------- sources

def manual(name):
    path = ROOT / "sources" / f"{name}.list"
    body = path.read_text(encoding="utf-8").split("\n\n", 1)[1]
    lines, rules = [], []
    for line in body.splitlines():
        parsed = parse_rules(line)
        if parsed:
            lines.append(parsed[0])
            rules.append(parsed[0])
        else:
            lines.append(line.rstrip())
    require(rules, f"{path.name} has no rules")
    return Section(f"手工维护：sources/{name}.list", rules, lines)


def openai_help():
    page = fetch(OPENAI_HELP, attempts=1, optional=True)
    if "domains to allowlist" not in page:
        # help.openai.com answers non-browser clients with a Cloudflare challenge.
        page = fetch("https://r.jina.ai/" + OPENAI_HELP)
    require("domains to allowlist" in page, "OpenAI help page: allowlist section not found")
    text = html_to_text(page) if "<html" in page.lower() else page
    allowlist = re.split(r"\n#+ |WebSocket requirements", text.split("domains to allowlist", 1)[1], maxsplit=1)[0]
    tokens = []
    for line in allowlist.splitlines():
        token = re.sub(r"^[*\-•]\s+", "", line.strip()).lower()
        if re.fullmatch(rf"(\*\.)?{HOST}", token):
            tokens.append(token)
    require(len(tokens) >= 20, f"OpenAI help page: only {len(tokens)} domains")
    rules = [host_rule(t) for t in tokens]
    rules += [("DOMAIN", h) for h in re.findall(rf"wss://({HOST})", text.lower())]
    return Section(f"OpenAI 官方：{OPENAI_HELP}", rules)


def openai_voice():
    prefixes = json.loads(fetch(OPENAI_VOICE))["prefixes"]
    rules = [normalize("IP-CIDR", p.get("ipv4Prefix") or p.get("ipv6Prefix")) for p in prefixes]
    require(len(rules) >= 50, f"chatgpt-voice.json: only {len(rules)} prefixes")
    return Section(f"ChatGPT Voice：{OPENAI_VOICE}", rules)


def anthropic_ips():
    text = fetch(ANTHROPIC_IPS + ".md").split("Phased out", 1)[0]
    rules = [normalize("IP-CIDR", c) for c in re.findall(r"`([0-9a-fA-F:.]+/\d+)`", text)]
    require(any(k == "IP-CIDR" for k, _ in rules) and any(k == "IP-CIDR6" for k, _ in rules),
            "Anthropic IP page: missing IPv4 or IPv6 ranges")
    return Section(f"Anthropic 官方：{ANTHROPIC_IPS}", rules)


def claude_docs(owned, skipped):
    sections = []
    for url in CLAUDE_DOCS:
        text = fetch(url + ".md").lower()
        rules = []
        for token in dict.fromkeys(re.findall(rf"`(\*\.)?({HOST})`", text)):
            rule = host_rule("".join(token))
            if under(rule[1], owned) or under(rule[1], CLAUDE_THIRD_PARTY) or "datadog" in rule[1]:
                rules.append(rule)
            else:
                skipped.add(rule[1])
        require(len(rules) >= 3, f"{url}: only {len(rules)} Claude hosts")
        sections.append(Section(f"Claude 官方：{url}", rules))
    return sections


def ripestat(asns):
    rules = []
    for asn in asns:
        data = json.loads(fetch(RIPESTAT.format(asn)))
        require(data.get("status") == "ok", f"RIPEstat AS{asn}: status {data.get('status')}")
        rules += [normalize("IP-CIDR", p["prefix"]) for p in data["data"]["prefixes"]]
    title = "、".join(f"AS{a}" for a in asns)
    return Section(f"BGP 路由（RIPEstat）：{title}", rules)


def v2fly(name, seen=None):
    seen = seen if seen is not None else set()
    seen.add(name)
    rules = []
    for line in fetch(V2FLY.format(name)).splitlines():
        entry = line.split("#", 1)[0].strip()
        entry = re.split(r"\s+@", entry, maxsplit=1)[0].strip()
        if not entry:
            continue
        kind, _, value = entry.partition(":") if re.match(r"^(full|domain|keyword|regexp|include):", entry) else ("domain", "", entry)
        if kind == "include":
            if value not in seen:
                rules += v2fly(value, seen).rules
            continue
        rules.append(normalize({"full": "DOMAIN", "domain": "DOMAIN-SUFFIX",
                                "keyword": "DOMAIN-KEYWORD", "regexp": "DOMAIN-REGEX"}[kind], value))
    require(len(rules) >= 5, f"v2fly {name}: only {len(rules)} entries")
    return Section(f"v2fly：{V2FLY_PAGE.format(name)}", rules)


def net_coffee():
    rules = parse_rules(html_to_text(fetch(NET_COFFEE)))
    require(len(rules) >= 10, f"ip.net.coffee: only {len(rules)} rules")
    return Section(f"社区：{NET_COFFEE}", rules)


def blackmatrix7(name):
    rules = parse_rules(fetch(BM7.format(name)))
    require(rules, f"blackmatrix7 {name}: empty")
    return Section(f"blackmatrix7：{BM7_PAGE.format(name)}", rules)


# ---------------------------------------------------------------- merge

def merge(sections):
    seen, removed = set(), 0
    for section in sections:
        kept = []
        for rule in section.rules:
            if rule not in EXCLUDED and rule not in seen:
                seen.add(rule)
                kept.append(rule)
        section.rules = kept

    suffixes = {v for k, v in seen if k == "DOMAIN-SUFFIX"}
    networks = [ipaddress.ip_network(v) for k, v in seen if k in ("IP-CIDR", "IP-CIDR6")]

    def covered(rule):
        kind, value = rule
        if kind in ("DOMAIN", "DOMAIN-SUFFIX"):
            labels = value.split(".")
            start = 0 if kind == "DOMAIN" else 1
            return any(".".join(labels[i:]) in suffixes for i in range(start, len(labels)))
        if kind in ("IP-CIDR", "IP-CIDR6"):
            network = ipaddress.ip_network(value)
            return any(network != other and network.version == other.version and network.subnet_of(other)
                       for other in networks)
        return False

    for section in sections:
        before = len(section.rules)
        section.rules = [r for r in section.rules if not covered(r)]
        removed += before - len(section.rules)
        if section.lines is not None:
            section.lines = [x for x in section.lines if isinstance(x, str) or x in section.rules]
    return sum(len(s.rules) for s in sections), removed


# ---------------------------------------------------------------- output

def regex_to_wildcard(pattern):
    wildcard = re.sub(r"\\S\+|\\w\+|\\d\+|\.\+|\.\*|\[\^\.\]\+|\[[a-z0-9\\-]+\]\+", "*",
                      pattern.removeprefix("^").removesuffix("$")).replace("\\.", ".")
    return None if re.search(r"[\\()\[\]{}|?+^$]", wildcard) else wildcard


def wildcard_to_regex(wildcard):
    return "^" + re.escape(wildcard).replace(r"\*", ".*").replace(r"\?", ".") + "$"


def render(rule, target, notes):
    kind, value = rule
    if target == "surge" and kind == "DOMAIN-REGEX":
        wildcard = regex_to_wildcard(value)
        if wildcard is None:
            notes.append(f"surge: skipped regex {value}")
            return None
        kind, value = "DOMAIN-WILDCARD", wildcard
    if target == "mihomo" and kind == "DOMAIN-WILDCARD":
        kind, value = "DOMAIN-REGEX", wildcard_to_regex(value)
    text = f"{kind},{value}" + (",no-resolve" if kind in IP_TYPES else "")
    if target == "mihomo":
        return "  - " + (f"'{text}'" if kind == "DOMAIN-REGEX" else text)
    return text


def body_lines(sections, target, notes):
    comment = "  # " if target == "mihomo" else "# "
    out = []
    for section in sections:
        if not section.rules:
            continue
        out += ["", comment + section.title]
        items = section.lines if section.lines is not None else section.rules
        for item in items:
            if isinstance(item, str):
                if not item:
                    out.append("")
                elif item.startswith("#"):
                    out.append(comment + item.lstrip("# ").rstrip())
                continue
            rendered = render(item, target, notes)
            if rendered:
                out.append(rendered)
    collapsed = []
    for line in out:
        if line == "" and collapsed and collapsed[-1] == "":
            continue
        collapsed.append(line)
    return collapsed


def render_file(name, sections, target, updated, notes):
    path = ROOT / (f"rules/surge/{name}.list" if target == "surge" else f"rules/mihomo/{name}.yaml")
    body = body_lines(sections, target, notes)
    prefix = "  - " if target == "mihomo" else ""
    total = sum(1 for line in body if line and not line.lstrip().startswith("#") and line.startswith(prefix))
    if path.exists():
        previous = re.search(r"^# TOTAL: (\d+)$", path.read_text(encoding="utf-8"), re.M)
        require(not previous or total >= int(previous.group(1)) * 0.8,
                f"{path.relative_to(ROOT)}: {total} rules, down from {previous and previous.group(1)}")
    header = [f"# NAME: {name}", f"# REPO: {REPO}", f"# UPDATED: {updated}", f"# TOTAL: {total}"]
    if target == "mihomo":
        body = ["", "payload:"] + body[1:]
    return path, "\n".join(header + body) + "\n", total


def asns_of(section):
    return [v for k, v in section.rules if k == "IP-ASN"]


def main():
    skipped, notes = set(), []

    v2fly_anthropic = v2fly("anthropic")
    owned = set(ANTHROPIC_OWNED) | {v for k, v in v2fly_anthropic.rules if k == "DOMAIN-SUFFIX"}
    anthropic_manual = manual("Anthropic")
    anthropic = [anthropic_manual, anthropic_ips(), *claude_docs(owned, skipped),
                 ripestat(asns_of(anthropic_manual)), v2fly_anthropic, net_coffee(), blackmatrix7("Anthropic")]

    openai_manual = manual("OpenAI")
    openai = [openai_manual, openai_help(), ripestat(asns_of(openai_manual)), v2fly("openai"),
              blackmatrix7("OpenAI"), openai_voice()]

    updated = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for name, sections in (("Anthropic", anthropic), ("OpenAI", openai)):
        total, removed = merge(sections)
        print(f"{name}: {total} rules after merge, {removed} covered by broader rules")
        for section in sections:
            print(f"  {len(section.rules):4d}  {section.title}")
    outputs = [render_file(name, sections, target, updated, notes)
               for name, sections in (("Anthropic", anthropic), ("OpenAI", openai))
               for target in ("surge", "mihomo")]
    for path, text, total in outputs:
        path.write_text(text, encoding="utf-8")
        print(f"{path.relative_to(ROOT)}: {total} rules")
    for note in dict.fromkeys(notes):
        print(note)
    if skipped:
        print("skipped non-Anthropic hosts from Claude docs:", ", ".join(sorted(skipped)))


if __name__ == "__main__":
    main()
