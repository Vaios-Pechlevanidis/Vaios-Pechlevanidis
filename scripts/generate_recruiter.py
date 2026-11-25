#!/usr/bin/env python3
"""Builds the recruiter-style profile README and its SVG cards from live GitHub data.

Layout follows the "Recruiter-ready" README idea: hero, quick-scan facts,
proof metrics, selected work, technical toolkit, consistency signal.

Run locally:  GITHUB_TOKEN=$(gh auth token) python3 scripts/generate_recruiter.py
In Actions:   .github/workflows/readme.yml runs it daily with GITHUB_TOKEN.

Output: README.md and assets/recruiter/{stats,projects,stack,heatmap}.svg
"""
import datetime as dt
import html
import json
import os
import subprocess
import sys
import urllib.request

LOGIN = "Vaios-Pechlevanidis"
ROLE = "Frontend or full-stack engineer"
STATUS = "Building and sharing work in public"
PITCH = "Open to thoughtful teams, ambitious products, and useful engineering work."
FALLBACK_DESC = "A selected public project."
# Repos shown under "Selected work". Empty list = use the pinned repos.
FEATURED = []

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ASSETS = os.path.join(ROOT, "assets", "recruiter")

# ------------------------------------------------------------------ palette
BG = "#0d1117"
PANEL = "#111722"
BORDER = "#263041"
TEXT = "#e6edf3"
MUTED = "#8b949e"
ACCENT = "#58a6ff"
GREEN = "#3fb950"
PURPLE = "#8957e5"
TEAL = "#1f8fb3"
HEAT = ["#161d29", "#0f3a4a", "#11607a", "#1f8fb3", "#5cc8ff"]
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,monospace"

QUERY = """
query($login: String!) {
  user(login: $login) {
    name bio location avatarUrl url
    followers { totalCount }
    pinnedItems(first: 6, types: REPOSITORY) { nodes { ... on Repository { name } } }
    repositories(ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false, first: 100,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      totalCount
      nodes {
        name description url stargazerCount forkCount pushedAt
        primaryLanguage { name color }
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          totalSize edges { size node { name color } }
        }
      }
    }
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { contributionCount date } }
      }
    }
  }
}
"""


