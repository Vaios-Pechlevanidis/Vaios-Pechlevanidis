#!/usr/bin/env python3
"""Fetches GitHub stats via GraphQL and renders pixel-art stat cards.

Runs in GitHub Actions (.github/workflows/stats.yml) with GITHUB_TOKEN.
Local test without network:  python3 scripts/generate_stats.py --demo
"""
import datetime
import json
import os
import random
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_svgs import (  # noqa: E402
    BG, BG2, CYAN, DIM, GREEN, MAGENTA, PURPLE, WHITE, YELLOW,
    frame, save, sprite, svg, text_path, text_width,
)

QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    pullRequests { totalCount }
    issues { totalCount }
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100,
                 orderBy: {field: STARGAZERS, direction: DESC}) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks { contributionDays { contributionCount } }
      }
    }
  }
}
"""


def fetch(login, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(f"GraphQL error: {data['errors']}")
    u = data["data"]["user"]
    repos = u["repositories"]["nodes"]
    langs = {}
    for repo in repos:
        for e in repo["languages"]["edges"]:
            n = e["node"]
            langs.setdefault(n["name"], [0, n["color"] or PURPLE])
            langs[n["name"]][0] += e["size"]
    cc = u["contributionsCollection"]
    days = [d["contributionCount"] for w in cc["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    return {
        "stars": sum(r["stargazerCount"] for r in repos),
        "commits": cc["totalCommitContributions"] + cc["restrictedContributionsCount"],
        "prs": u["pullRequests"]["totalCount"],
        "issues": u["issues"]["totalCount"],
        "repos": u["repositories"]["totalCount"],
        "followers": u["followers"]["totalCount"],
        "contrib": cc["contributionCalendar"]["totalContributions"],
        "langs": sorted(([k, v[0], v[1]] for k, v in langs.items()), key=lambda x: -x[1]),
        "days": days,
    }


def demo():
    rnd = random.Random(1)
    days = [max(0, int(rnd.gauss(2, 3))) for _ in range(364)]
    return {
        "stars": 42, "commits": 512, "prs": 37, "issues": 12, "repos": 18, "followers": 64,
        "contrib": sum(days), "days": days,
        "langs": [["Python", 500, "#3572A5"], ["TypeScript", 300, "#3178c6"],
                  ["JavaScript", 150, "#f1e05a"], ["Shell", 60, "#89e051"], ["HTML", 40, "#e34c26"]],
    }


def fmt(n):
    return f"{n / 1000:.1f}K" if n >= 10000 else str(n)


# -------------------------------------------------------------- stats card
ICONS = {
    "star": ["..#..", ".###.", "#####", ".###.", ".#.#."],
    "commit": [".....", ".###.", "##.##", ".###.", "....."],
    "pr": ["#..#.", "#.###", "#..##", "#...#", "#..##"],
    "issue": [".###.", "#.#.#", "#.#.#", "#...#", ".#.#."],
    "repo": ["####.", "#..#.", "#..#.", "####.", "#.#.."],
    "user": [".###.", ".###.", "..#..", "#####", "#...#"],
}


def count_up(value, x, y, color, dur=1.6):
    """Number that counts up once (frames shown discretely, last frame frozen)."""
    steps = [0.0, 0.1, 0.25, 0.45, 0.65, 0.8, 0.92, 1.0]
    out = []
    n = len(steps)
    for i, f in enumerate(steps):
        txt = fmt(int(round(value * f)))
        vals = ";".join("1" if j == i else "0" for j in range(n))
        kts = ";".join(f"{j / n:.3f}" for j in range(n))
        out.append(
            f'<path fill="{color}" d="{text_path(txt, x - text_width(txt, 2), y, 2)}" opacity="{1 if i == n - 1 else 0}">'
            f'<animate attributeName="opacity" values="{vals}" keyTimes="{kts}" dur="{dur}s" '
            f'calcMode="discrete" fill="freeze"/></path>'
        )
    return "".join(out)


def stats_card(d):
    W, H = 420, 240
    body = [f'<rect width="{W}" height="{H}" fill="{BG}"/>', frame(W, H, PURPLE, 4)]
    body.append(f'<path fill="{CYAN}" d="{text_path("GITHUB STATS", 24, 22, 3)}"/>')
    body.append(f'<rect class="bl" x="{24 + text_width("GITHUB STATS", 3) + 8}" y="22" width="12" height="21" fill="{CYAN}"/>')
    rows = [
        ("star", "STARS", d["stars"], YELLOW),
        ("commit", f"COMMITS {datetime.date.today().year}", d["commits"], GREEN),
        ("pr", "PULL REQUESTS", d["prs"], MAGENTA),
        ("issue", "ISSUES", d["issues"], CYAN),
        ("repo", "REPOS", d["repos"], PURPLE),
        ("user", "FOLLOWERS", d["followers"], WHITE),
    ]
    for i, (ic, label, val, col) in enumerate(rows):
        y = 62 + i * 28
        body.append(f'<g class="ic" style="animation-delay:{i * 0.2:.1f}s">{sprite(ICONS[ic], 24, y, 3, {"#": col})}</g>')
        body.append(f'<path fill="{WHITE}" d="{text_path(label, 50, y + 1, 2)}"/>')
        # dotted leader
        lx0 = 50 + text_width(label, 2) + 8
        body.append(f'<path fill="{DIM}" d="{"".join(f"M{x} {y + 11}h2v2h-2z" for x in range(lx0, W - 100, 6))}"/>')
        body.append(count_up(val, W - 24, y + 1, col))
    style = (
        ".bl{animation:bl 1s steps(1) infinite}@keyframes bl{50%{opacity:0}}"
        ".ic{animation:ic 2.4s steps(1) infinite}@keyframes ic{0%,10%{transform:translateY(-3px)}11%{transform:translateY(0)}}"
    )
    save("stats.svg", svg(W, H, "\n".join(body), style))


def langs_card(d):
    W, H = 420, 240
    body = [f'<rect width="{W}" height="{H}" fill="{BG}"/>', frame(W, H, PURPLE, 4)]
    body.append(f'<path fill="{MAGENTA}" d="{text_path("TOP LANGUAGES", 24, 22, 3)}"/>')
    langs = d["langs"][:6]
    total = sum(l[1] for l in d["langs"]) or 1
    if not langs:
        body.append(f'<path fill="{DIM}" d="{text_path("NO DATA YET", 24, 110, 2)}"/>')
    barw = 160
    for i, (name, size, col) in enumerate(langs):
        y = 64 + i * 28
        pct = size / total * 100
        body.append(f'<path fill="{WHITE}" d="{text_path(name[:10], 24, y + 1, 2)}"/>')
        bx = 160
        segs = max(1, round(pct / 100 * barw / 8))
        body.append(f'<path fill="{BG2}" d="{"".join(f"M{bx + k * 8} {y}h6v14h-6z" for k in range(barw // 8))}"/>')
        for k in range(segs):
            t = round(0.1 + 0.8 * k / max(segs, 1), 3)
            body.append(
                f'<rect x="{bx + k * 8}" y="{y}" width="6" height="14" fill="{col}" opacity="0">'
                f'<set attributeName="opacity" to="1" begin="{t + i * 0.15:.2f}s" fill="freeze"/></rect>'
            )
        txt = f"{pct:.1f}%"
        body.append(f'<path fill="{col}" d="{text_path(txt, W - 24 - text_width(txt, 2), y + 1, 2)}"/>')
    save("languages.svg", svg(W, H, "\n".join(body), ""))


def contrib_card(d):
    W, H = 860, 200
    body = [f'<rect width="{W}" height="{H}" fill="{BG}"/>', frame(W, H, PURPLE, 4)]
    title = f"{fmt(d['contrib'])} CONTRIBUTIONS IN THE LAST YEAR"
    body.append(f'<path fill="{GREEN}" d="{text_path(title, 24, 22, 2)}"/>')
    days = d["days"][-371:]
    weeks = (len(days) + 6) // 7
    cell, step = 11, 15
    gx = (W - weeks * step) // 2
    gy = 56
    mx = max(days) if days else 0
    levels = [BG2, "#1f3a5f", "#2f6fa8", CYAN, MAGENTA]
    for i, c in enumerate(days):
        w, dow = divmod(i, 7)
        lvl = 0 if c == 0 or mx == 0 else min(4, 1 + int(3.999 * c / mx))
        x, y = gx + w * step, gy + dow * step
        if lvl == 0:
            body.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="{levels[0]}"/>')
        else:
            body.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="{levels[lvl]}" opacity="0">'
                f'<set attributeName="opacity" to="1" begin="{w * 0.03:.2f}s" fill="freeze"/></rect>'
            )
    # scanning highlight column
    body.append(
        f'<rect class="scan" x="{gx - 2}" y="{gy - 2}" width="{cell + 4}" height="{7 * step}" fill="{WHITE}" opacity=".12"/>'
    )
    # legend
    lx = W - 24 - 5 * 15 - text_width("LESS", 2) - text_width("MORE", 2) - 16
    body.append(f'<path fill="{DIM}" d="{text_path("LESS", lx, H - 34, 2)}"/>')
    for k, c in enumerate(levels):
        body.append(f'<rect x="{lx + text_width("LESS", 2) + 8 + k * 15}" y="{H - 34}" width="11" height="11" fill="{c}"/>')
    body.append(f'<path fill="{DIM}" d="{text_path("MORE", lx + text_width("LESS", 2) + 16 + 5 * 15, H - 34, 2)}"/>')
    upd = "UPDATED " + datetime.date.today().strftime("%d.%m.%Y")
    body.append(f'<path fill="{DIM}" d="{text_path(upd, 24, H - 34, 2)}"/>')
    style = (
        f".scan{{animation:scan 6s steps({weeks}) infinite}}"
        f"@keyframes scan{{from{{transform:translateX(0)}}to{{transform:translateX({weeks * step}px)}}}}"
    )
    save("contributions.svg", svg(W, H, "\n".join(body), style))


def placeholder():
    """Shown until the GitHub Action has run once."""
    for name, w, h in (("stats.svg", 420, 240), ("languages.svg", 420, 240), ("contributions.svg", 860, 200)):
        t1, t2 = "LOADING STATS...", "RUN THE STATS WORKFLOW"
        body = [f'<rect width="{w}" height="{h}" fill="{BG}"/>', frame(w, h, PURPLE, 4),
                f'<path class="bl" fill="{CYAN}" d="{text_path(t1, (w - text_width(t1, 3)) // 2, h // 2 - 26, 3)}"/>',
                f'<path fill="{DIM}" d="{text_path(t2, (w - text_width(t2, 2)) // 2, h // 2 + 12, 2)}"/>']
        save(name, svg(w, h, "\n".join(body), ".bl{animation:bl 1s steps(1) infinite}@keyframes bl{50%{opacity:0}}"))


def main():
    if "--demo" in sys.argv:
        d = demo()
    elif not os.environ.get("GITHUB_TOKEN"):
        placeholder()
        return
    else:
        token = os.environ["GITHUB_TOKEN"]
        login = os.environ.get("GH_USER") or os.environ["GITHUB_REPOSITORY_OWNER"]
        d = fetch(login, token)
    stats_card(d)
    langs_card(d)
    contrib_card(d)


if __name__ == "__main__":
    main()
