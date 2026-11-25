#!/usr/bin/env python3
"""Builds the profile README: five animated SVG cards from live GitHub data.

  hero.svg      avatar, handle, name, bio, top languages
  projects.svg  PROJECTS.LIST – pinned repos as a 2x2 grid with language rings
  shooter.svg   contribution grid that a little ship shoots down, cell by cell
  stats.svg     Profile Signal – stars, contributions, repos, followers
  social.svg    GitHub handle pill

Run locally:  python3 scripts/generate_profile.py   (uses GITHUB_TOKEN or `gh auth token`)
In Actions:   .github/workflows/readme.yml runs it daily.
"""
import base64
import datetime as dt
import html
import json
import math
import os
import random
import subprocess
import sys
import urllib.request

LOGIN = "Vaios-Pechlevanidis"
FALLBACK_DESC = "No description provided."
FEATURED = []  # repo names for PROJECTS.LIST; empty = pinned repos

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ASSETS = os.path.join(ROOT, "assets", "profile")
W = 840

# ------------------------------------------------------------------ palette
BG = "#0a0d13"
PANEL = "#0e141f"
EDGE = "#2b4a72"
INNER = "#33598a"
TEXT = "#f0f6fc"
MUTED = "#8b949e"
ACCENT = "#58a6ff"
BLUE_GLOW = "#2f6fd6"
GREEN_GLOW = "#2ea043"
PURPLE_GLOW = "#8957e5"
TEAL_GLOW = "#1b8fa8"
STAT_COLORS = ["#6cb6ff", "#4fd1e8", "#a371f7", "#56d364"]
GRID_EMPTY = "#161b22"
GRID_GREEN = ["#0e4429", "#006d32", "#26a641", "#39d353"]
SANS = "Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "'JetBrains Mono',ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,monospace"
OCTOCAT = ("M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49"
           "-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82"
           ".72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15"
           "-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82"
           " 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48"
           " 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z")

QUERY = """
query($login: String!) {
  user(login: $login) {
    login name bio location avatarUrl url
    followers { totalCount }
    pinnedItems(first: 6, types: REPOSITORY) { nodes { ... on Repository { name } } }
    repositories(ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false, first: 100,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      totalCount
      nodes {
        name description url stargazerCount pushedAt
        primaryLanguage { name color }
        languages(first: 6, orderBy: {field: SIZE, direction: DESC}) {
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


def avatar_data_uri(url):
    """GitHub serves README SVGs through a proxy that blocks external images, so inline it."""
    sep = "&" if "?" in url else "?"
    req = urllib.request.Request(f"{url}{sep}s=200", headers={"User-Agent": "profile-readme"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        mime = resp.headers.get_content_type() or "image/png"
        return f"data:{mime};base64,{base64.b64encode(resp.read()).decode()}"


def summarize(u):
    repos = u["repositories"]["nodes"]
    langs = {}
    for r in repos:
        for e in r["languages"]["edges"]:
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    by_name = {r["name"]: r for r in repos}
    names = FEATURED or [p["name"] for p in u["pinnedItems"]["nodes"] if p]
    featured = [by_name[n] for n in names if n in by_name]
    for r in repos:
        if len(featured) >= 4:
            break
        if r not in featured and r["name"] != LOGIN:
            featured.append(r)
    cal = u["contributionsCollection"]["contributionCalendar"]
    return {
        "login": u["login"].lower(),
        "name": u["name"] or u["login"],
        "bio": " ".join((u["bio"] or "").split()),
        "url": u["url"],
        "avatar": avatar_data_uri(u["avatarUrl"]),
        "followers": u["followers"]["totalCount"],
        "repos": u["repositories"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in repos),
        "contributions": cal["totalContributions"],
        "weeks": cal["weeks"],
        "languages": [n for n, _ in sorted(langs.items(), key=lambda kv: -kv[1])],
        "featured": featured[:4],
    }


# ------------------------------------------------------------------ helpers
def esc(s):
    return html.escape(str(s), quote=True)


def text_w(s, size, mono=False, bold=False):
    return len(s) * size * (0.6 if mono else (0.6 if bold else 0.55))


def clip(s, size, width, mono=False, bold=False):
    if text_w(s, size, mono, bold) <= width:
        return s
    while s and text_w(s + "…", size, mono, bold) > width:
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
    if " ".join(out) != " ".join(words):
        out[-1] = clip(out[-1] + "…", size, width, mono)
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


STYLE = f"""<style>
  .s{{font-family:{SANS}}} .m{{font-family:{MONO}}}
  .fade{{opacity:0;animation:fade .8s ease-out forwards}}
  .grow{{transform-box:fill-box;transform-origin:left center;transform:scaleX(0);animation:grow 1.2s cubic-bezier(.2,.8,.2,1) forwards}}
  .blink{{animation:blink 1.05s steps(1) infinite}}
  @keyframes fade{{from{{opacity:0;transform:translateY(5px)}}to{{opacity:1;transform:none}}}}
  @keyframes grow{{to{{transform:scaleX(1)}}}}
  @keyframes blink{{50%{{opacity:0}}}}
  @media (prefers-reduced-motion:reduce){{
    .fade{{opacity:1!important;animation:none!important}}
    .grow{{transform:none!important;animation:none!important}}
    .blink{{animation:none!important}}
  }}
