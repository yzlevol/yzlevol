#!/usr/bin/env python3
"""合成 My Tech Stack 图标带（skillicons 风格，白底磁贴）。

图标源：tandpfun/skill-icons 官方库 + simple-icons（AI 品牌图标，skillicons 无）。
运行：python skill_icons.py   （需要能访问 raw.githubusercontent.com）
输出：profile/skill-icons.svg

想增删图标：改下方 ICONS 列表，重新运行即可。
注意：每个图标的内部 id 都会加唯一前缀，避免合并后渐变/裁剪路径互相串色。
"""
import io
import os
import re
import urllib.request

TILE, GAP, RX = 48, 9, 11
BG, BORDER = "#FFFFFF", "#E5E7EB"
PERLINE = 7
OUT = os.path.join(os.path.dirname(__file__), "..", "profile", "skill-icons.svg")

RAW = "https://raw.githubusercontent.com"
SOURCES = {
    "skillicons": RAW + "/tandpfun/skill-icons/main/icons/{}.svg",
    "simpleicons": RAW + "/simple-icons/simple-icons/develop/icons/{}.svg",
    "openai-legacy": RAW + "/simple-icons/simple-icons/13.0.0/icons/openai.svg",
}

# (显示名, 来源, 文件名, 单色填充或 None=保留原色)
ICONS = [
    ("Python",          "skillicons", "Python-Light", None),
    ("C++",             "skillicons", "CPP", None),
    ("PyTorch",         "skillicons", "PyTorch-Light", None),
    ("Hugging Face",    "simpleicons", "huggingface", "#2F2F2F"),
    ("Claude",          "simpleicons", "claude", "#D97757"),
    ("Codex",           "openai-legacy", "openai", "#111111"),
    ("Cursor",          "simpleicons", "cursor", "#111111"),
    ("GitHub Copilot",  "simpleicons", "githubcopilot", "#111111"),
    ("Docker",          "skillicons", "Docker", None),
    ("Windows",         "skillicons", "Windows-Light", None),
    ("Ubuntu",          "skillicons", "Ubuntu-Light", None),
    ("LaTeX",           "skillicons", "LaTeX-Light", None),
    ("Obsidian",        "skillicons", "Obsidian-Light", None),
    ("VS Code",         "skillicons", "VSCode-Light", None),
]

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "skill-icons-composer"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")

def parse(svg):
    m = re.search(r'viewBox="([-\d\.\s]+)"', svg)
    if m:
        x, y, w, h = [float(v) for v in m.group(1).split()]
    else:
        w = float(re.search(r'width="(\d+)', svg).group(1))
        h = float(re.search(r'height="(\d+)', svg).group(1))
        x = y = 0
    inner = re.sub(r'^.*?<svg[^>]*>', '', svg.strip(), count=1, flags=re.S)
    inner = re.sub(r'</svg>\s*$', '', inner).strip()
    inner = re.sub(r'<!--.*?-->', '', inner, flags=re.S)
    return x, y, w, h, inner

def namespace_ids(inner, prefix):
    """给图标内部的 id 及其引用加前缀，防止合并后跨图标串色。"""
    for old in sorted(set(re.findall(r'id="([^"]+)"', inner)), key=len, reverse=True):
        new = prefix + old
        inner = inner.replace(f'id="{old}"', f'id="{new}"')
        inner = inner.replace(f'url(#{old})', f'url(#{new})')
        inner = inner.replace(f"url('#{old}')", f"url('#{new}')")
        inner = inner.replace(f'url("#{old}")', f'url("#{new}")')
        inner = inner.replace(f'href="#{old}"', f'href="#{new}"')
        inner = inner.replace(f'xlink:href="#{old}"', f'xlink:href="#{new}"')
    return inner

def main():
    rows = [ICONS[i:i + PERLINE] for i in range(0, len(ICONS), PERLINE)]
    W = PERLINE * TILE + (PERLINE - 1) * GAP
    H = len(rows) * TILE + (len(rows) - 1) * GAP
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="tech stack icons">']
    for ri, row in enumerate(rows):
        rowW = len(row) * TILE + (len(row) - 1) * GAP
        x0 = (W - rowW) / 2
        for ci, (label, src, fname, mono) in enumerate(row):
            x, y, w, h, inner = parse(fetch(SOURCES[src].format(fname)))
            inner = namespace_ids(inner, f"i{ri}_{ci}_")
            if mono:
                inner = re.sub(r'<path(?![^>]*fill)', '<path fill="' + mono + '"', inner)
            s = min(30.0 / w, 30.0 / h)
            px = x0 + ci * (TILE + GAP)
            py = ri * (TILE + GAP)
            ox = px + (TILE - w * s) / 2 - x * s
            oy = py + (TILE - h * s) / 2 - y * s
            parts.append(
                f'<g><title>{label}</title>'
                f'<rect x="{px}" y="{py}" width="{TILE}" height="{TILE}" rx="{RX}" fill="{BG}" stroke="{BORDER}" stroke-width="1"/>'
                f'<g transform="translate({ox:.2f},{oy:.2f}) scale({s:.4f})">{inner}</g></g>'
            )
    parts.append("</svg>")
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(parts))
    print(f"生成 {OUT}: {W}x{H}, {len(ICONS)} 图标, {len(rows)} 行")

if __name__ == "__main__":
    main()