# ------------------------------------------------------------------ data
def token():
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if tok:
        return tok
    try:
        return subprocess.check_output(["gh", "auth", "token"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        sys.exit("Set GITHUB_TOKEN (or log in with the gh CLI).")


def fetch():
    body = json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql", data=body,
        headers={"Authorization": f"bearer {token()}", "User-Agent": "profile-readme"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    if data.get("errors"):
        sys.exit(json.dumps(data["errors"], indent=2))
    return data["data"]["user"]


def summarize(u):
    repos = u["repositories"]["nodes"]
    langs, colors = {}, {}
    for r in repos:
        for e in r["languages"]["edges"]:
            n = e["node"]["name"]
            langs[n] = langs.get(n, 0) + e["size"]
            colors[n] = e["node"]["color"] or MUTED
    total = sum(langs.values()) or 1
    languages = [(n, s * 100 / total, colors[n])
                 for n, s in sorted(langs.items(), key=lambda kv: -kv[1])]

    cal = u["contributionsCollection"]["contributionCalendar"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]

    by_name = {r["name"]: r for r in repos}
    names = FEATURED or [p["name"] for p in u["pinnedItems"]["nodes"] if p]
    featured = [by_name[n] for n in names if n in by_name]
    for r in repos:  # top up with recently pushed repos
        if len(featured) >= 4:
            break
        if r not in featured and r["name"] != LOGIN:
            featured.append(r)

    return {
        "name": u["name"] or LOGIN,
        "bio": " ".join((u["bio"] or "").split()),
        "location": u["location"],
        "avatar": u["avatarUrl"],
        "url": u["url"],
        "followers": u["followers"]["totalCount"],
        "repo_count": u["repositories"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in repos),
        "contributions": cal["totalContributions"],
        "active_days": sum(1 for d in days if d["contributionCount"] > 0),
        "weeks": cal["weeks"],
        "languages": languages,
        "featured": featured[:4],
    }


# ------------------------------------------------------------------ svg helpers
def esc(s):
    return html.escape(str(s), quote=True)


def text_w(s, size, mono=False):
    return len(s) * size * (0.6 if mono else 0.56)


def clip(s, size, width, mono=False):
    if text_w(s, size, mono) <= width:
        return s
    while s and text_w(s + "…", size, mono) > width:
        s = s[:-1]
    return s.rstrip() + "…"


def wrap(s, size, width, lines, mono=False):
    words, out, cur = s.split(), [], ""
    for w in words:
        nxt = f"{cur} {w}".strip()
        if text_w(nxt, size, mono) <= width:
            cur = nxt
            continue
        out.append(cur)
        cur = w
        if len(out) == lines:
            break
    if len(out) < lines and cur:
        out.append(cur)
    if len(out) == lines and " ".join(out) != " ".join(words):
        out[-1] = clip(out[-1] + " …", size, width, mono)
    return [line for line in out if line]


def ago(iso):
    days = (dt.datetime.now(dt.timezone.utc)
            - dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))).days
    if days < 1:
        return "today"
    if days < 30:
        return f"{days}d ago"
    if days < 365:
        return f"{days // 30}mo ago"
    return f"{days // 365}y ago"


STYLE = """
<style>
  .t{font-family:%(sans)s;fill:%(text)s}
  .m{font-family:%(mono)s}
  .muted{fill:%(muted)s}
  .fade{opacity:0;animation:fade .7s ease-out forwards}
  .grow{transform-box:fill-box;transform-origin:left center;transform:scaleX(0);
        animation:grow 1s cubic-bezier(.2,.8,.2,1) forwards}
  .pop{opacity:0;animation:pop .4s ease-out forwards}
  .ring{stroke-dasharray:0 200;animation:ring 1.2s ease-out forwards}
  .blink{animation:blink 1.1s steps(1) infinite}
  @keyframes fade{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
  @keyframes grow{to{transform:scaleX(1)}}
  @keyframes pop{to{opacity:1}}
  @keyframes ring{to{stroke-dasharray:var(--d) 200}}
  @keyframes blink{50%%{opacity:0}}
  @media (prefers-reduced-motion:reduce){
    .fade,.pop{opacity:1!important;animation:none!important}
    .grow{transform:none!important;animation:none!important}
    .ring{stroke-dasharray:var(--d) 200!important;animation:none!important}
  }
</style>
""" % {"sans": SANS, "mono": MONO, "text": TEXT, "muted": MUTED}


def card(w, h, title, subtitle, body, tag=""):
    tag_svg = (f'<text x="{w - 40}" y="52" text-anchor="end" class="t m" font-size="12" '
               f'fill="{ACCENT}" style="fill:{ACCENT}">{esc(tag)}'
               f'<tspan class="blink"> _</tspan></text>') if tag else ""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}">
<title>{esc(title)}</title>{STYLE}
<defs>
  <radialGradient id="g1" cx="78%" cy="0%" r="55%"><stop offset="0" stop-color="{GREEN}" stop-opacity=".22"/><stop offset="1" stop-color="{GREEN}" stop-opacity="0"/></radialGradient>
  <radialGradient id="g2" cx="50%" cy="105%" r="45%"><stop offset="0" stop-color="{PURPLE}" stop-opacity=".35"/><stop offset="1" stop-color="{PURPLE}" stop-opacity="0"/></radialGradient>
  <radialGradient id="g3" cx="102%" cy="60%" r="35%"><stop offset="0" stop-color="{TEAL}" stop-opacity=".28"/><stop offset="1" stop-color="{TEAL}" stop-opacity="0"/></radialGradient>
  <clipPath id="cl"><rect width="{w}" height="{h}" rx="16"/></clipPath>