</style>"""


def frame(h, body, label, inner=True):
    """Dark card with blue rim, soft aurora glows and an inner panel."""
    panel = (f'<rect x="20.5" y="20.5" width="{W - 41}" height="{h - 41}" rx="14" fill="{PANEL}" '
             f'fill-opacity=".35" stroke="{INNER}" stroke-opacity=".75"/>') if inner else ""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" aria-label="{esc(label)}">
<title>{esc(label)}</title>
{STYLE}
<defs>
  <radialGradient id="gb" cx="25%" cy="0%" r="45%"><stop offset="0" stop-color="{BLUE_GLOW}" stop-opacity=".45"/><stop offset="1" stop-color="{BLUE_GLOW}" stop-opacity="0"/></radialGradient>
  <radialGradient id="gg" cx="78%" cy="0%" r="40%"><stop offset="0" stop-color="{GREEN_GLOW}" stop-opacity=".2"/><stop offset="1" stop-color="{GREEN_GLOW}" stop-opacity="0"/></radialGradient>
  <radialGradient id="gp" cx="58%" cy="108%" r="40%"><stop offset="0" stop-color="{PURPLE_GLOW}" stop-opacity=".38"/><stop offset="1" stop-color="{PURPLE_GLOW}" stop-opacity="0"/></radialGradient>
  <radialGradient id="gt" cx="104%" cy="62%" r="32%"><stop offset="0" stop-color="{TEAL_GLOW}" stop-opacity=".32"/><stop offset="1" stop-color="{TEAL_GLOW}" stop-opacity="0"/></radialGradient>
  <clipPath id="clip"><rect width="{W}" height="{h}" rx="18"/></clipPath>
</defs>
<g clip-path="url(#clip)">
  <rect width="{W}" height="{h}" fill="{BG}"/>
  <rect width="{W}" height="{h}" fill="url(#gb)"/><rect width="{W}" height="{h}" fill="url(#gg)"/>
  <rect width="{W}" height="{h}" fill="url(#gp)"/><rect width="{W}" height="{h}" fill="url(#gt)"/>
</g>
<rect x=".75" y=".75" width="{W - 1.5}" height="{h - 1.5}" rx="18" fill="none" stroke="{EDGE}" stroke-width="1.5"/>
{panel}
{body}
</svg>
"""


