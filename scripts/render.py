#!/usr/bin/env python3
"""Render the profile README graphics into assets/, one dark and one light SVG each.

All text is converted to glyph outlines, so the cards look the same on every OS and
browser and need no web fonts. Fonts: Inter 4.1 and JetBrains Mono 2.304 (SIL OFL 1.1),
downloaded into .fonts/ on the first run.

    python3 -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt
    .venv/bin/python scripts/render.py
"""

import io
import math
import random
import subprocess
import urllib.request
import zipfile
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = ROOT / ".fonts"
ASSETS = ROOT / "assets"

FONT_RELEASES = [
    ("https://github.com/rsms/inter/releases/download/v4.1/Inter-4.1.zip", {
        "Inter-Regular.ttf": "extras/ttf/Inter-Regular.ttf",
        "Inter-Medium.ttf": "extras/ttf/Inter-Medium.ttf",
        "Inter-SemiBold.ttf": "extras/ttf/Inter-SemiBold.ttf",
        "InterDisplay-Bold.ttf": "extras/ttf/InterDisplay-Bold.ttf",
        "InterDisplay-SemiBold.ttf": "extras/ttf/InterDisplay-SemiBold.ttf",
    }),
    ("https://github.com/JetBrains/JetBrainsMono/releases/download/v2.304/JetBrainsMono-2.304.zip", {
        "JetBrainsMono-Regular.ttf": "fonts/ttf/JetBrainsMono-Regular.ttf",
        "JetBrainsMono-Medium.ttf": "fonts/ttf/JetBrainsMono-Medium.ttf",
    }),
]


def ensure_fonts():
    FONT_DIR.mkdir(exist_ok=True)
    for url, members in FONT_RELEASES:
        if all((FONT_DIR / name).exists() for name in members):
            continue
        print(f"downloading {url}")
        try:
            with urllib.request.urlopen(url) as resp:
                data = resp.read()
        except urllib.error.URLError:  # e.g. a python.org build without its CA certificates
            data = subprocess.run(["curl", "-fsSL", url], check=True, capture_output=True).stdout
        archive = zipfile.ZipFile(io.BytesIO(data))
        for name, member in members.items():
            (FONT_DIR / name).write_bytes(archive.read(member))


# ---------------------------------------------------------------------------- type


class Face:
    def __init__(self, key, filename, features=None):
        path = FONT_DIR / filename
        self.key = key
        self.hb = hb.Font(hb.Face(path.read_bytes()))
        self.tt = TTFont(path)
        self.upm = self.tt["head"].unitsPerEm
        self.glyphs = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()
        self.features = features or {}

    def shape(self, text, features=None):
        if not text:
            return []
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb, buf, {**self.features, **(features or {})})
        out = []
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            if info.codepoint == 0:
                raise ValueError(f"{self.key}: no glyph for a character in {text!r}")
            out.append((info.codepoint, pos.x_advance, pos.x_offset, pos.y_offset))
        return out

    def width(self, text, size, tracking=0.0, features=None):
        g = self.shape(text, features)
        units = sum(a for _, a, _, _ in g) + tracking * self.upm * (len(g) - 1)
        return units * size / self.upm


MONO_OFF = {"calt": False, "liga": False}
F = {}


def load_faces():
    F["reg"] = Face("r", "Inter-Regular.ttf")
    F["med"] = Face("m", "Inter-Medium.ttf")
    F["semi"] = Face("s", "Inter-SemiBold.ttf")
    F["disp"] = Face("d", "InterDisplay-Bold.ttf")
    F["dsemi"] = Face("e", "InterDisplay-SemiBold.ttf")
    F["mono"] = Face("j", "JetBrainsMono-Regular.ttf", MONO_OFF)
    F["monom"] = Face("k", "JetBrainsMono-Medium.ttf", MONO_OFF)


def wrap(face, text, size, max_width):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and face.width(trial, size) > max_width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------------------- svg


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def n(v):
    """Compact number for SVG attributes."""
    r = round(v, 2)
    return str(int(r)) if r == int(r) else f"{r:g}"