</defs>
<g clip-path="url(#cl)">
  <rect width="{w}" height="{h}" fill="{BG}"/>
  <rect width="{w}" height="{h}" fill="url(#g1)"/><rect width="{w}" height="{h}" fill="url(#g2)"/><rect width="{w}" height="{h}" fill="url(#g3)"/>
</g>
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="16" fill="none" stroke="{BORDER}"/>
<rect x="14.5" y="14.5" width="{w - 29}" height="{h - 29}" rx="11" fill="none" stroke="#ffffff" stroke-opacity=".06"/>
<text x="34" y="52" class="t fade" font-size="20" font-weight="700">{esc(title)}</text>
<text x="34" y="72" class="t muted fade" font-size="12" letter-spacing=".4" style="animation-delay:.1s">{esc(subtitle)}</text>
{tag_svg}
{body}
</svg>
"""


# ------------------------------------------------------------------ cards
def stats_svg(d):
    w, h = 840, 250
    tiles = [("Repositories", d["repo_count"]), ("Stars", d["stars"]),
             ("Contributions", d["contributions"]), ("Followers", d["followers"])]
    tw, gap, x0 = 180, 12, 34
    body = []
    for i, (label, val) in enumerate(tiles):
        x = x0 + i * (tw + gap)
        delay = .15 + i * .1
        body.append(f'<g class="fade" style="animation-delay:{delay:.2f}s">'
                    f'<rect x="{x}" y="92" width="{tw}" height="66" rx="10" fill="{PANEL}" fill-opacity=".8" stroke="{BORDER}"/>'
                    f'<text x="{x + 16}" y="125" class="t" font-size="24" font-weight="700">{val}</text>'
                    f'<text x="{x + 16}" y="145" class="t muted" font-size="11" letter-spacing=".6">{label.upper()}</text></g>')
    # weekly contribution sparkline
    weekly = [sum(dd["contributionCount"] for dd in wk["contributionDays"]) for wk in d["weeks"]]
    sx, sy, sw, sh = 34, 176, w - 68, 44
    peak = max(weekly) or 1
    pts = [(sx + i * sw / max(len(weekly) - 1, 1), sy + sh - v / peak * sh) for i, v in enumerate(weekly)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"{sx},{sy + sh} {line} {sx + sw},{sy + sh}"
    body.append(f'<defs><linearGradient id="sp" x1="0" y1="0" x2="0" y2="1">'
                f'<stop offset="0" stop-color="{ACCENT}" stop-opacity=".35"/><stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/></linearGradient></defs>'
                f'<g class="fade" style="animation-delay:.6s"><polygon points="{area}" fill="url(#sp)"/>'
                f'<polyline points="{line}" fill="none" stroke="{ACCENT}" stroke-width="1.6" stroke-linejoin="round"/></g>'
                f'<text x="{w - 34}" y="{sy - 4}" text-anchor="end" class="t muted m fade" font-size="10" style="animation-delay:.6s">'
                f'{d["active_days"]} active days · weekly contributions, last 12 months</text>')
    return card(w, h, "Profile Signal", "Live GitHub stats, refreshed daily", "\n".join(body))


def projects_svg(d):
    cw, ch, gap = 492, 150, 14
    rows = len(d["featured"])
    w, h = 560, 96 + rows * (ch + gap) + 20
    body = [f'<text x="{w - 34}" y="52" text-anchor="end" class="t muted m" font-size="11">{len(d["featured"])} projects</text>']
    for i, r in enumerate(d["featured"]):
        x = 34
        y = 96 + i * (ch + gap)
        lang = r["primaryLanguage"] or {"name": "Code", "color": MUTED}
        total = r["languages"]["totalSize"] or 1
        share = next((e["size"] for e in r["languages"]["edges"] if e["node"]["name"] == lang["name"]), total)
        pct = round(share * 100 / total) if r["languages"]["totalSize"] else 100
        circ = 2 * 3.14159 * 18
        desc = wrap(r["description"] or FALLBACK_DESC, 11.5, cw - 100, 2, mono=True)
        pill_w = text_w(lang["name"], 10.5, True) + 18
        delay = .15 + i * .12
        body.append(
            f'<g class="fade" style="animation-delay:{delay:.2f}s">'
            f'<a href="{esc(r["url"])}"><rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="10" fill="{PANEL}" fill-opacity=".85" stroke="{BORDER}"/></a>'
            f'<text x="{x + 14}" y="{y + 22}" class="t muted m" font-size="10">{esc(clip("⌂ " + LOGIN + "/" + r["name"], 10, cw - 50, True))}</text>'
            f'<circle cx="{x + cw - 16}" cy="{y + 18}" r="3" fill="{MUTED}" fill-opacity=".6"/>'
            f'<line x1="{x}" y1="{y + 32}" x2="{x + cw}" y2="{y + 32}" stroke="{BORDER}"/>'
            f'<text x="{x + 14}" y="{y + 56}" class="t m" font-size="15" font-weight="700">{esc(clip(r["name"], 15, cw - 90, True))}</text>'
            + "".join(f'<text x="{x + 14}" y="{y + 78 + j * 16}" class="t muted m" font-size="11.5">{esc(t)}</text>' for j, t in enumerate(desc))
            + f'<rect x="{x + 14}" y="{y + 108}" width="{pill_w:.0f}" height="18" rx="9" fill="{lang["color"]}" fill-opacity=".18" stroke="{lang["color"]}" stroke-opacity=".5"/>'
            f'<text x="{x + 14 + pill_w / 2:.0f}" y="{y + 121}" text-anchor="middle" class="t m" font-size="10.5">{esc(lang["name"])}</text>'
            f'<text x="{x + 14}" y="{y + ch - 8}" class="t muted m" font-size="10">★ {r["stargazerCount"]}   ⑂ {r["forkCount"]}   · updated {ago(r["pushedAt"])}</text>'
            f'<circle cx="{x + cw - 40}" cy="{y + 80}" r="18" fill="none" stroke="{BORDER}" stroke-width="5"/>'
            f'<circle cx="{x + cw - 40}" cy="{y + 80}" r="18" fill="none" stroke="{lang["color"]}" stroke-width="5" stroke-linecap="round" '
            f'transform="rotate(-90 {x + cw - 40} {y + 80})" class="ring" style="--d:{circ * pct / 100:.1f};animation-delay:{delay + .3:.2f}s"/>'
            f'<text x="{x + cw - 40}" y="{y + 84}" text-anchor="middle" class="t m" font-size="10" font-weight="700">{pct}%</text>'
            '</g>')
    return card(w, h, "PROJECTS.LIST", "~/projects $ ls --pinned", "\n".join(body))


def stack_svg(d):
    langs = d["languages"][:6]
    w, h = 840, 104 + len(langs) * 34 + 20
    bx, bw = 170, w - 170 - 100
    body = []
    for i, (name, pct, color) in enumerate(langs):
        y = 100 + i * 34
        delay = .15 + i * .1
        fill = max(bw * pct / 100, 4)
        body.append(
            f'<g class="fade" style="animation-delay:{delay:.2f}s">'
            f'<circle cx="40" cy="{y + 9}" r="5" fill="{color}"/>'
            f'<text x="54" y="{y + 13}" class="t" font-size="13" font-weight="600">{esc(name)}</text>'
            f'<rect x="{bx}" y="{y + 3}" width="{bw}" height="12" rx="6" fill="{PANEL}" stroke="{BORDER}"/>'
            f'<rect x="{bx}" y="{y + 3}" width="{fill:.1f}" height="12" rx="6" fill="{color}" class="grow" style="animation-delay:{delay + .1:.2f}s"/>'
            f'<text x="{w - 34}" y="{y + 13}" text-anchor="end" class="t m" font-size="12">{pct:.1f}%</text></g>')
    return card(w, h, "Language Stack", "Repository-weighted technologies", "\n".join(body), tag="> stack.scan")


def heatmap_svg(d):
    weeks = d["weeks"]
    cell, gap = 11, 3
    w = 840
    gx = (w - len(weeks) * (cell + gap) + gap) / 2
    gy = 104
    h = gy + 7 * (cell + gap) + 52
    counts = sorted(c for wk in weeks for c in (dd["contributionCount"] for dd in wk["contributionDays"]) if c)
    q = [counts[int(len(counts) * f)] for f in (.25, .5, .75)] if counts else [1, 2, 3]

    def level(c):
        return 0 if c == 0 else 1 + sum(c > t for t in q)

    body, months, last = [], [], None
    for i, wk in enumerate(weeks):
        first = wk["contributionDays"][0]["date"]
        m = dt.date.fromisoformat(first).strftime("%b")
        if m != last and i < len(weeks) - 2:
            months.append((i, m))
            last = m
        for dd in wk["contributionDays"]:
            wd = (dt.date.fromisoformat(dd["date"]).weekday() + 1) % 7  # Sunday = 0
            x, y = gx + i * (cell + gap), gy + wd * (cell + gap)
            body.append(f'<rect x="{x:.1f}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{HEAT[level(dd["contributionCount"])]}" '
                        f'class="pop" style="animation-delay:{.2 + i * .018:.3f}s"><title>{dd["date"]}: {dd["contributionCount"]}</title></rect>')
    for i, m in months:
        body.append(f'<text x="{gx + i * (cell + gap):.1f}" y="{gy - 8}" class="t muted" font-size="10">{m}</text>')
    lx = w - 34 - 5 * 14 - 30
    body.append(f'<text x="{lx - 8}" y="52" text-anchor="end" class="t muted" font-size="10">Less</text>')
    body += [f'<rect x="{lx + i * 14}" y="43" width="11" height="11" rx="2" fill="{c}"/>' for i, c in enumerate(HEAT)]
    body.append(f'<text x="{lx + 5 * 14 + 4}" y="52" class="t muted" font-size="10">More</text>')
    body.append(f'<text x="{gx:.1f}" y="{h - 26}" class="t muted m fade" font-size="10" style="animation-delay:1.2s">'
                f'{d["active_days"]} active days · {d["contributions"]} contributions</text>')
    return card(w, h, "Contribution Activity", f'{d["contributions"]} contributions in the last year', "\n".join(body))


# ------------------------------------------------------------------ readme
def short(s, n=150):
    s = " ".join((s or FALLBACK_DESC).split())
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + " …"


def readme(d):
    gh = d["url"]
    top = [n for n, _, _ in d["languages"][:3]]
    bio_html = esc(d["bio"])
    f = d["featured"]

    def lang(r):
        return r["primaryLanguage"]["name"] if r["primaryLanguage"] else "Code"

    lead = f[0]
    rest = "\n".join(
        f'- **[{r["name"]}]({r["url"]})** · <sub>{lang(r)} · ⭐ {r["stargazerCount"]}</sub><br>'
        f'{esc(short(r["description"], 160))}'
        for r in f[1:4])
    toolkit = "".join(
        f'<td width="20%" align="center"><strong>{esc(n)}</strong><br><sub>{p:.0f}% of public code</sub></td>'
        for n, p, _ in d["languages"][:5])
    location = f"\n<p><sub>📍 Based in {esc(d['location'])}</sub></p>" if d["location"] else ""

    return f"""<!-- Generated by scripts/generate_recruiter.py — edit the script, not this file. -->