# ------------------------------------------------------------------ cards
def hero_svg(d):
    h = 240
    cx, cy, r = 128, h / 2, 62
    tx = 222
    name_size = min(48, (W - 50 - tx) / (len(d["name"]) * 0.6))
    handle = "@" + d["login"]
    hw = text_w(handle, 14, bold=True) + len(handle) * 2.6
    pills = []
    for i, lang in enumerate(d["languages"][:4]):
        px = tx + i * 140
        pills.append(
            f'<g class="fade" style="animation-delay:{.55 + i * .1:.2f}s">'
            f'<rect x="{px}" y="172" width="128" height="34" rx="17" fill="#0d1626" stroke="{ACCENT}" stroke-opacity=".55" stroke-width="1.3"/>'
            f'<text x="{px + 20}" y="194" class="s" font-size="14" font-weight="700" fill="{TEXT}">{esc(lang)}</text></g>')
    body = f"""
<defs><clipPath id="av"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath>
  <linearGradient id="arc" x1="0" x2="1"><stop offset="0" stop-color="{ACCENT}" stop-opacity="0"/><stop offset=".5" stop-color="{ACCENT}" stop-opacity=".8"/><stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/></linearGradient></defs>
<g class="fade">
  <circle cx="{cx}" cy="{cy}" r="{r + 5}" fill="none" stroke="{ACCENT}" stroke-opacity=".75" stroke-width="3"/>
  <image href="{d["avatar"]}" xlink:href="{d["avatar"]}" x="{cx - r}" y="{cy - r}" width="{2 * r}" height="{2 * r}" clip-path="url(#av)" preserveAspectRatio="xMidYMid slice"/>
</g>
<g class="fade" style="animation-delay:.15s">
  <path d="M{tx - 4} 82 Q{tx + hw / 2} 58 {tx + hw + 30} 80" fill="none" stroke="url(#arc)" stroke-width="1.5"/>
  <text x="{tx}" y="84" class="s" font-size="14" font-weight="700" letter-spacing="2.6" fill="{MUTED}">{esc(handle)}</text>
</g>
<text x="{tx - 2}" y="134" class="s fade" font-size="{name_size:.1f}" font-weight="800" letter-spacing="-.5" fill="{TEXT}" style="animation-delay:.25s">{esc(d["name"])}</text>
<text x="{tx}" y="160" class="s fade" font-size="16" fill="{MUTED}" style="animation-delay:.4s">{esc(clip(d["bio"], 16, W - 50 - tx))}</text>
{"".join(pills)}
"""
    return frame(h, body, f'{d["name"]} – {d["bio"]}')


def ring(cx, cy, r, sw, segments, delay):
    """Donut of language shares; segments = [(fraction, color)]."""
    circ = 2 * math.pi * r
    out = [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#1d2533" stroke-width="{sw}"/>']
    start = 0.0
    for frac, color in segments:
        length = max(circ * frac - (1.2 if len(segments) > 1 else 0), 0.8)
        out.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="{sw}" '
            f'stroke-dasharray="0 {circ:.1f}" transform="rotate({-90 + start * 360:.1f} {cx} {cy})">'
            f'<animate attributeName="stroke-dasharray" values="0 {circ:.1f};{length:.1f} {circ:.1f}" '
            f'begin="{delay:.2f}s" dur="1s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines=".2 .8 .2 1"/></circle>')
        start += frac
    return "".join(out)