class Svg:
    def __init__(self, w, h, title, desc):
        self.w, self.h, self.title, self.desc = w, h, title, desc
        self.glyph_defs = {}
        self.defs = []
        self.style = []
        self.body = []

    def add(self, s):
        self.body.append(s)

    def glyph_id(self, face, gid):
        key = f"{face.key}{gid}"
        if key not in self.glyph_defs:
            pen = SVGPathPen(face.glyphs, ntos=lambda v: str(round(v)))
            face.glyphs[face.order[gid]].draw(pen)
            self.glyph_defs[key] = pen.getCommands()
        return key if self.glyph_defs[key] else None

    def text(self, face, s, x, y, size, fill, tracking=0.0, anchor="start", features=None,
             attrs=""):
        """Set `s` with its baseline at y. Returns the advance width in px."""
        g = face.shape(s, features)
        track = tracking * face.upm
        units = sum(a for _, a, _, _ in g) + track * (len(g) - 1)
        scale = size / face.upm
        if anchor == "end":
            x -= units * scale
        elif anchor == "middle":
            x -= units * scale / 2
        uses, pen = [], 0.0
        for gid, adv, xo, yo in g:
            ref = self.glyph_id(face, gid)
            if ref:
                y_attr = f' y="{yo}"' if yo else ""
                uses.append(f'<use href="#{ref}" x="{round(pen + xo)}"{y_attr}/>')
            pen += adv + track
        self.add(f'<g fill="{fill}" transform="translate({n(x)} {n(y)}) scale({scale:.6f} '
                 f'{-scale:.6f})"{attrs}>{"".join(uses)}</g>')
        return units * scale

    def render(self):
        glyphs = "".join(f'<path id="{k}" d="{d}"/>' for k, d in self.glyph_defs.items() if d)
        style = f"<style>{''.join(self.style)}</style>" if self.style else ""
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
            f'width="{self.w}" height="{self.h}" role="img" aria-labelledby="t d">'
            f'<title id="t">{esc(self.title)}</title><desc id="d">{esc(self.desc)}</desc>'
            f'{style}<defs>{glyphs}{"".join(self.defs)}</defs>{"".join(self.body)}</svg>\n'
        )


# ---------------------------------------------------------------------------- themes

# Series colors were checked with a CVD/contrast palette validator against each surface:
# dark on #0d1117, light on #ffffff (all-pairs, protan/deutan dE >= 8.7, normal dE >= 16.5).
THEMES = {
    "dark": dict(
        card="#0d1117", card2="#111721", border="#30363d", grid="#21262d", plane="#e6edf3",
        text="#e6edf3", text2="#9da7b3", text3="#7d8590", accent="#e3b341",
        accent_soft="#e3b34126", chip="#161b22", node="#7d8590", edge="#3b434d",
        series=["#b98a1e", "#4a86d6", "#22a07f"],
    ),
    "light": dict(
        card="#ffffff", card2="#f6f8fa", border="#d1d9e0", grid="#eaeef2", plane="#1f2328",
        text="#1f2328", text2="#59636e", text3="#6e7781", accent="#9a6700",
        accent_soft="#bf870024", chip="#f6f8fa", node="#8c959f", edge="#c8d1da",
        series=["#b07d0e", "#2a78d6", "#1a8f6e"],
    ),
}


def card(svg, t, w, h, gradient=True, behind=False):
    if gradient:
        svg.defs.append(
            f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0" stop-color="{t["card2"]}"/><stop offset="1" stop-color="{t["card"]}"/>'
            f"</linearGradient>")
        fill = "url(#bg)"
    else:
        fill = t["card"]
    rect = (f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="12" fill="{fill}" '
            f'stroke="{t["border"]}"/>')
    if behind:
        svg.body.insert(0, rect)
    else:
        svg.add(rect)


def eyebrow(svg, t, s, x, y, size=12.5):
    return svg.text(F["monom"], s.upper(), x, y, size, t["accent"], tracking=0.08)


def chip(svg, t, s, x, y, size=12, anchor="start", color=None, border=None):
    """A rounded tag; (x, y) is the top-left corner (top-right with anchor='end')."""
    w = F["mono"].width(s, size) + 18
    h = size + 12
    if anchor == "end":
        x -= w
    svg.add(f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" rx="{n(h / 2)}" '
            f'fill="{t["chip"]}" stroke="{border or t["border"]}"/>')
    svg.text(F["mono"], s, x + 9, y + h / 2 + size * 0.36, size, color or t["text2"])
    return w


def chips(svg, t, items, x, y, size=12, gap=8, anchor="start"):
    if anchor == "end":
        for s in reversed(items):
            x -= chip(svg, t, s, x, y, size, anchor="end") + gap
        return
    for s in items:
        x += chip(svg, t, s, x, y, size) + gap


def pill(svg, t, s, x, y, size=11.5):
    """An award marker in the accent color; (x, y) is the left end of the vertical center."""
    w = F["monom"].width(s, size, tracking=0.06) + 32
    h = size + 11
    svg.add(f'<rect x="{n(x)}" y="{n(y - h / 2)}" width="{n(w)}" height="{n(h)}" rx="{n(h / 2)}" '
            f'fill="{t["accent_soft"]}" stroke="{t["accent"]}" stroke-opacity="0.55"/>')
    # a small four-point star
    cx, cy, r = x + 13, y, 4.6
    svg.add(f'<path d="M{n(cx)} {n(cy - r)} Q{n(cx + 0.9)} {n(cy - 0.9)} {n(cx + r)} {n(cy)} '
            f'Q{n(cx + 0.9)} {n(cy + 0.9)} {n(cx)} {n(cy + r)} Q{n(cx - 0.9)} {n(cy + 0.9)} '
            f'{n(cx - r)} {n(cy)} Q{n(cx - 0.9)} {n(cy - 0.9)} {n(cx)} {n(cy - r)}Z" '
            f'fill="{t["accent"]}"/>')
    svg.text(F["monom"], s, x + 23, y + size * 0.36, size, t["accent"], tracking=0.06)
    return w