<div align="center">
<table width="100%"><tr><td width="64%" valign="middle">

<sub>RECRUITER SIGNAL BRIEF · {LOGIN.lower()}</sub>

<h1>{esc(d["name"])}</h1>
<h2>{esc(ROLE)}</h2>
<p>{bio_html}</p>
<p><strong>🟢 {esc(STATUS)}</strong></p>{location}
<p><a href="{gh}"><img src="https://img.shields.io/badge/GitHub-{LOGIN.replace("-", "--")}-0d1117?style=for-the-badge&logo=github&logoColor=white" alt="GitHub"/></a></p>

</td><td width="36%" align="center" valign="middle">
<img width="180" src="{d["avatar"]}" alt="{esc(d["name"])} GitHub avatar"/>
</td></tr></table>
</div>

## What teams can evaluate quickly

<table width="100%"><tr>
<td width="33%" valign="top"><h3>🎯 Role fit</h3><p>{esc(ROLE)} · {" · ".join(top)}</p></td>
<td width="33%" valign="top"><h3>📦 Public proof</h3><p>{d["repo_count"]} repositories · {d["stars"]} stars</p></td>
<td width="33%" valign="top"><h3>📈 Momentum</h3><p>{d["contributions"]} contributions · {d["active_days"]} active days</p></td>
</tr></table>