def projects_svg(d):
    gap, ch, top = 16, 150, 96
    cw = (W - 2 * 44 - gap) / 2
    rows = (len(d["featured"]) + 1) // 2
    h = top + rows * ch + (rows - 1) * gap + 44
    body = [
        f'<text x="44" y="62" class="m fade" font-size="13" font-weight="700" letter-spacing="3" fill="{ACCENT}">PROJECTS.LIST</text>',
        f'<text x="200" y="62" class="m fade" font-size="12" fill="{MUTED}">./projects.sh --all</text>',
        f'<text x="{W - 44}" y="62" text-anchor="end" class="m fade" font-size="12" fill="{MUTED}">{len(d["featured"])} projects</text>',
        f'<line x1="42" y1="74" x2="{W - 42}" y2="74" stroke="{ACCENT}" stroke-opacity=".55" stroke-width="1.5"/>',
    ]
    for i, r in enumerate(d["featured"]):
        x = 44 + (i % 2) * (cw + gap)
        y = top + (i // 2) * (ch + gap)
        delay = .2 + i * .15
        lang = r["primaryLanguage"] or {"name": "Code", "color": MUTED}
        total = r["languages"]["totalSize"]
        segs = [(e["size"] / total, e["node"]["color"] or MUTED) for e in r["languages"]["edges"]] if total else [(1, lang["color"])]
        pct = round(segs[0][0] * 100)
        title = clip(r["name"], 16, cw - 120, mono=True)
        cursor_x = x + 22 + text_w(title, 16, mono=True) + 8
        desc = wrap(r["description"] or FALLBACK_DESC, 11.5, cw - 120, 2, mono=True)
        pill_w = text_w(lang["name"], 10.5, mono=True) + 20
        rx, ry = x + cw - 52, y + 94
        body.append(
            f'<g class="fade" style="animation-delay:{delay:.2f}s">'
            f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="12" fill="{PANEL}" fill-opacity=".9" stroke="{INNER}"/>'
            f'<text x="{x + 20}" y="{y + 21}" class="m" font-size="11" fill="{MUTED}"><tspan fill="{ACCENT}">•</tspan>  {esc(clip(r["name"], 11, cw - 70, mono=True))}</text>'
            f'<circle cx="{x + cw - 20}" cy="{y + 17}" r="4" fill="{MUTED}" fill-opacity=".7"/>'
            f'<line x1="{x}" y1="{y + 32}" x2="{x + cw}" y2="{y + 32}" stroke="{INNER}" stroke-opacity=".8"/>'
            f'<text x="{x + 22}" y="{y + 60}" class="m" font-size="16" font-weight="700" fill="{TEXT}">{esc(title)}</text>'
            f'<rect x="{cursor_x:.1f}" y="{y + 61}" width="10" height="2" fill="{ACCENT}" class="blink"/>'
            + "".join(f'<text x="{x + 22}" y="{y + 82 + j * 17}" class="m" font-size="11.5" fill="{MUTED}">{esc(t)}</text>'
                      for j, t in enumerate(desc))
            + f'<rect x="{x + 22}" y="{y + 107}" width="{pill_w:.0f}" height="18" rx="9" fill="{ACCENT}" fill-opacity=".1" stroke="{ACCENT}" stroke-opacity=".55"/>'
            f'<text x="{x + 22 + pill_w / 2:.1f}" y="{y + 120}" text-anchor="middle" class="m" font-size="10.5" fill="{ACCENT}">{esc(lang["name"])}</text>'
            f'<text x="{x + 22}" y="{y + ch - 9}" class="m" font-size="11" fill="{MUTED}"><tspan fill="#e3b341">★</tspan> {r["stargazerCount"]}<tspan dx="16">updated {ago(r["pushedAt"])}</tspan></text>'
            + ring(rx, ry, 22, 7, segs, delay + .3)
            + f'<text x="{rx}" y="{ry + 4}" text-anchor="middle" class="m" font-size="11" font-weight="700" fill="{TEXT}">{pct}%</text>'
            '</g>')
    return frame(h, "\n".join(body), f'{d["name"]} – pinned projects')


def shooter_svg(d):
    weeks = d["weeks"]
    pitch, cell = 14.6, 11
    gx = (W - (len(weeks) - 1) * pitch - cell) / 2
    gy = 44
    dots_y = gy + 7 * pitch + 16
    ship_y = dots_y + 40
    h = ship_y + 40

    counts = sorted(dd["contributionCount"] for wk in weeks for dd in wk["contributionDays"] if dd["contributionCount"])
    q = [counts[int(len(counts) * f)] for f in (.25, .5, .75)] if counts else [1, 2, 3]

    def color(c):
        return GRID_EMPTY if c == 0 else GRID_GREEN[sum(c > t for t in q)]

    def cx_of(col):
        return gx + col * pitch + cell / 2

    cells, targets = {}, []
    for col, wk in enumerate(weeks):
        for dd in wk["contributionDays"]:
            row = (dt.date.fromisoformat(dd["date"]).weekday() + 1) % 7
            cells[(col, row)] = dd
            if dd["contributionCount"]:
                targets.append((col, row))

    # ---- schedule: ship sweeps left→right, shooting each column bottom-up
    by_col = {}
    for col, row in targets:
        by_col.setdefault(col, []).append(row)
    t, frames, shots, col_done = 0.8, [], {}, {}
    prev = min(by_col) if by_col else 0
    frames.append((0.0, cx_of(prev)))
    for col in sorted(by_col):
        t += max(.14, abs(col - prev) * .045) if col != prev else 0
        frames.append((t, cx_of(col)))
        for row in sorted(by_col[col], reverse=True):
            travel = .1 + (ship_y - 26 - (gy + row * pitch)) / 900
            shots[(col, row)] = (t, t + travel)
            t += .3
        col_done[col] = t
        frames.append((t, cx_of(col)))
        prev = col
    end = t + .9
    T = end + 1.4
    frames += [(end, cx_of(prev)), (T, frames[0][1])]

    def kt(*times):
        vals, last = [], 0.0
        for tm in times:
            v = max(min(tm / T, 1.0), last)
            vals.append(v)
            last = v
        return ";".join(f"{v:.4f}" for v in vals)

    anim = f'dur="{T:.2f}s" repeatCount="indefinite"'
    reset = T - .35
    body = []

    # twinkling stars
    rnd = random.Random(7)
    for _ in range(18):
        sx, sy = rnd.uniform(30, W - 30), rnd.uniform(26, h - 20)
        if gx - 8 < sx < W - gx + 8 and gy - 8 < sy < gy + 7 * pitch + 8:
            continue
        body.append(f'<circle cx="{sx:.0f}" cy="{sy:.0f}" r="{rnd.choice([1, 1.3, 1.6])}" fill="{MUTED}" opacity=".5">'
                    f'<animate attributeName="opacity" values=".15;.7;.15" dur="{rnd.uniform(2.5, 5):.1f}s" begin="{rnd.uniform(0, 3):.1f}s" repeatCount="indefinite"/></circle>')

    for (col, row), dd in cells.items():
        x, y = gx + col * pitch, gy + row * pitch
        c = color(dd["contributionCount"])
        title = f'<title>{dd["date"]}: {dd["contributionCount"]} contributions</title>'
        if (col, row) not in shots:
            body.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" rx="2.5" fill="{c}">{title}</rect>')
            continue
        fire, hit = shots[(col, row)]
        ccx, ccy = x + cell / 2, y + cell / 2
        body.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" rx="2.5" fill="{c}">{title}'
            f'<animate attributeName="fill" calcMode="discrete" values="{c};#b6f5c2;{GRID_EMPTY};{c}" keyTimes="{kt(0, hit, hit + .12, reset)}" {anim}/></rect>'
            f'<circle cx="{ccx:.1f}" cy="{ccy:.1f}" r="5" fill="none" stroke="#3fb950" stroke-width="2" opacity="0">'
            f'<animate attributeName="r" values="5;5;13;13" keyTimes="{kt(0, hit, hit + .55, T)}" {anim}/>'
            f'<animate attributeName="opacity" values="0;0;1;0;0" keyTimes="{kt(0, hit, hit + .03, hit + .6, T)}" {anim}/></circle>'
            f'<rect x="{ccx - 1:.1f}" y="{ship_y - 26}" width="2" height="8" rx="1" fill="#79c0ff" opacity="0">'
            f'<animate attributeName="y" values="{ship_y - 26};{ship_y - 26};{ccy - 4:.1f};{ccy - 4:.1f}" keyTimes="{kt(0, fire, hit, T)}" {anim}/>'
            f'<animate attributeName="opacity" calcMode="discrete" values="0;1;0" keyTimes="{kt(0, fire, hit)}" {anim}/></rect>')

    # score dots: one per cleared column
    for col, done in col_done.items():
        body.append(f'<circle cx="{cx_of(col):.1f}" cy="{dots_y}" r="3.2" fill="#3fb950" opacity=".18">'
                    f'<animate attributeName="opacity" calcMode="discrete" values=".18;1;.18" keyTimes="{kt(0, done, reset)}" {anim}/></circle>')

    # the ship
    xs = ";".join(f"{x:.1f},{ship_y}" for _, x in frames)
    body.append(f"""
<defs><linearGradient id="hull" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#a5d6ff"/><stop offset=".55" stop-color="#4493f8"/><stop offset="1" stop-color="#1f4fb5"/></linearGradient></defs>
<g transform="translate({frames[0][1]:.1f},{ship_y})">
  <animateTransform attributeName="transform" type="translate" values="{xs}" keyTimes="{kt(*[tm for tm, _ in frames])}" {anim}/>
  <path d="M-4 9 L0 22 L4 9 Z" fill="#f0883e"><animate attributeName="d" values="M-4 9 L0 22 L4 9 Z;M-3.5 9 L0 16 L3.5 9 Z;M-4 9 L0 22 L4 9 Z" dur=".25s" repeatCount="indefinite"/></path>
  <path d="M0 -26 L7 -6 L8 4 L17 13 L5 9 L0 11 L-5 9 L-17 13 L-8 4 L-7 -6 Z" fill="url(#hull)" stroke="#cae8ff" stroke-opacity=".5" stroke-width=".8"/>
  <circle cx="0" cy="-6" r="3.2" fill="#e6f3ff"/>
</g>""")
    return frame(h, "\n".join(body), f'{d["contributions"]} contributions in the last year', inner=False)