def stat(svg, t, value, label_lines, x, y):
    svg.text(F["disp"], value, x, y, 30, t["text"], tracking=-0.01, features={"tnum": True})
    for i, line in enumerate(label_lines):
        svg.text(F["reg"], line, x, y + 22 + i * 17, 13, t["text2"])


def repo_link(svg, t, s, x, y, anchor="start"):
    return svg.text(F["mono"], s + " ↗", x, y, 12.5, t["text3"], anchor=anchor)


# ---------------------------------------------------------------------------- banner


def dist(p, q, aspect=0.55):
    return math.hypot(p[0] - q[0], (p[1] - q[1]) * aspect)


def farthest_subset(points, k, seed_index):
    chosen = [seed_index]
    while len(chosen) < k:
        best = max((i for i in range(len(points)) if i not in chosen),
                   key=lambda i: min(dist(points[i], points[j]) for j in chosen))
        chosen.append(best)
    return chosen


def knn_edges(points, members, k):
    edges = set()
    nbrs = {i: set() for i in members}
    for i in members:
        near = sorted((j for j in members if j != i), key=lambda j: dist(points[i], points[j]))[:k]
        for j in near:
            edges.add((min(i, j), max(i, j)))
            nbrs[i].add(j)
            nbrs[j].add(i)
    return edges, nbrs


def hnsw_scene():
    """A small three-layer HNSW graph plus a real greedy search for one query.

    Seeds are tried until the search makes hops on every layer and lands on the true
    nearest neighbor, so the picture shows the algorithm working, not a drawing of it.
    """
    for seed in range(1, 500):
        rng = random.Random(seed)
        pts = []
        for _ in range(5000):
            p = (rng.uniform(0.04, 0.96), rng.uniform(0.1, 0.9))
            if all(dist(p, q) > 0.1 for q in pts):
                pts.append(p)
                if len(pts) == 22:
                    break
        if len(pts) < 22:
            continue
        query = (rng.uniform(0.55, 0.9), rng.uniform(0.45, 0.85))
        if min(dist(query, p) for p in pts) < 0.05:
            continue
        l0 = list(range(len(pts)))
        l1 = farthest_subset(pts, 8, rng.randrange(len(pts)))
        l2 = farthest_subset(pts, 3, l1[rng.randrange(len(l1))])
        l2 = [i for i in l2 if i in l1] or l1[:3]
        if len(l2) < 3:
            continue
        layers = [l0, l1, l2]
        graph = [knn_edges(pts, m, k) for m, k in ((l0, 3), (l1, 2), (l2, 2))]
        cur = max(l2, key=lambda i: dist(pts[i], query))
        path, hops = [cur], []
        for level in (2, 1, 0):
            count = 0
            while True:
                nb = graph[level][1][cur]
                best = min(nb, key=lambda j: dist(pts[j], query))
                if dist(pts[best], query) >= dist(pts[cur], query):
                    break
                cur = best
                path.append((level, cur))
                count += 1
            hops.append(count)
            if level:
                path.append((level - 1, cur))
        true_nn = min(l0, key=lambda i: dist(pts[i], query))
        if all(h >= 1 for h in hops) and hops[2] >= 2 and cur == true_nn and sum(hops) <= 8:
            return pts, layers, graph, query, path
    raise RuntimeError("no seed produced a clean search path")


