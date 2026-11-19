#!/usr/bin/env python3
"""Generates the animated pixel-art SVGs used in the profile README.

Run:  python3 scripts/generate_svgs.py
Output goes to ./assets/
"""
import os
import random

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")

# ---------------------------------------------------------------- palette
BG = "#0b0f1a"
BG2 = "#131a2e"
CYAN = "#00f0ff"
MAGENTA = "#ff2bd6"
PURPLE = "#8b5cf6"
GREEN = "#7cffcb"
YELLOW = "#ffd23f"
WHITE = "#e6edf3"
DIM = "#2a3350"
LINKEDIN = "#0a66c2"

# ---------------------------------------------------------------- 5x7 pixel font
FONT = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": [".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "J": ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."],
    "X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
    "&": [".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"],
    "-": [".....", ".....", ".....", "#####", ".....", ".....", "....."],
    ">": ["#....", ".#...", "..#..", "...#.", "..#..", ".#...", "#...."],
    "<": ["....#", "...#.", "..#..", ".#...", "..#..", "...#.", "....#"],
    "_": [".....", ".....", ".....", ".....", ".....", ".....", "#####"],
    ".": [".....", ".....", ".....", ".....", ".....", ".....", "..#.."],
    "!": ["..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."],
    ":": [".....", "..#..", ".....", ".....", ".....", "..#..", "....."],
    "/": ["....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."],
    "?": [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
    "[": [".###.", ".#...", ".#...", ".#...", ".#...", ".#...", ".###."],
    "]": [".###.", "...#.", "...#.", "...#.", "...#.", "...#.", ".###."],
    "%": ["##..#", "##.#.", "...#.", "..#..", ".#...", ".#.##", "#..##"],
    "#": [".#.#.", "#####", ".#.#.", ".#.#.", ".#.#.", "#####", ".#.#."],
    "+": [".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."],
    ",": [".....", ".....", ".....", ".....", ".....", "..#..", ".#..."],
    " ": ["....."] * 7,
}


def text_width(s, scale):
    return len(s) * 6 * scale - scale


def glyph_path(ch, x, y, s):
    d = []
    for r, row in enumerate(FONT.get(ch.upper(), FONT[" "])):
        for c, px in enumerate(row):
            if px == "#":
                d.append(f"M{x + c * s} {y + r * s}h{s}v{s}h-{s}z")
    return "".join(d)


def text_path(s, x, y, scale):
    """Whole string as a single path 'd'."""
    return "".join(glyph_path(ch, x + i * 6 * scale, y, scale) for i, ch in enumerate(s))


def text_chars(s, x, y, scale):
    """List of (char, d) per character (for per-letter animation)."""
    return [(ch, glyph_path(ch, x + i * 6 * scale, y, scale)) for i, ch in enumerate(s)]


def sprite(grid, x, y, s, colors):
    """grid: list of strings, colors: dict char->color. Returns <path> elements grouped per color."""
    paths = {}
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch in colors:
                paths.setdefault(ch, []).append(f"M{x + c * s} {y + r * s}h{s}v{s}h-{s}z")
    return "".join(f'<path fill="{colors[k]}" d="{"".join(v)}"/>' for k, v in paths.items())


def svg(w, h, body, style=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'shape-rendering="crispEdges">\n<style>{style}</style>\n{body}\n</svg>\n'
    )


def frame(w, h, color=DIM, s=4):
    """Pixel border with notched corners."""
    return (
        f'<path fill="{color}" d="M{s} 0h{w - 2 * s}v{s}h-{w - 2 * s}z'
        f'M{s} {h - s}h{w - 2 * s}v{s}h-{w - 2 * s}z'
        f'M0 {s}h{s}v{h - 2 * s}h-{s}z'
        f'M{w - s} {s}h{s}v{h - 2 * s}h-{s}z"/>'
    )


def save(name, content):
    with open(os.path.join(OUT, name), "w") as f:
        f.write(content)
    print("wrote", name, len(content), "bytes")


# ---------------------------------------------------------------- sprites
_GEAR_BODY = [
    "............",
    "............",
    "....####....",
    "...######...",
    "..###..###..",
    "..##....##..",
    "..##....##..",
    "..###..###..",
    "...######...",
    "....####....",
    "............",
    "............",
]


def _gear_frame(teeth):
    g = [list(r) for r in _GEAR_BODY]
    for r, c in teeth:
        g[r][c] = "#"
    return ["".join(r) for r in g]


# frame A: teeth up/down/left/right, frame B: diagonal teeth -> looks like rotation
GEAR_A = _gear_frame(
    [(r, c) for r in (0, 1, 10, 11) for c in (5, 6)] + [(r, c) for r in (5, 6) for c in (0, 1, 10, 11)]
)
GEAR_B = _gear_frame(
    [(r, c) for r in (1, 2) for c in (1, 2, 9, 10)] + [(r, c) for r in (9, 10) for c in (1, 2, 9, 10)]
)