def stats_svg(d):
    h = 222
    tiles = [("Stars", d["stars"]), ("Contributions", d["contributions"]),
             ("Repos", d["repos"]), ("Followers", d["followers"])]
    peak = max(v for _, v in tiles) or 1
    gap, x0, y0, th = 14, 40, 104, 90
    tw = (W - 2 * x0 - 3 * gap) / 4
    body = [
        f'<text x="44" y="66" class="s fade" font-size="26" font-weight="800" fill="{TEXT}">Profile Signal</text>',
        f'<text x="46" y="88" class="s fade" font-size="13" font-weight="600" letter-spacing="1" fill="{MUTED}" style="animation-delay:.1s">Live GitHub stats, refreshed daily</text>',
    ]
    for i, ((label, val), col) in enumerate(zip(tiles, STAT_COLORS)):
        x = x0 + i * (tw + gap)
        delay = .2 + i * .12
        bar = max((tw - 44) * val / peak, 10)
        body.append(
            f'<g class="fade" style="animation-delay:{delay:.2f}s">'
            f'<rect x="{x:.1f}" y="{y0}" width="{tw:.1f}" height="{th}" rx="14" fill="#0b1019" fill-opacity=".85" stroke="{INNER}"/>'
            f'<text x="{x + 22:.1f}" y="{y0 + 28}" class="s" font-size="13" font-weight="600" letter-spacing=".6" fill="{MUTED}">{label}</text>'
            f'<text x="{x + 22:.1f}" y="{y0 + 62}" class="s" font-size="32" font-weight="800" fill="{col}">{val}</text>'
            f'<rect x="{x + 22:.1f}" y="{y0 + 72}" width="{tw - 44:.1f}" height="6" rx="3" fill="#1d2330"/>'
            f'<rect x="{x + 22:.1f}" y="{y0 + 72}" width="{bar:.1f}" height="6" rx="3" fill="{col}" class="grow" style="animation-delay:{delay + .2:.2f}s"/>'
            '</g>')
    return frame(h, "\n".join(body), f'{d["name"]} – GitHub stats')