<sub>{bio_html}</sub>

## Proof at a glance

<table width="100%"><tr>
<td width="25%" align="center"><strong>{d["repo_count"]}</strong><br><sub>Repositories</sub></td>
<td width="25%" align="center"><strong>{d["stars"]}</strong><br><sub>Stars</sub></td>
<td width="25%" align="center"><strong>{d["contributions"]}</strong><br><sub>Contributions</sub></td>
<td width="25%" align="center"><strong>{d["followers"]}</strong><br><sub>Followers</sub></td>
</tr></table>

<p align="center"><img width="100%" src="./assets/recruiter/stats.svg" alt="{esc(d["name"])} GitHub proof metrics"/></p>

## Selected work

<table width="100%"><tr>
<td width="58%" valign="middle"><img width="100%" src="./assets/recruiter/projects.svg" alt="{esc(d["name"])} selected projects"/></td>
<td width="42%" valign="middle">
<h3><a href="{lead["url"]}">{esc(lead["name"])}</a></h3>
<p>{esc(short(lead["description"]))}</p>
<p><sub>{lang(lead)} · ⭐ {lead["stargazerCount"]} · 🍴 {lead["forkCount"]}</sub></p>
<p><a href="{lead["url"]}">Read the repository →</a></p>
</td>
</tr></table>