def banner(t, mode):
    W, H = 1000, 300
    svg = Svg(W, H, "Matías Blanco",
              "Matías Blanco, Computer Engineering at Columbia University. I build "
              "performance-critical software from scratch, from SIMD vector search to LLM "
              "inference engines. Illustration: a greedy search descending a three-layer HNSW graph.")
    card(svg, t, W, H)

    # faint dot grid that fades in toward the right
    svg.defs.append(
        f'<pattern id="dots" width="18" height="18" patternUnits="userSpaceOnUse">'
        f'<circle cx="9" cy="9" r="0.9" fill="{t["text3"]}"/></pattern>'
        f'<linearGradient id="fade" x1="0" x2="1"><stop offset="0.35" stop-color="#fff" '
        f'stop-opacity="0"/><stop offset="1" stop-color="#fff" stop-opacity="0.55"/></linearGradient>'
        f'<mask id="m"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask>')
    svg.add(f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="12" fill="url(#dots)" '
            f'mask="url(#m)" opacity="0.5"/>')

    x0 = 46
    eyebrow(svg, t, "Computer Engineering · Columbia University", x0, 72, 13)
    svg.text(F["disp"], "Matías Blanco", x0 - 3, 140, 62, t["text"], tracking=-0.02)
    for i, line in enumerate(["I build performance-critical software from scratch,",
                              "from SIMD vector search to LLM inference engines."]):
        svg.text(F["reg"], line, x0, 184 + i * 29, 20.5, t["text2"])

    xm = x0
    for i, item in enumerate(["AI Engineer @ Forva", "NYC ← Montevideo", "Class of ’29"]):
        if i:
            xm += 16
            svg.add(f'<circle cx="{n(xm)}" cy="255.5" r="2" fill="{t["accent"]}"/>')
            xm += 16
        xm += svg.text(F["mono"], item, xm, 260, 13.5, t["text2"])

    # ---- HNSW illustration
    pts, layers, graph, query, path = hnsw_scene()
    ox, PW, skew, D = 612, 280, 58, 52
    tops = {2: 44, 1: 124, 0: 204}

    def P(level, p):
        a, b = p
        return (ox + a * PW + (1 - b) * skew, tops[level] + b * D)

    for level in (2, 1, 0):
        y = tops[level]
        quad = [(ox + skew, y), (ox + skew + PW, y), (ox + PW, y + D), (ox, y + D)]
        d = "M" + " L".join(f"{n(a)} {n(b)}" for a, b in quad) + "Z"
        svg.add(f'<path d="{d}" fill="{t["plane"]}" fill-opacity="0.025" stroke="{t["border"]}"/>')
        svg.text(F["mono"], f"L{level}", ox + PW + skew / 2 + 18, y + D / 2 + 4, 12, t["text3"])

    # nodes that continue into the layer below
    for level in (2, 1):
        for i in layers[level]:
            (xa, ya), (xb, yb) = P(level, pts[i]), P(level - 1, pts[i])
            svg.add(f'<line x1="{n(xa)}" y1="{n(ya)}" x2="{n(xb)}" y2="{n(yb)}" '
                    f'stroke="{t["text3"]}" stroke-opacity="0.35" stroke-dasharray="1.5 3.5"/>')
    for level in (2, 1, 0):
        for i, j in graph[level][0]:
            (xa, ya), (xb, yb) = P(level, pts[i]), P(level, pts[j])
            svg.add(f'<line x1="{n(xa)}" y1="{n(ya)}" x2="{n(xb)}" y2="{n(yb)}" '
                    f'stroke="{t["edge"]}" stroke-width="1"/>')
    for level in (2, 1, 0):
        r = 3.2 if level == 0 else 3.8
        for i in layers[level]:
            x, y = P(level, pts[i])
            svg.add(f'<circle cx="{n(x)}" cy="{n(y)}" r="{r}" fill="{t["node"]}" '
                    f'stroke="{t["card"]}" stroke-width="1.5"/>')

    qx, qy = P(0, query)
    svg.add(f'<circle cx="{n(qx)}" cy="{n(qy)}" r="6.5" fill="none" stroke="{t["accent"]}" '
            f'stroke-width="1.5"/><circle cx="{n(qx)}" cy="{n(qy)}" r="1.8" fill="{t["accent"]}"/>')
    l0_xy = [P(0, pts[i]) for i in layers[0]]
    spots = [(qx + 11, qy + 4.5), (qx - 19, qy + 4.5), (qx - 4, qy - 11), (qx - 4, qy + 21)]
    lx, ly = max(spots, key=lambda s: min(math.hypot(s[0] + 4 - a, s[1] - 4.5 - b) for a, b in l0_xy))
    svg.text(F["monom"], "q", lx, ly, 13, t["accent"])

    # the animated search path
    start, step, seg_t = 0.7, 0.5, 0.4
    events = []
    prev = (2, path[0])
    for item in path[1:]:
        events.append((prev, item))
        prev = item
    T = start + len(events) * step + 3.2
    fade_a, fade_b = (T - 0.9) / T * 100, (T - 0.35) / T * 100
    css = [f".a{{animation-duration:{T:.2f}s;animation-iteration-count:infinite;"
           f"animation-timing-function:ease-in-out}}"
           "@media (prefers-reduced-motion:reduce){.a{animation:none!important}}"]

    def pct(sec):
        return f"{sec / T * 100:.2f}%"

    entry = P(2, pts[path[0]])
    def fade(name, on_a, on_b, prop):
        off = ";".join(f"{q}:0" for q in prop)
        on = ";".join(f"{q}:1" for q in prop)
        css.append(f"@keyframes {name}{{0%,{pct(on_a)}{{{off}}}{pct(on_b)},{fade_a:.2f}%{{{on}}}"
                   f"{fade_b:.2f}%,100%{{{off}}}}}")

    dot = ("fill-opacity", "stroke-opacity")
    fade("n0", start - 0.3, start, dot)
    svg.add(f'<circle class="a" style="animation-name:n0" cx="{n(entry[0])}" cy="{n(entry[1])}" '
            f'r="4.6" fill="{t["accent"]}" stroke="{t["card"]}" stroke-width="2"/>')
    for k, ((la, ia), (lb, ib)) in enumerate(events, start=1):
        (xa, ya), (xb, yb) = P(la, pts[ia]), P(lb, pts[ib])
        s0 = start + (k - 1) * step
        s1 = s0 + seg_t
        length = math.hypot(xb - xa, yb - ya)
        if la == lb:
            css.append(f"@keyframes s{k}{{0%,{pct(s0)}{{stroke-dashoffset:{length:.1f};opacity:1}}"
                       f"{pct(s1)},{fade_a:.2f}%{{stroke-dashoffset:0;opacity:1}}"
                       f"{fade_b:.2f}%,100%{{stroke-dashoffset:0;opacity:0}}}}")
            for width, op in ((7, 0.16), (2.2, 1)):
                svg.add(f'<line class="a" style="animation-name:s{k}" x1="{n(xa)}" y1="{n(ya)}" '
                        f'x2="{n(xb)}" y2="{n(yb)}" stroke="{t["accent"]}" stroke-width="{width}" '
                        f'stroke-opacity="{op}" stroke-linecap="round" '
                        f'stroke-dasharray="{length:.1f}"/>')
        else:
            fade(f"s{k}", s0, s1, ("stroke-opacity",))
            svg.add(f'<line class="a" style="animation-name:s{k}" x1="{n(xa)}" y1="{n(ya)}" '
                    f'x2="{n(xb)}" y2="{n(yb)}" stroke="{t["accent"]}" stroke-width="1.6" '
                    f'stroke-dasharray="3 3" stroke-linecap="round"/>')
        fade(f"n{k}", s1 - 0.05, s1 + 0.05, dot)
        svg.add(f'<circle class="a" style="animation-name:n{k}" cx="{n(xb)}" cy="{n(yb)}" '
                f'r="4.6" fill="{t["accent"]}" stroke="{t["card"]}" stroke-width="2"/>')

    done = start + len(events) * step
    css.append(f"@keyframes pulse{{0%,{pct(done - 0.1)}{{transform:scale(1);opacity:0}}{pct(done)}"
               f"{{transform:scale(1);opacity:.9}}{pct(done + 1.3)},100%{{transform:scale(2.8);"
               f"opacity:0}}}}")
    svg.add(f'<circle class="a" style="animation-name:pulse;animation-timing-function:ease-out;'
            f'transform-box:fill-box;transform-origin:center" '
            f'cx="{n(qx)}" cy="{n(qy)}" r="6.5" fill="none" stroke="{t["accent"]}" '
            f'stroke-width="1.5" opacity="0"/>')
    svg.style.extend(css)

    svg.text(F["mono"], "greedy search, top layer → bottom", ox, 284, 11.5, t["text3"])
    return svg