def social_svg(d):
    h = 120
    handle = "@" + d["login"]
    pw = max(text_w(handle, 15, bold=True) + 80, 200)
    px, py = (W - pw) / 2, h / 2 - 26
    body = f"""
<defs><linearGradient id="rim" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#e6edf3" stop-opacity=".7"/><stop offset=".5" stop-color="{ACCENT}" stop-opacity=".5"/><stop offset="1" stop-color="#e6edf3" stop-opacity=".6"/></linearGradient></defs>
<g class="fade" style="animation-delay:.15s">
  <rect x="{px:.1f}" y="{py:.1f}" width="{pw:.1f}" height="52" rx="26" fill="#0d1117" stroke="url(#rim)" stroke-width="1.6"/>
  <circle cx="{px + 30:.1f}" cy="{h / 2}" r="15" fill="#21262d"/>
  <path d="{OCTOCAT}" fill="{TEXT}" transform="translate({px + 21:.1f},{h / 2 - 9}) scale(1.125)"/>
  <text x="{px + 56:.1f}" y="{h / 2 - 4}" class="s" font-size="11" font-weight="600" letter-spacing=".6" fill="{MUTED}">GitHub</text>
  <text x="{px + 56:.1f}" y="{h / 2 + 14}" class="s" font-size="15" font-weight="700" fill="{TEXT}">{esc(handle)}</text>
</g>"""
    return frame(h, body, f"GitHub {handle}")


# ------------------------------------------------------------------ readme
def readme(d):
    gh = d["url"]
    img = './assets/profile/{}.svg'
    return f"""<!-- Generated by scripts/generate_profile.py – edit the script, not this file. -->
<div align="center">

<a href="{gh}"><img src="{img.format("hero")}" width="100%" alt="{esc(d["name"])} – {esc(d["bio"])}"/></a>

<a href="{gh}?tab=repositories"><img src="{img.format("projects")}" width="100%" alt="Pinned projects: {esc(", ".join(r["name"] for r in d["featured"]))}"/></a>

<img src="{img.format("shooter")}" width="100%" alt="{d["contributions"]} contributions in the last year, shot down by a tiny spaceship"/>

<img src="{img.format("stats")}" width="100%" alt="{d["stars"]} stars · {d["contributions"]} contributions · {d["repos"]} repos · {d["followers"]} followers"/>

<a href="{gh}"><img src="{img.format("social")}" width="100%" alt="GitHub @{d["login"]}"/></a>

</div>
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
    for name, fn in [("hero", hero_svg), ("projects", projects_svg), ("shooter", shooter_svg),
                     ("stats", stats_svg), ("social", social_svg)]:
        with open(os.path.join(ASSETS, f"{name}.svg"), "w") as fh:
            fh.write(fn(d))
    with open(os.path.join(ROOT, "README.md"), "w") as fh:
        fh.write(readme(d))
    print(f"README + 5 cards · {d['repos']} repos · {d['contributions']} contributions")


if __name__ == "__main__":
    main()