BRAIN = [
    "...####.###...",
    "..#....#...#..",
    ".#..##.#.#..#.",
    "#..#...#..#..#",
    "#....#.#.....#",
    "#.##...#.##..#",
    ".#...#.#...##.",
    "..###..#.##...",
    "......###.....",
    "......###.....",
]


def gear(x, y, s, color, cls):
    return (
        f'<g class="{cls}a">{sprite(GEAR_A, x, y, s, {"#": color})}</g>'
        f'<g class="{cls}b">{sprite(GEAR_B, x, y, s, {"#": color})}</g>'
    )


GEAR_CSS = """
.ga{animation:ga 0.6s steps(1) infinite}
.gb{animation:gb 0.6s steps(1) infinite}
@keyframes ga{0%{opacity:1}50%{opacity:0}}
@keyframes gb{0%{opacity:0}50%{opacity:1}}
"""


# ---------------------------------------------------------------- header
def header():
    W, H = 860, 220
    rnd = random.Random(7)
    body = [f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    body.append(
        '<defs>'
        '<pattern id="grid" width="12" height="12" patternUnits="userSpaceOnUse">'
        f'<path d="M12 0H0V12" fill="none" stroke="{BG2}" stroke-width="1"/></pattern>'
        '<linearGradient id="tg" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{CYAN}"/><stop offset="0.5" stop-color="{PURPLE}"/>'
        f'<stop offset="1" stop-color="{MAGENTA}"/>'
        '<animate attributeName="x1" values="0;-1;0" dur="6s" repeatCount="indefinite"/>'
        '<animate attributeName="x2" values="1;0;1" dur="6s" repeatCount="indefinite"/>'
        '</linearGradient></defs>'
    )
    body.append(f'<rect width="{W}" height="{H}" fill="url(#grid)"/>')

    # stars
    stars = []
    for i in range(55):
        x = rnd.randrange(8, W - 8) // 4 * 4
        y = rnd.randrange(8, H - 8) // 4 * 4
        sz = rnd.choice([3, 4, 4, 6])
        col = rnd.choice([CYAN, MAGENTA, WHITE, PURPLE, WHITE])
        dur = rnd.choice([1.2, 1.6, 2.0, 2.4, 3.0])
        delay = round(rnd.random() * 3, 2)
        stars.append(
            f'<rect class="st" x="{x}" y="{y}" width="{sz}" height="{sz}" fill="{col}" '
            f'style="animation-duration:{dur}s;animation-delay:-{delay}s"/>'
        )
    body.append("".join(stars))

    # title
    title = "VAIOS PECHLEVANIDIS"
    sc = 6
    tw = text_width(title, sc)
    tx = (W - tw) // 2 // sc * sc
    ty = 54
    body.append(f'<path fill="#3b1d6e" d="{text_path(title, tx + sc, ty + sc, sc)}"/>')
    letters = []
    for i, (ch, d) in enumerate(text_chars(title, tx, ty, sc)):
        if not d:
            continue
        letters.append(f'<path class="lt" style="animation-delay:{i * 0.08:.2f}s" fill="url(#tg)" d="{d}"/>')
    body.append("".join(letters))

    # tags row
    tags = ["AI AGENTS", "WORKFLOWS", "LLMS", "PYTHON"]
    ts = 2
    gap = 18
    widths = [text_width(t, ts) + 20 for t in tags]
    total = sum(widths) + gap * (len(tags) - 1)
    x = (W - total) // 2
    y = 140
    cols = [CYAN, MAGENTA, YELLOW, GREEN, PURPLE]
    tag_svg = []
    for i, (t, w) in enumerate(zip(tags, widths)):
        c = cols[i % len(cols)]
        tag_svg.append(
            f'<g class="tag" style="animation-delay:{i * 0.25}s">'
            f'<path fill="{c}" d="M{x + 2} {y}h{w - 4}v2h-{w - 4}zM{x + 2} {y + 28}h{w - 4}v2h-{w - 4}z'
            f'M{x} {y + 2}h2v26h-2zM{x + w - 2} {y + 2}h2v26h-2z"/>'
            f'<path fill="{c}" d="{text_path(t, x + 10, y + 8, ts)}"/></g>'
        )
        x += w + gap
    body.append("".join(tag_svg))

    # side sprites: brain (left), gear (right)
    body.append(
        f'<g class="bob">{sprite(BRAIN, 40, 132, 4, {"#": MAGENTA})}</g>'
    )
    body.append(gear(W - 40 - 48, 128, 4, CYAN, "g"))

    # scanline
    body.append(f'<rect class="scan" x="0" y="0" width="{W}" height="4" fill="{CYAN}" opacity="0.08"/>')
    body.append(frame(W, H, PURPLE, 4))
    # corner accents
    body.append(
        f'<path fill="{CYAN}" d="M12 12h24v4h-24zM12 12h4v24h-4zM{W - 36} {H - 16}h24v4h-24zM{W - 16} {H - 36}h4v24h-4z"/>'
    )

    style = (
        ".st{animation-name:tw;animation-iteration-count:infinite;animation-timing-function:steps(2)}"
        "@keyframes tw{0%,100%{opacity:1}50%{opacity:.15}}"
        ".lt{animation:hop 2.4s steps(1) infinite}"
        "@keyframes hop{0%,90%,100%{transform:translateY(0)}93%{transform:translateY(-6px)}96%{transform:translateY(-3px)}}"
        ".tag{animation:tg 2.5s steps(1) infinite}"
        "@keyframes tg{0%,80%{opacity:1}85%{opacity:.35}90%{opacity:1}}"
        ".bob{animation:bob 1.6s steps(1) infinite}"
        "@keyframes bob{50%{transform:translateY(-4px)}}"
        ".scan{animation:scan 5s steps(70) infinite}"
        f"@keyframes scan{{from{{transform:translateY(0)}}to{{transform:translateY({H}px)}}}}"
        + GEAR_CSS
    )
    save("header.svg", svg(W, H, "\n".join(body), style))


# ---------------------------------------------------------------- AI: neural network
NEURON = [".####.", "######", "######", "######", "######", ".####."]


def _pixel_line(x0, y0, x1, y1, s):
    """Stair-stepped pixel line between two points (block size s)."""
    d = []
    n = max(abs(x1 - x0), abs(y1 - y0)) // s
    seen = set()
    for i in range(n + 1):
        x = round((x0 + (x1 - x0) * i / max(n, 1)) / s) * s
        y = round((y0 + (y1 - y0) * i / max(n, 1)) / s) * s
        if (x, y) not in seen:
            seen.add((x, y))
            d.append(f"M{x} {y}h{s}v{s}h-{s}z")
    return "".join(d)


def neural():
    W, H = 420, 330
    rnd = random.Random(11)
    T = 3.0          # one forward pass
    EPOCHS = 8       # status frames
    body = [f'<rect width="{W}" height="{H}" fill="{BG}"/>', frame(W, H, PURPLE, 4)]

    layers = [3, 4, 4, 2]
    xs = [36, 140, 244, 352]
    top, bottom = 60, 268
    pos = []
    for n, x in zip(layers, xs):
        gap = (bottom - top) / (n + 1)
        pos.append([(x, int(top + gap * (i + 1)) // 4 * 4 - 12) for i in range(n)])

    # connections
    conn = []
    for L in range(len(layers) - 1):
        for (ax, ay) in pos[L]:
            for (bx, by) in pos[L + 1]:
                conn.append(_pixel_line(ax + 11, ay + 11, bx + 11, by + 11, 2))
    body.append(f'<path fill="#232c48" d="{"".join(conn)}"/>')

    # signals: one per target neuron (+ extras), stepped motion along the line
    window = 0.24
    sig = []
    for L in range(len(layers) - 1):
        t0 = 0.04 + L * window
        t1 = t0 + window * 0.9
        pairs = [(rnd.randrange(len(pos[L])), j) for j in range(len(pos[L + 1]))]
        pairs += [(rnd.randrange(len(pos[L])), rnd.randrange(len(pos[L + 1]))) for _ in range(2)]
        col = [CYAN, MAGENTA, YELLOW][L]
        for a, b in pairs:
            (ax, ay), (bx, by) = pos[L][a], pos[L + 1][b]
            N = 8
            xv = [round((ax + 8 + (bx - ax) * k / N) / 4) * 4 for k in range(N + 1)]
            yv = [round((ay + 8 + (by - ay) * k / N) / 4) * 4 for k in range(N + 1)]
            kt = [0] + [round(t0 + (t1 - t0) * k / N, 3) for k in range(N + 1)] + [1]
            xv = [xv[0]] + xv + [xv[-1]]
            yv = [yv[0]] + yv + [yv[-1]]
            ktxt = ";".join(str(k) for k in kt)
            sig.append(
                f'<rect width="8" height="8" fill="{col}" x="{xv[0]}" y="{yv[0]}" opacity="0">'
                f'<animate attributeName="x" values="{";".join(map(str, xv))}" keyTimes="{ktxt}" dur="{T}s" calcMode="discrete" repeatCount="indefinite"/>'
                f'<animate attributeName="y" values="{";".join(map(str, yv))}" keyTimes="{ktxt}" dur="{T}s" calcMode="discrete" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" values="0;1;0" keyTimes="0;{t0};{t1}" dur="{T}s" calcMode="discrete" repeatCount="indefinite"/>'
                f'</rect>'
            )
    body.append("".join(sig))

    # neurons: dim base + flash when activated
    lay_cols = [CYAN, PURPLE, MAGENTA, GREEN]
    for L, col in enumerate(pos):
        arrive = 0.0 if L == 0 else round(0.04 + (L - 1) * window + window * 0.9, 3)
        end = round(min(arrive + 0.14, 0.99), 3)
        for (x, y) in col:
            body.append(sprite(NEURON, x, y, 4, {"#": "#1d2540"}))
            body.append(f'<path fill="{lay_cols[L]}" d="M{x + 8} {y + 8}h8v8h-8z" opacity=".5"/>')
            flash = sprite(NEURON, x, y, 4, {"#": lay_cols[L]}) + f'<path fill="{WHITE}" d="M{x + 8} {y + 4}h8v4h-8z"/>'
            vals = "1;0" if arrive == 0 else "0;1;0"
            kts = f"0;{end}" if arrive == 0 else f"0;{arrive};{end}"
            body.append(
                f'<g opacity="0">{flash}'
                f'<animate attributeName="opacity" values="{vals}" keyTimes="{kts}" dur="{T}s" '
                f'calcMode="discrete" repeatCount="indefinite"/></g>'
            )

    # status: epoch counter + falling loss, one frame per forward pass
    losses = ["0.92", "0.71", "0.55", "0.38", "0.24", "0.15", "0.08", "0.03"]
    for e in range(EPOCHS):
        txt = f"EPOCH {e + 1:03d}  LOSS {losses[e]}"
        vals = ";".join("1" if j == e else "0" for j in range(EPOCHS)) + (";1" if e == 0 else ";0")
        kts = ";".join(f"{j / EPOCHS:.3f}" for j in range(EPOCHS)) + ";1"
        c = GREEN if e == EPOCHS - 1 else WHITE
        body.append(
            f'<path fill="{c}" d="{text_path(txt, 24, 24, 2)}" opacity="{1 if e == 0 else 0}">'
            f'<animate attributeName="opacity" values="{vals}" keyTimes="{kts}" dur="{T * EPOCHS}s" '
            f'calcMode="discrete" repeatCount="indefinite"/></path>'
        )
    # loss bar shrinking
    bw = [int(80 * float(l)) // 4 * 4 + 4 for l in losses]
    body.append(
        f'<rect x="{W - 24 - 84}" y="44" width="84" height="8" fill="{BG2}"/>'
        f'<rect x="{W - 24 - 84}" y="44" width="{bw[0]}" height="8" fill="{MAGENTA}">'
        f'<animate attributeName="width" values="{";".join(map(str, bw))};{bw[0]}" '
        f'keyTimes="{";".join(f"{j / EPOCHS:.3f}" for j in range(EPOCHS))};1" dur="{T * EPOCHS}s" '
        f'calcMode="discrete" repeatCount="indefinite"/></rect>'
    )

    lbl = "NEURAL NETWORK"
    body.append(f'<path fill="{CYAN}" d="{text_path(lbl, (W - text_width(lbl, 2)) // 2, H - 30, 2)}"/>')
    save("ai-network.svg", svg(W, H, "\n".join(body), ""))


# ---------------------------------------------------------------- automation: data factory
RAW = [
    ".##.#.",
    "####.#",
    "#.###.",
    ".#####",
    "##.##.",
    ".#.##.",
]
BOX = [
    "######",
    "#WWWW#",
    "#W####",
    "######",
    "######",
    "######",
]


def factory():
    W, H = 420, 330
    body = [f'<rect width="{W}" height="{H}" fill="{BG}"/>', frame(W, H, PURPLE, 4)]
    P = 1.2  # seconds between items

    # status + item counter
    body.append(f'<rect class="dot" x="24" y="26" width="10" height="10" fill="{GREEN}"/>')
    body.append(f'<path fill="{WHITE}" d="{text_path("PIPELINE ACTIVE", 44, 24, 2)}"/>')
    N = 10
    for k in range(N):
        txt = f"{(k + 1) * 128:05d}"
        vals = ";".join("1" if j == k else "0" for j in range(N)) + (";1" if k == 0 else ";0")
        kts = ";".join(f"{j / N:.3f}" for j in range(N)) + ";1"
        body.append(
            f'<path fill="{YELLOW}" d="{text_path(txt, W - 24 - text_width(txt, 2), 24, 2)}" opacity="{1 if k == 0 else 0}">'
            f'<animate attributeName="opacity" values="{vals}" keyTimes="{kts}" dur="{P * N}s" '
            f'calcMode="discrete" repeatCount="indefinite"/></path>'
        )

    # conveyor belt
    by = 232
    x0, x1 = 16, W - 16
    body.append(f'<rect x="{x0}" y="{by}" width="{x1 - x0}" height="20" fill="#1d2540"/>')
    treads = "".join(f"M{x} {by + 4}h8v4h-8zM{x + 8} {by + 12}h8v4h-8z" for x in range(x0 - 16, x1 + 16, 16))
    body.append(
        '<defs><clipPath id="belt">'
        f'<rect x="{x0}" y="{by}" width="{x1 - x0}" height="20"/></clipPath></defs>'
        f'<g clip-path="url(#belt)"><path class="tread" fill="{DIM}" d="{treads}"/></g>'
    )
    body.append(f'<path fill="{WHITE}" d="M{x0} {by - 4}h{x1 - x0}v4h-{x1 - x0}zM{x0} {by + 20}h{x1 - x0}v4h-{x1 - x0}z"/>')
    # legs
    body.append(f'<path fill="{DIM}" d="M28 {by + 24}h8v28h-8zM{W - 36} {by + 24}h8v28h-8z"/>')

    mx0, mx1 = 140, 280  # machine span
    # raw items (left) -> machine
    raw_cols = ["#6b7280", "#8b93a7"]
    for i in range(2):
        body.append(
            f'<g class="raw" style="animation-delay:-{i * P:.2f}s">'
            f'{sprite(RAW, 16, by - 4 - 24, 4, {"#": raw_cols[i]})}</g>'
        )
    # packaged items (right) machine -> out
    out_cols = [CYAN, MAGENTA]
    for i in range(2):
        body.append(
            f'<g class="out" style="animation-delay:-{i * P:.2f}s">'
            f'{sprite(BOX, mx1 - 24, by - 4 - 24, 4, {"#": out_cols[i], "W": WHITE})}</g>'
        )

    # machine
    body.append(f'<rect x="{mx0}" y="104" width="{mx1 - mx0}" height="{by + 24 - 104}" fill="{BG2}"/>')
    body.append(
        f'<path fill="{PURPLE}" d="M{mx0} 104h{mx1 - mx0}v4h-{mx1 - mx0}z'
        f'M{mx0} 108h4v{by - 112}h-4zM{mx1 - 4} 108h4v{by - 112}h-4z'
        f'M{mx0 - 8} {by - 36}h12v4h-12zM{mx1 - 4} {by - 36}h12v4h-12z"/>'
    )
    # entry/exit flaps
    flaps = "".join(f"M{x} {by - 32}h4v28h-4z" for x in (mx0, mx0 + 8, mx1 - 4, mx1 - 12))
    body.append(f'<path fill="{DIM}" d="{flaps}"/>')
    # screen with "AI"
    body.append(f'<rect x="{mx0 + 24}" y="120" width="{mx1 - mx0 - 48}" height="36" fill="{BG}"/>')
    body.append(f'<path class="scr" fill="{GREEN}" d="{text_path("AI", (mx0 + mx1) // 2 - 11, 132, 2)}"/>')
    body.append(
        f'<path class="scr2" fill="{MAGENTA}" d="M{mx0 + 32} 148h8v4h-8zM{mx0 + 44} 144h8v8h-8zM{mx0 + 56} 140h8v12h-8z'
        f'M{mx1 - 64} 136h8v16h-8zM{mx1 - 52} 142h8v10h-8zM{mx1 - 40} 146h8v6h-8z"/>'
    )
    # indicator lights
    for i, c in enumerate([CYAN, YELLOW, MAGENTA, GREEN]):
        body.append(
            f'<rect class="led" style="animation-delay:{i * 0.15:.2f}s" x="{mx0 + 28 + i * 24}" y="168" '
            f'width="8" height="8" fill="{c}"/>'
        )
    # gears on top
    body.append(gear(mx0 + 14, 56, 4, CYAN, "g"))
    body.append(gear(mx1 - 62, 64, 4, MAGENTA, "h"))
    # sparks / steam
    for i in range(4):
        body.append(
            f'<rect class="spk" style="animation-delay:-{i * 0.4:.1f}s" x="{(mx0 + mx1) // 2 - 4 + (i % 2) * 8}" '
            f'y="96" width="6" height="6" fill="{YELLOW if i % 2 else WHITE}"/>'
        )

    lbl = "AUTOMATION"
    body.append(f'<path fill="{CYAN}" d="{text_path(lbl, (W - text_width(lbl, 2)) // 2, H - 30, 2)}"/>')

    raw_dist = mx0 - 16 + 4
    out_dist = x1 - (mx1 - 24)
    style = (
        f".raw{{animation:raw {2 * P}s steps({raw_dist // 8}) infinite}}"
        f"@keyframes raw{{from{{transform:translateX(0)}}to{{transform:translateX({raw_dist}px)}}}}"
        f".out{{animation:out {2 * P}s steps({out_dist // 8}) infinite}}"
        f"@keyframes out{{from{{transform:translateX(0)}}to{{transform:translateX({out_dist}px)}}}}"
        ".tread{animation:tr .4s steps(4) infinite}"
        "@keyframes tr{from{transform:translateX(0)}to{transform:translateX(16px)}}"
        ".dot{animation:bl 1s steps(1) infinite}@keyframes bl{50%{opacity:0}}"
        f".scr{{animation:bl {P}s steps(1) infinite}}"
        f".scr2{{animation:eq {P / 2}s steps(1) infinite}}@keyframes eq{{50%{{transform:translateY(4px)}}}}"
        ".led{animation:led .6s steps(1) infinite}@keyframes led{50%{opacity:.2}}"
        ".spk{animation:spk 1.6s steps(8) infinite}"
        "@keyframes spk{0%{transform:translate(0,0);opacity:1}100%{transform:translate(0,-48px);opacity:0}}"
        + GEAR_CSS
        + ".ha{animation:gb .45s steps(1) infinite}.hb{animation:ga .45s steps(1) infinite}"
    )
    save("automation.svg", svg(W, H, "\n".join(body), style))


# ---------------------------------------------------------------- divider
def divider():
    W, H = 860, 24
    n = 54
    step = W // n
    body = []
    for i in range(n):
        x = i * step + (step - 8) // 2
        c = [CYAN, PURPLE, MAGENTA][i % 3]
        body.append(
            f'<rect class="d" style="animation-delay:{i * 0.05:.2f}s" x="{x}" y="8" width="8" height="8" fill="{c}"/>'
        )
    style = (
        ".d{animation:d 2.7s steps(1) infinite;opacity:.25}"
        "@keyframes d{0%{opacity:1;transform:translateY(-4px)}6%{opacity:.6;transform:translateY(0)}12%,100%{opacity:.25}}"
    )
    save("divider.svg", svg(W, H, "".join(body), style))


# ---------------------------------------------------------------- linkedin button
def linkedin():
    W, H = 372, 72
    body = [f'<rect x="4" y="4" width="{W - 8}" height="{H - 8}" fill="{BG}"/>']
    body.append(f'<g class="glow">{frame(W, H, LINKEDIN, 4)}</g>')
    # pixel "in" logo, 10x10 grid scale 4
    logo = [
        "##########",
        "#........#",
        "#.#......#",
        "#........#",
        "#.#.#.##.#",
        "#.#.##..##",
        "#.#.#...##",
        "#.#.#...##",
        "#........#",
        "##########",
    ]
    lx, ly = 18, 16
    body.append(f'<rect x="{lx}" y="{ly}" width="40" height="40" fill="{LINKEDIN}"/>')
    body.append(sprite(logo, lx, ly, 4, {".": LINKEDIN, "#": LINKEDIN}))
    # white letters
    inn = [
        "..........",
        "..........",
        "..#.......",
        "..........",
        "..#.#.##..",
        "..#.##..#.",
        "..#.#...#.",
        "..#.#...#.",
        "..........",
        "..........",
    ]
    body.append(sprite(inn, lx, ly, 4, {"#": "#ffffff"}))
    t = "CONNECT ON LINKEDIN"
    body.append(f'<path fill="{WHITE}" d="{text_path(t, 72, 22, 2)}"/>')
    t2 = "LETS BUILD THE FUTURE"
    body.append(f'<path fill="{CYAN}" d="{text_path(t2, 72, 40, 2)}"/>')
    body.append(f'<path class="arr" fill="{MAGENTA}" d="{text_path(">", W - 32, 29, 2)}"/>')
    style = (
        ".glow{animation:gl 1.4s steps(1) infinite}"
        f"@keyframes gl{{50%{{opacity:.45}}}}"
        ".arr{animation:ar .8s steps(1) infinite}"
        "@keyframes ar{50%{transform:translateX(4px)}}"
    )
    save("linkedin.svg", svg(W, H, "\n".join(body), style))


# ---------------------------------------------------------------- footer
def footer():
    W, H = 860, 120
    body = [f'<rect width="{W}" height="{H}" fill="{BG}"/>', frame(W, H, PURPLE, 4)]
    t = "THANKS FOR VISITING!"
    sc = 3
    tx = (W - text_width(t, sc)) // 2
    for i, (ch, d) in enumerate(text_chars(t, tx, 30, sc)):
        if d:
            c = [CYAN, PURPLE, MAGENTA][i % 3]
            body.append(f'<path class="w" style="animation-delay:{i * 0.07:.2f}s" fill="{c}" d="{d}"/>')
    s2 = "SYSTEM STATUS: ONLINE   UPTIME: 24/7"
    sx = (W - text_width(s2, 2) - 20) // 2
    body.append(f'<rect class="dot" x="{sx}" y="80" width="10" height="10" fill="{GREEN}"/>')
    body.append(f'<path fill="{GREEN}" d="{text_path(s2, sx + 20, 79, 2)}"/>')
    style = (
        ".w{animation:w 1.8s steps(1) infinite}"
        "@keyframes w{0%,100%{transform:translateY(0)}10%{transform:translateY(-6px)}20%{transform:translateY(-3px)}30%{transform:translateY(0)}}"
        ".dot{animation:bl 1s steps(1) infinite}@keyframes bl{50%{opacity:0}}"
    )
    save("footer.svg", svg(W, H, "\n".join(body), style))


# ---------------------------------------------------------------- small icons (120x120)
IW = 120


def icon_base():
    return [f'<rect width="{IW}" height="{IW}" fill="{BG}"/>', frame(IW, IW, PURPLE, 4)]


def icon_brain():
    body = icon_base()
    s = 6
    x0, y0 = (IW - 14 * s) // 2, (IW - 10 * s) // 2
    body.append(sprite(BRAIN, x0, y0, s, {"#": MAGENTA}))
    # synapses firing along the brain outline
    cells = [(r, c) for r, row in enumerate(BRAIN) for c, ch in enumerate(row) if ch == "#"]
    rnd = random.Random(5)
    picks = rnd.sample(cells, 10)
    for i, (r, c) in enumerate(picks):
        body.append(
            f'<rect class="syn" style="animation-delay:{i * 0.15:.2f}s" x="{x0 + c * s}" y="{y0 + r * s}" '
            f'width="{s}" height="{s}" fill="{CYAN}"/>'
        )
    # sparks around
    for i, (x, y) in enumerate([(14, 16), (98, 20), (12, 96), (100, 94)]):
        body.append(
            f'<path class="spk" style="animation-delay:{i * 0.3:.1f}s" fill="{YELLOW}" '
            f'd="M{x + 4} {y}h4v12h-4zM{x} {y + 4}h12v4h-12z"/>'
        )
    style = (
        ".syn{animation:syn 1.5s steps(1) infinite;opacity:0}"
        "@keyframes syn{0%,12%{opacity:1}13%,100%{opacity:0}}"
        ".spk{animation:spk 1.2s steps(1) infinite}@keyframes spk{50%{opacity:0}}"
    )
    save("icon-brain.svg", svg(IW, IW, "\n".join(body), style))


def icon_gears():
    body = icon_base()
    body.append(gear(14, 30, 5, CYAN, "g"))
    body.append(gear(64, 14, 4, MAGENTA, "h"))
    body.append(gear(70, 66, 3, YELLOW, "g"))
    style = GEAR_CSS + ".ha{animation:gb .45s steps(1) infinite}.hb{animation:ga .45s steps(1) infinite}"
    save("icon-gears.svg", svg(IW, IW, "\n".join(body), style))


def icon_terminal():
    body = icon_base()
    # window
    body.append(f'<rect x="12" y="16" width="96" height="88" fill="{BG2}"/>')
    body.append(f'<rect x="12" y="16" width="96" height="14" fill="{DIM}"/>')
    for i, c in enumerate([MAGENTA, YELLOW, GREEN]):
        body.append(f'<rect x="{18 + i * 10}" y="20" width="6" height="6" fill="{c}"/>')
    lines = ["> BUILD", "> TEST", "> SHIP"]
    T = 6.0
    total = sum(len(l) for l in lines)
    k = 0
    for li, line in enumerate(lines):
        y = 40 + li * 20
        for ci, (ch, d) in enumerate(text_chars(line, 18, y, 2)):
            t = round(0.05 + 0.7 * k / total, 3)
            k += 1
            if not d:
                continue
            col = GREEN if ch == ">" else WHITE
            body.append(
                f'<path fill="{col}" d="{d}" opacity="0"><animate attributeName="opacity" values="0;1;0" '
                f'keyTimes="0;{t};0.95" dur="{T}s" calcMode="discrete" repeatCount="indefinite"/></path>'
            )
    body.append(f'<rect class="cur" x="18" y="98" width="10" height="2" fill="{GREEN}"/>')
    style = ".cur{animation:bl .8s steps(1) infinite}@keyframes bl{50%{opacity:0}}"
    save("icon-terminal.svg", svg(IW, IW, "\n".join(body), style))


def icon_chat():
    body = icon_base()
    bx, by, bw, bh = 16, 22, 88, 56
    body.append(
        f'<path fill="{CYAN}" d="M{bx + 4} {by}h{bw - 8}v4h-{bw - 8}zM{bx + 4} {by + bh - 4}h{bw - 8}v4h-{bw - 8}z'
        f'M{bx} {by + 4}h4v{bh - 8}h-4zM{bx + bw - 4} {by + 4}h4v{bh - 8}h-4z'
        f'M{bx + 16} {by + bh}h12v4h-12zM{bx + 12} {by + bh + 4}h8v4h-8zM{bx + 8} {by + bh + 8}h4v4h-4z"/>'
    )
    body.append(f'<rect x="{bx + 4}" y="{by + 4}" width="{bw - 8}" height="{bh - 8}" fill="{BG2}"/>')
    for i, c in enumerate([CYAN, PURPLE, MAGENTA]):
        body.append(
            f'<rect class="dt" style="animation-delay:{i * 0.2:.1f}s" x="{bx + 20 + i * 18}" y="{by + 24}" '
            f'width="12" height="12" fill="{c}"/>'
        )
    style = (
        ".dt{animation:dt 1.2s steps(1) infinite}"
        "@keyframes dt{0%,100%{transform:translateY(0)}15%{transform:translateY(-8px)}30%{transform:translateY(-4px)}45%{transform:translateY(0)}}"
    )
    save("icon-chat.svg", svg(IW, IW, "\n".join(body), style))


def icon_server():
    body = icon_base()
    x, y, w = 28, 14, 64
    for u in range(3):
        uy = y + u * 30
        body.append(f'<rect x="{x}" y="{uy}" width="{w}" height="26" fill="{DIM}"/>')
        body.append(f'<rect x="{x + 4}" y="{uy + 4}" width="{w - 8}" height="18" fill="{BG2}"/>')
        body.append(f'<path fill="{DIM}" d="M{x + 30} {uy + 8}h22v2h-22zM{x + 30} {uy + 13}h22v2h-22z"/>')
        for i, c in enumerate([GREEN, CYAN if u % 2 else MAGENTA]):
            dur = [0.5, 0.8, 1.1, 0.7, 1.3, 0.9][u * 2 + i]
            body.append(
                f'<rect class="led" style="animation-duration:{dur}s" x="{x + 8 + i * 10}" y="{uy + 9}" '
                f'width="6" height="6" fill="{c}"/>'
            )
    body.append(f'<path fill="{DIM}" d="M{x + 8} {y + 90}h8v8h-8zM{x + w - 16} {y + 90}h8v8h-8z"/>')
    style = ".led{animation-name:bl;animation-iteration-count:infinite;animation-timing-function:steps(1)}@keyframes bl{50%{opacity:.15}}"
    save("icon-server.svg", svg(IW, IW, "\n".join(body), style))


ROCKET = [
    "....##....",
    "...####...",
    "..######..",
    "..##WW##..",
    "..##WW##..",
    "..######..",
    "..######..",
    ".F######F.",
    "FF.####.FF",
    "F..####..F",
    "...#..#...",
]
FLAME_A = ["...YYYY...", "....OO....", ".........."]
FLAME_B = ["...OYYO...", "...YYYY...", "....OO...."]


def icon_rocket():
    body = icon_base()
    rnd = random.Random(9)
    for i in range(9):
        x = rnd.randrange(10, 106) // 2 * 2
        body.append(
            f'<rect class="sf" style="animation-delay:-{rnd.random() * 1.2:.2f}s" x="{x}" y="0" width="3" '
            f'height="{rnd.choice([6, 9, 12])}" fill="{rnd.choice([WHITE, PURPLE, CYAN])}"/>'
        )
    s = 6
    x0, y0 = (IW - 10 * s) // 2, 12
    cols = {"#": WHITE, "W": CYAN, "F": MAGENTA, "Y": YELLOW, "O": "#ff7a00"}
    r = sprite(ROCKET, x0, y0, s, cols)
    r += f'<g class="fa">{sprite(FLAME_A, x0, y0 + 11 * s, s, cols)}</g>'
    r += f'<g class="fb">{sprite(FLAME_B, x0, y0 + 11 * s, s, cols)}</g>'
    body.append(f'<g class="rk">{r}</g>')
    body.append(frame(IW, IW, PURPLE, 4))
    style = (
        ".sf{animation:sf 1.2s steps(10) infinite}"
        "@keyframes sf{from{transform:translateY(-12px)}to{transform:translateY(124px)}}"
        ".fa{animation:fa .3s steps(1) infinite}.fb{animation:fb .3s steps(1) infinite}"
        "@keyframes fa{50%{opacity:0}}@keyframes fb{0%{opacity:0}50%{opacity:1}}"
        ".rk{animation:rk .8s steps(1) infinite}@keyframes rk{50%{transform:translate(2px,-2px)}}"
    )
    save("icon-rocket.svg", svg(IW, IW, "\n".join(body), style))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    header()
    neural()
    factory()
    divider()
    linkedin()
    footer()
    icon_brain()
    icon_gears()
    icon_terminal()
    icon_chat()
    icon_server()
    icon_rocket()