# ---------------------------------------------------------------------------- vecdex

# SIFT1M from Python, one thread, M=16, efConstruction=200, ef = 10..512.
# recall@10 by distance threshold, QPS median of 5 passes. Source:
# github.com/MatiiiBL/HNSW_vector_search/tree/main/bench/results/sift1m/sift-*.csv
SIFT = {
    "vecdex": [(0.7068, 70259), (0.8012, 52462), (0.9039, 31813), (0.9639, 17958),
               (0.9901, 9858), (0.9980, 5296), (0.9997, 2839)],
    "FAISS HNSW": [(0.7164, 40465), (0.8085, 30309), (0.9117, 18138), (0.9683, 10083),
                   (0.9911, 5340), (0.9980, 2761), (0.9997, 1366)],
    "hnswlib": [(0.7116, 24451), (0.8028, 18525), (0.9053, 11465), (0.9645, 6706),
                (0.9901, 3752), (0.9980, 2093), (0.9997, 1164)],
}


def project_left(svg, t, x, kicker, title, repo, desc, stats, tags, desc_width=420):
    eyebrow(svg, t, kicker, x, 54)
    tw = svg.text(F["disp"], title, x - 1.5, 98, 38, t["text"], tracking=-0.015)
    repo_link(svg, t, repo, x + tw + 14, 97)
    y = 134
    for line in wrap(F["reg"], desc, 16, desc_width):
        svg.text(F["reg"], line, x, y, 16, t["text2"])
        y += 24
    sy = y + 34
    for i, (value, label) in enumerate(stats):
        stat(svg, t, value, label, x + (0, 148, 290)[i], sy)
    cy = sy + 62
    chips(svg, t, tags, x, cy)
    return cy + 24


def big_card(svg, t, W, bottom, min_h):
    H = max(math.ceil(bottom + 36), min_h)
    svg.h = H
    card(svg, t, W, H, gradient=False, behind=True)
    return H


