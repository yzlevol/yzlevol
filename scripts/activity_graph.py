#!/usr/bin/env python3
"""Generate an activity-graph SVG styled after Ashutosh00710/github-readme-activity-graph (rogue theme).

Data comes from the GitHub GraphQL API (contributionCalendar). No third-party
dependencies: urllib + stdlib only.

Usage:
  GH_TOKEN=... python activity_graph.py --username flesymeb --out profile/activity-graph.svg
"""
import argparse
import datetime as dt
import json
import os
import sys
import urllib.request

# rogue theme (src/styles/themes.ts)
C_BG = "#172030"
C_LINE = "#b18bb1"
C_POINT = "#c6797e"
C_TEXT = "#a3b09a"
C_AREA = "#b18bb1"

WIDTH, HEIGHT = 1200, 420
PAD_TOP, PAD_RIGHT, PAD_BOTTOM, PAD_LEFT = 80, 50, 20, 20
AXIS_Y_OFFSET, AXIS_X_OFFSET = 70, 50   # space for y / x labels
DAYS = 31

QUERY = """
query($LOGIN: String!, $FROM: DateTime!, $TO: DateTime!) {
  user(login: $LOGIN) {
    name
    contributionsCollection(from: $FROM, to: $TO) {
      contributionCalendar {
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def fetch_days(token, username, days):
    to = dt.datetime.now(dt.timezone.utc)
    frm = to - dt.timedelta(days=days - 1)
    frm = frm.replace(hour=0, minute=0, second=0, microsecond=0)
    body = json.dumps({
        "query": QUERY.strip(),
        "variables": {"LOGIN": username, "FROM": frm.isoformat(), "TO": to.isoformat()},
    }).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql", data=body, method="POST",
        headers={"Authorization": "bearer " + token,
                 "Content-Type": "application/json",
                 "User-Agent": "activity-graph-generator"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    if "errors" in data:
        raise RuntimeError("GraphQL error: " + json.dumps(data["errors"])[:300])
    user = data["data"]["user"]
    if user is None:
        raise RuntimeError("user not found: " + username)
    name = user["name"] or username
    flat = {}
    for w in user["contributionsCollection"]["contributionCalendar"]["weeks"]:
        for d in w["contributionDays"]:
            flat[d["date"]] = d["contributionCount"]
    out = []
    for i in range(days):
        d = (frm + dt.timedelta(days=i)).date().isoformat()
        out.append((d, flat.get(d, 0)))
    return name, out


def monotone_tangents(xs, ys):
    n = len(xs)
    if n < 2:
        return [0.0] * n
    d = [(ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]) for i in range(n - 1)]
    m = [0.0] * n
    m[0], m[-1] = d[0], d[-1]
    for i in range(1, n - 1):
        if d[i - 1] * d[i] <= 0:
            m[i] = 0.0
        else:
            h1 = xs[i] - xs[i - 1]
            h2 = xs[i + 1] - xs[i]
            w1, w2 = 2 * h2 + h1, h2 + 2 * h1
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    return m


def smooth_path(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    m = monotone_tangents(xs, ys)
    parts = ["M {:.2f} {:.2f}".format(xs[0], ys[0])]
    for i in range(len(pts) - 1):
        h = (xs[i + 1] - xs[i]) / 3.0
        c1 = (xs[i] + h, ys[i] + m[i] * h)
        c2 = (xs[i + 1] - h, ys[i + 1] - m[i + 1] * h)
        parts.append("C {:.2f} {:.2f} {:.2f} {:.2f} {:.2f} {:.2f}".format(
            c1[0], c1[1], c2[0], c2[1], xs[i + 1], ys[i + 1]))
    return " ".join(parts)


def nice_ceil(v):
    if v <= 4: return 4
    if v <= 8: return 8
    step = 1
    while step * 4 < v:
        step *= 2 if step < 4 else 5 if step == 4 else 10
    # round up to a multiple of a nice step producing ~4 ticks
    for s in (2, 4, 5, 10, 20, 25, 50, 100, 200):
        if v <= s * 4:
            return s * ((v + s - 1) // s)
    return v


def build_svg(name, days_data):
    x0 = PAD_LEFT + AXIS_Y_OFFSET
    x1 = WIDTH - PAD_RIGHT
    y0 = PAD_TOP
    y1 = HEIGHT - PAD_BOTTOM - AXIS_X_OFFSET
    n = len(days_data)
    counts = [c for _, c in days_data]
    vmax = max(max(counts), 1)
    top = nice_ceil(vmax)
    ticks = 4
    def px(i): return x0 + (x1 - x0) * i / (n - 1)
    def py(v): return y1 - (y1 - y0) * v / top

    pts = [(px(i), py(c)) for i, c in enumerate(counts)]
    line_path = smooth_path(pts)
    area_path = line_path + " L {:.2f} {:.2f} L {:.2f} {:.2f} Z".format(px(n - 1), y1, px(0), y1)

    grid, ylabels = [], []
    for t in range(ticks + 1):
        v = top * t // ticks
        gy = py(v)
        if gy < y0 - 0.5 or gy > y1 + 0.5: continue
        grid.append('<line class="ct-grid" x1="{:.1f}" x2="{:.1f}" y1="{gy:.1f}" y2="{gy:.1f}"/>'.format(x0, x1, gy=gy))
        ylabels.append('<text class="ct-label" x="{:.1f}" y="{:.1f}" text-anchor="end">{}</text>'.format(x0 - 6, gy + 4, v))

    xlabels, vgrid = [], []
    for i, (d, _) in enumerate(days_data):
        if i % 3 == 1 or (i == n - 1 and (n - 1) % 3 != 1):
            date = dt.date.fromisoformat(d)
            label = date.strftime("%b %d")
            xlabels.append('<text class="ct-label" x="{:.1f}" y="{:.1f}" text-anchor="middle">{}</text>'.format(px(i), y1 + 18, label))
            vgrid.append('<line class="ct-grid" x1="{x:.1f}" x2="{x:.1f}" y1="{y0:.1f}" y2="{y1:.1f}"/>'.format(x=px(i), y0=y0, y1=y1))

    points = "".join('<circle class="ct-point" cx="{:.1f}" cy="{:.1f}" r="5"/>'.format(x, y) for x, y in pts)

    return f'''<svg width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{name}'s contribution graph">
  <style>
    .header {{ font: 600 20px 'Segoe UI', Ubuntu, Sans-Serif; fill: {C_TEXT}; }}
    .ct-label {{ fill: {C_TEXT}; color: {C_TEXT}; font: 600 12px 'Segoe UI', Ubuntu, Sans-Serif; }}
    .ct-grid {{ stroke: {C_TEXT}; stroke-width: 1px; stroke-opacity: 0.3; stroke-dasharray: 2px; }}
    .ct-line {{ fill: none; stroke: {C_LINE}; stroke-width: 4px; stroke-linecap: round; stroke-linejoin: round; }}
    .ct-area {{ stroke: none; fill: {C_AREA}; fill-opacity: 0.1; }}
    .ct-point {{ fill: {C_POINT}; stroke: {C_POINT}; stroke-width: 0; }}
    .ct-axis-title {{ fill: {C_TEXT}; font: 600 12px 'Segoe UI', Ubuntu, Sans-Serif; }}
  </style>
  <rect data-testid="card_bg" x="0" y="0" rx="0" height="100%" width="100%" fill="{C_BG}" stroke="none"/>
  <text class="header" x="{WIDTH / 2}" y="42" text-anchor="middle">{name}&apos;s Contribution Graph</text>
  <g>{"".join(grid)}{"".join(vgrid)}</g>
  <g>{"".join(ylabels)}{"".join(xlabels)}</g>
  <path class="ct-area" d="{area_path}"/>
  <path class="ct-line" d="{line_path}"/>
  <g>{points}</g>
  <text class="ct-axis-title" x="14" y="{(y0 + y1) / 2}" text-anchor="middle" transform="rotate(-90 14 {(y0 + y1) / 2})">Contributions</text>
  <text class="ct-axis-title" x="{(x0 + x1) / 2}" y="{HEIGHT - 8}" text-anchor="middle">Days</text>
</svg>
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--username", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--days", type=int, default=DAYS)
    args = ap.parse_args()
    token = os.environ.get("GH_TOKEN") or os.environ.get("PAT_1") or os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("need GH_TOKEN / PAT_1 / GITHUB_TOKEN env")
    name, data = fetch_days(token, args.username, args.days)
    svg = build_svg(name, data)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {args.out} ({len(svg)} bytes, {args.days} days, user={name})")


if __name__ == "__main__":
    main()