{rest}

## Technical toolkit

<p align="center"><img width="100%" src="./assets/recruiter/stack.svg" alt="{esc(d["name"])} technology stack"/></p>

<table width="100%"><tr>{toolkit}</tr></table>

## Consistency signal

<p align="center"><img width="100%" src="./assets/recruiter/heatmap.svg" alt="{esc(d["name"])} contribution activity"/></p>

---

<table width="100%"><tr>
<td width="62%" valign="middle"><h2>Let’s talk about the next build</h2><p>{esc(PITCH)}</p></td>
<td width="38%" align="center" valign="middle"><a href="{gh}"><img src="https://img.shields.io/badge/Say_hi_on-GitHub-58a6ff?style=for-the-badge&logo=github&logoColor=white" alt="GitHub"/></a></td>
</tr></table>

<p align="center"><sub>{esc(d["name"])} · recruiter-ready profile · stats refresh daily</sub></p>
"""


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--data":
        with open(sys.argv[2]) as fh:
            raw = json.load(fh)
        user = raw.get("data", {}).get("user", raw)
    else:
        user = fetch()
    d = summarize(user)
    os.makedirs(ASSETS, exist_ok=True)
    for name, fn in [("stats", stats_svg), ("projects", projects_svg),
                     ("stack", stack_svg), ("heatmap", heatmap_svg)]:
        with open(os.path.join(ASSETS, f"{name}.svg"), "w") as fh:
            fh.write(fn(d))
    with open(os.path.join(ROOT, "README.md"), "w") as fh:
        fh.write(readme(d))
    print(f"README + 4 cards written · {d['repo_count']} repos · {d['contributions']} contributions")


if __name__ == "__main__":
    main()