def vecdex(t, mode):
    W = 1000
    svg = Svg(W, 0, "vecdex: HNSW vector search in C++20",
              "18,000 queries per second at 96.4% recall@10 on SIFT1M, 1.78 times FAISS HNSW "
              "with the same parameters, 1M-vector build in 28 seconds on 10 threads. Chart: "
              "recall@10 against queries per second on SIFT1M for vecdex, FAISS HNSW and hnswlib; "
              "vecdex is fastest at every recall level.")
    x = 40
    bottom = project_left(
        svg, t, x, "Vector search · C++20", "vecdex", "MatiiiBL/HNSW_vector_search",
        "Approximate nearest-neighbor search on HNSW graphs, with NEON SIMD distance kernels, a "
        "multithreaded build, crash-safe save/load and zero-copy NumPy bindings.",
        [("18.0K", ["queries/s at", "96.4% recall@10"]),
         ("1.78×", ["FAISS HNSW,", "same parameters"]),
         ("28 s", ["1M-vector build", "on 10 threads"])],
        ["C++20", "NEON", "pybind11", "libFuzzer", "TSan"])
    H = big_card(svg, t, W, bottom, 384)

    # ---- chart panel
    px, py, pw, ph = 498, 24, 478, H - 48
    svg.add(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="10" fill="{t["card2"]}" '
            f'stroke="{t["grid"]}"/>')
    cx0 = px + 24
    svg.text(F["semi"], "SIFT1M: recall@10 vs. queries/s", cx0, py + 32, 14.5, t["text"])
    svg.text(F["mono"], "log scale · 1 thread · Apple M4 · M=16, efC=200", cx0, py + 52, 11.5,
             t["text3"])

    names = list(SIFT)
    lx = cx0
    for i, name in enumerate(names):
        c = t["series"][i]
        svg.add(f'<line x1="{n(lx)}" y1="{py + 76}" x2="{n(lx + 16)}" y2="{py + 76}" stroke="{c}" '
                f'stroke-width="2" stroke-linecap="round"/><circle cx="{n(lx + 8)}" cy="{py + 76}" '
                f'r="3.5" fill="{c}" stroke="{t["card2"]}" stroke-width="2"/>')
        lx += 24 + svg.text(F["med"], name, lx + 22, py + 80.5, 12.5, t["text2"]) + 18

    # plot area
    ax0, ax1 = px + 64, px + pw - 22
    ay0, ay1 = py + ph - 44, py + 102          # bottom, top
    xmin, xmax = 0.70, 1.00
    ymin, ymax = math.log10(1000), math.log10(80000)

    def X(r):
        return ax0 + (r - xmin) / (xmax - xmin) * (ax1 - ax0)

    def Y(q):
        return ay0 - (math.log10(q) - ymin) / (ymax - ymin) * (ay0 - ay1)

    for q, label in ((1000, "1K"), (3000, "3K"), (10000, "10K"), (30000, "30K")):
        y = Y(q)
        svg.add(f'<line x1="{n(ax0)}" y1="{n(y)}" x2="{n(ax1)}" y2="{n(y)}" stroke="{t["grid"]}" '
                f'stroke-width="1"/>')
        svg.text(F["mono"], label, ax0 - 10, y + 4, 11, t["text3"], anchor="end")
    svg.add(f'<line x1="{n(ax0)}" y1="{n(ay0)}" x2="{n(ax1)}" y2="{n(ay0)}" stroke="{t["border"]}" '
            f'stroke-width="1"/>')
    for r in (0.7, 0.8, 0.9, 1.0):
        svg.text(F["mono"], f"{r:.1f}", X(r), ay0 + 18, 11, t["text3"], anchor="middle")
    svg.text(F["reg"], "recall@10 →", ax1, ay0 + 34, 11.5, t["text3"], anchor="end")

    for i, name in reversed(list(enumerate(names))):
        c = t["series"][i]
        d = "M" + " L".join(f"{n(X(r))} {n(Y(q))}" for r, q in SIFT[name])
        svg.add(f'<path d="{d}" fill="none" stroke="{c}" stroke-width="2" stroke-linejoin="round" '
                f'stroke-linecap="round"/>')
        for r, q in SIFT[name]:
            svg.add(f'<circle cx="{n(X(r))}" cy="{n(Y(q))}" r="4" fill="{c}" stroke="{t["card2"]}" '
                    f'stroke-width="2"/>')

    # the comparison behind the 1.78x claim: smallest ef that reaches recall >= 0.95 (ef = 64)
    (rv, qv), (rf, qf) = SIFT["vecdex"][3], SIFT["FAISS HNSW"][3]
    (xv, yv), (xf, yf) = (X(rv), Y(qv)), (X(rf), Y(qf))
    for cx, cy in ((xv, yv), (xf, yf)):
        svg.add(f'<circle cx="{n(cx)}" cy="{n(cy)}" r="8" fill="none" stroke="{t["text"]}" '
                f'stroke-width="1.2"/>')
    svg.add(f'<line x1="{n(xv + 1)}" y1="{n(yv + 8)}" x2="{n(xf - 1)}" y2="{n(yf - 8)}" '
            f'stroke="{t["text"]}" stroke-width="1.2"/>')
    svg.add(f'<line x1="{n(xv)}" y1="{n(yv - 8)}" x2="{n(xv)}" y2="{n(yv - 24)}" '
            f'stroke="{t["text"]}" stroke-width="1.2"/>')
    svg.text(F["semi"], "1.78× FAISS", ax1, yv - 44, 13, t["text"], anchor="end")
    svg.text(F["reg"], "at recall ≥ 0.95", ax1, yv - 29, 11, t["text2"], anchor="end")
    return svg


