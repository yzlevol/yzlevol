#!/usr/bin/env python3
"""合成 My Tech Stack 图标带（无底色透明版，深/浅主题各一份）。

图标源：
  - tandpfun/skill-icons 官方库（语言/系统/编辑器，保留原色）
  - lobehub/lobe-icons 静态包（AI 品牌彩色图标：Claude、Codex 等）
  - simple-icons（个别补充）
运行：python skill_icons.py   （需能访问 raw.githubusercontent.com 与 cdn.jsdelivr.net）
输出：profile/skill-icons.svg（浅色主题）与 profile/skill-icons-dark.svg（深色主题）

想增删图标：改下方 ICONS 列表（显示名, 来源, 文件名, 浅色填充, 深色填充）。
注意：单色重染仅对单一路径的源安全（simple-icons / Rust 齿轮）；
skill-icons 的复合图标（如 Markdown 徽章）禁止重染，会变实心色块。
"""
import io
import os
import re
import urllib.request

SIZE, GAP = 40, 10
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "profile")

RAW = "https://raw.githubusercontent.com"
SOURCES = {
    "skillicons": RAW + "/tandpfun/skill-icons/main/icons/{}.svg",
    "simpleicons": RAW + "/simple-icons/simple-icons/develop/icons/{}.svg",
    "lobeicons": "https://cdn.jsdelivr.net/npm/@lobehub/icons-static-svg@1.95.0/icons/{}.svg",
}

# (显示名, 来源, 文件名, 浅色主题单色填充, 深色主题单色填充；None=保留原色)
ICONS = [
    ("Python",     "skillicons", "Python-Light", None, None),
    ("C++",        "skillicons", "CPP", None, None),
    ("TypeScript", "skillicons", "TypeScript", None, None),
    ("Rust",       "skillicons", "Rust", None, "#D4D4D4"),  # 黑齿轮在深色背景不可见
    ("Claude",     "lobeicons", "claude-color", None, None),
    ("Codex",      "lobeicons", "codex-color", None, None),
    ("VS Code",    "skillicons", "VSCode-Light", None, None),
    ("Windows",    "skillicons", "Windows-Light", None, None),
    ("Ubuntu",     "skillicons", "Ubuntu-Light", None, None),
    ("Markdown",   "skillicons", "Markdown-Light", None, None),
    ("LaTeX",      "skillicons", "LaTeX-Light", None, None),
    ("Inkscape",   "simpleicons", "inkscape", "#4B5B6B", "#4B5B6B"),
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

def recolor_mono(inner, mono):
    """整体重上色（仅限单一路径源），清除 fill/stroke 后统一上色。"""
    inner = re.sub(r'\s(?:fill|stroke)="[^"]*"', '', inner)
    return f'<g fill="{mono}">' + inner + "</g>"

def build(theme):
    """theme: 'light' 或 'dark'，返回 SVG 字符串。"""
    n = len(ICONS)
    W = n * SIZE + (n - 1) * GAP
    H = SIZE
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="tech stack icons">']
    for i, (label, src, fname, mono_light, mono_dark) in enumerate(ICONS):
        mono = mono_light if theme == "light" else mono_dark
        x, y, w, h, inner = parse(fetch(SOURCES[src].format(fname)))
        inner = namespace_ids(inner, f"i{i}_")
        if mono:
            inner = recolor_mono(inner, mono)
        s = min(SIZE / w, SIZE / h)
        px = i * (SIZE + GAP)
        ox = px + (SIZE - w * s) / 2 - x * s
        oy = (SIZE - h * s) / 2 - y * s
        parts.append(f'<g><title>{label}</title><g transform="translate({ox:.2f},{oy:.2f}) scale({s:.4f})">{inner}</g></g>')
    parts.append("</svg>")
    return "\n".join(parts)

def main():
    for theme, name in (("light", "skill-icons.svg"), ("dark", "skill-icons-dark.svg")):
        out = os.path.join(OUT_DIR, name)
        with io.open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(build(theme))
        print(f"生成 {out} ({theme})")

if __name__ == "__main__":
    main()