# ---------------------------------------------------------------------------- minillm


def minillm(t, mode):
    W = 1000
    svg = Svg(W, 0, "minillm: an LLM inference engine in C++20",
              "A from-scratch Llama-architecture inference engine running SmolLM2-135M end to end. "
              "Greedy tokens match a PyTorch oracle exactly; Q8_0 weights are 3.8 times smaller "
              "(538 to 143 MB); ASan, UBSan and TSan run in CI. Diagram: tokenizer, embedding, "
              "30 decoder blocks of RMSNorm, attention with RoPE and a KV cache, RMSNorm and a "
              "SwiGLU MLP, then the final norm, LM head and sampler.")
    x = 40
    bottom = project_left(
        svg, t, x, "LLM inference · C++20", "minillm", "MatiiiBL/LLM-inference-engine",
        "Llama-architecture inference from scratch, running SmolLM2-135M end to end. Every kernel "
        "exists twice: a scalar reference checked against PyTorch, and a fast one checked "
        "against the reference.",
        [("Exact", ["greedy-token match", "with PyTorch"]),
         ("3.8×", ["smaller weights,", "Q8_0 (538→143 MB)"]),
         ("3", ["sanitizers in CI:", "ASan, UBSan, TSan"])],
        ["C++20", "safetensors", "bf16", "Q8_0", "doctest"])
    H = big_card(svg, t, W, bottom, 352)

    px, py, pw, ph = 498, 24, 478, H - 48
    svg.add(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="10" fill="{t["card2"]}" '
            f'stroke="{t["grid"]}"/>')
    cx0 = px + 24
    svg.text(F["semi"], "One forward pass", cx0, py + 32, 14.5, t["text"])
    svg.text(F["mono"], "SmolLM2-135M · 30 layers · d=576 · vocab 49,152", cx0, py + 52, 11.5,
             t["text3"])

    def box(label, x, y, sub=None, accent=False, w=None):
        size = 12
        w = w or max(F["mono"].width(label, size), F["mono"].width(sub or "", 10.5)) + 22
        h = 40 if sub else 28
        stroke = t["accent"] if accent else t["border"]
        svg.add(f'<rect x="{n(x)}" y="{n(y - h / 2)}" width="{n(w)}" height="{h}" rx="7" '
                f'fill="{t["card"]}" stroke="{stroke}"' + (' stroke-opacity="0.7"' if accent else '')
                + '/>')
        if sub:
            svg.text(F["monom"], label, x + w / 2, y - 2, size, t["text"], anchor="middle")
            svg.text(F["mono"], sub, x + w / 2, y + 13, 10.5, t["text3"], anchor="middle")
        else:
            svg.text(F["monom"], label, x + w / 2, y + 4.3, size, t["text"], anchor="middle")
        return w

    svg.defs.append(f'<marker id="ar" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" '
                    f'markerHeight="7" orient="auto-start-reverse"><path d="M1 1 L7 4 L1 7" '
                    f'fill="none" stroke="{t["text3"]}" stroke-width="1.4" stroke-linecap="round" '
                    f'stroke-linejoin="round"/></marker>')

    def arrow(x1, y1, x2, y2):
        svg.add(f'<line x1="{n(x1)}" y1="{n(y1)}" x2="{n(x2)}" y2="{n(y2)}" stroke="{t["text3"]}" '
                f'stroke-width="1.2" marker-end="url(#ar)"/>')

    def row(items, x, y, gap=22):
        spans = []
        for k, (label, sub, acc) in enumerate(items):
            w = box(label, x, y, sub, acc)
            spans.append((x, x + w))
            if k < len(items) - 1:
                arrow(x + w + 3, y, x + w + gap - 3, y)
            x += w + gap
        return spans

    extra = (ph - 304) / 2
    r1y, r2y, r3y = py + 92 + extra, py + 168 + extra, py + 252 + extra
    s1 = row([("prompt", None, False), ("tokenizer", "BPE", False), ("embedding", "49,152 × 576", False)],
             cx0, r1y)

    # decoder block group
    gx0, gx1 = cx0 - 8, px + pw - 16
    svg.add(f'<rect x="{n(gx0)}" y="{n(r2y - 36)}" width="{n(gx1 - gx0)}" height="72" rx="10" '
            f'fill="{t["accent_soft"]}" fill-opacity="0.5" stroke="{t["accent"]}" '
            f'stroke-opacity="0.45" stroke-dasharray="4 4"/>')
    svg.text(F["monom"], "× 30", gx1 - 10, r2y - 42, 12, t["accent"], anchor="end")
    s2 = row([("RMSNorm", None, False), ("attention", "RoPE · KV cache", True),
              ("RMSNorm", None, False), ("SwiGLU", "MLP", False)], cx0 + 4, r2y, gap=20)
    s3 = row([("RMSNorm", None, False), ("LM head", "→ logits", False), ("sampler", None, False),
              ("next token", None, True)], cx0, r3y)

    # row-to-row connectors
    def elbow(xa, ya, xb, yb):
        mid = (ya + yb) / 2
        svg.add(f'<path d="M{n(xa)} {n(ya)} V{n(mid)} H{n(xb)} V{n(yb - 3)}" fill="none" '
                f'stroke="{t["text3"]}" stroke-width="1.2" marker-end="url(#ar)"/>')

    elbow((s1[-1][0] + s1[-1][1]) / 2, r1y + 20, (s2[0][0] + s2[0][1]) / 2, r2y - 36)
    elbow((s2[-1][0] + s2[-1][1]) / 2, r2y + 36, (s3[0][0] + s3[0][1]) / 2, r3y - 14)

    # autoregressive loop: next token goes back in, past keys/values stay cached
    lx = s3[-1][1] + 10
    svg.add(f'<path d="M{n(lx)} {n(r3y)} H{n(gx1 + 6)} V{n(r1y)} H{n(s1[-1][1] + 4)}" fill="none" '
            f'stroke="{t["accent"]}" stroke-opacity="0.75" stroke-width="1.2" '
            f'stroke-dasharray="3 3" marker-end="url(#ar)"/>')
    svg.text(F["mono"], "decode loop", gx1 - 2, r1y - 8, 10.5, t["accent"], anchor="end")
    return svg


# ---------------------------------------------------------------------------- slim rows


SLIM_DESC = dict(size=15, width=880, lead=22)


def slim_lines(desc):
    return wrap(F["reg"], desc, SLIM_DESC["size"], SLIM_DESC["width"])


def slim(t, mode, kicker, title, award, desc, tags, repo, alt, H):
    W = 1000
    svg = Svg(W, H, title, alt)
    card(svg, t, W, H, gradient=False)
    x = 40
    eyebrow(svg, t, kicker, x, 44, 12)
    tw = svg.text(F["disp"], title, x - 1, 80, 28, t["text"], tracking=-0.01)
    if award:
        pill(svg, t, award, x + tw + 16, 71)
    y = 110
    for line in slim_lines(desc):
        svg.text(F["reg"], line, x, y, SLIM_DESC["size"], t["text2"])
        y += SLIM_DESC["lead"]
    rx = W - 40
    chips(svg, t, tags, rx, 32, size=11.5, gap=7, anchor="end")
    repo_link(svg, t, repo, rx, 80, anchor="end")
    return svg


SLIMS = {
    "memo": dict(
        kicker="Robotics · assistive hardware", title="memo", award="AI CATEGORY WINNER · makeCU",
        desc="A tendon-driven glove (5 servos) that helps stroke patients open their hand. I owned "
             "the webcam hand tracking: MediaPipe finger-flexion measurement, calibration and "
             "temporal filtering.",
        tags=["ESP32", "MediaPipe", "TypeScript", "Python"], repo="MateoVidalS/makecu-guante",
        alt="memo, AI category winner at the makeCU hackathon: a tendon-driven stroke-rehab glove; "
            "I owned the webcam hand tracking."),
    "wattsgood": dict(
        kicker="Multi-agent LLM app", title="WattsGood", award="1ST PLACE · 8-HOUR HACKATHON",
        desc="Three orchestrated Claude Haiku 4.5 agents (eligibility parsing, program matching, "
             "plain-language explanation) connect low-income households to unclaimed energy "
             "assistance. Built with a 4-person team.",
        tags=["JavaScript", "React", "Claude API"], repo="MatiiiBL/housing-energy-assistance",
        alt="WattsGood, first place at an 8-hour hackathon: three orchestrated Claude agents that "
            "match households to energy assistance programs."),
    "shellc": dict(
        kicker="Systems · POSIX", title="ShellC", award=None,
        desc="A bash-like Unix shell in C: quote-aware parser, builtins, fork/exec with exit-status "
             "reporting, SIGPIPE handling, and byte-at-a-time stdin so child processes share input "
             "correctly. No heap allocation.",
        tags=["C", "POSIX", "make", "CI"], repo="MatiiiBL/ShellC",
        alt="ShellC: a small bash-like Unix shell written in C with no heap allocation."),
}


# ---------------------------------------------------------------------------- main


def main():
    ensure_fonts()
    load_faces()
    ASSETS.mkdir(exist_ok=True)
    builders = {"banner": banner, "vecdex": vecdex, "minillm": minillm}
    lines = max(len(slim_lines(spec["desc"])) for spec in SLIMS.values())
    slim_h = 110 + (lines - 1) * SLIM_DESC["lead"] + 36
    for mode, t in THEMES.items():
        for name, fn in builders.items():
            out = ASSETS / f"{name}-{mode}.svg"
            out.write_text(fn(t, mode).render())
        for name, spec in SLIMS.items():
            out = ASSETS / f"{name}-{mode}.svg"
            out.write_text(slim(t, mode, H=slim_h, **spec).render())
    for p in sorted(ASSETS.glob("*.svg")):
        print(f"{p.relative_to(ROOT)}  {p.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
