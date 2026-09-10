import io, re, math

TILE, GAP, RX = 48, 9, 11
BG = "#F5F5F5"

# (文件名, 显示名, 单色填充或 None=保留原色)
ICONS = [
    ("Python-Light.svg", "Python", None),
    ("CPP.svg", "C++", None),
    ("PyTorch-Light.svg", "PyTorch", None),
    ("si-huggingface.svg", "Hugging Face", "#2F2F2F"),
    ("si-claude.svg", "Claude", "#D97757"),
    ("si-openai.svg", "Codex", "#111111"),
    ("si-cursor.svg", "Cursor", "#111111"),
    ("si-githubcopilot.svg", "GitHub Copilot", "#111111"),
    ("Docker.svg", "Docker", None),
    ("Windows-Light.svg", "Windows", None),
    ("Ubuntu-Light.svg", "Ubuntu", None),
    ("Markdown-Light.svg", "Markdown", None),
    ("LaTeX-Light.svg", "LaTeX", None),
    ("Obsidian-Light.svg", "Obsidian", None),
    ("VSCode-Light.svg", "VS Code", None),
    ("VisualStudio-Light.svg", "Visual Studio", None),
    ("PyCharm-Light.svg", "PyCharm", None),
]

PERLINE = 9
rows = [ICONS[i:i+PERLINE] for i in range(0, len(ICONS), PERLINE)]
W = PERLINE * TILE + (PERLINE - 1) * GAP
H = len(rows) * TILE + (len(rows) - 1) * GAP

def parse(path):
    s = io.open(path, encoding='utf-8').read()
    m = re.search(r'viewBox="([-\d\.\s]+)"', s)
    if m:
        x, y, w, h = [float(v) for v in m.group(1).split()]
    else:
        w = float(re.search(r'width="(\d+)', s).group(1)); h = float(re.search(r'height="(\d+)', s).group(1)); x = y = 0
    inner = re.sub(r'^.*?<svg[^>]*>', '', s.strip(), count=1, flags=re.S)
    inner = re.sub(r'</svg>\s*$', '', inner).strip()
    inner = re.sub(r'<!--.*?-->', '', inner, flags=re.S)
    return x, y, w, h, inner

parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="tech stack icons">']
for ri, row in enumerate(rows):
    # 每行独立居中
    rowW = len(row) * TILE + (len(row) - 1) * GAP
    x0 = (W - rowW) / 2
    for ci, (fname, label, mono) in enumerate(row):
        px = x0 + ci * (TILE + GAP)
        py = ri * (TILE + GAP)
        x, y, w, h, inner = parse(fname)
        if mono:
            # simple-icons 单色路径：给 path 直接上色
            inner = re.sub(r'<path(?![^>]*fill)', '<path fill="' + mono + '"', inner)
        s = min(30.0 / w, 30.0 / h)
        ox = px + (TILE - w * s) / 2 - x * s
        oy = py + (TILE - h * s) / 2 - y * s
        parts.append(f'<g><title>{label}</title><rect x="{px}" y="{py}" width="{TILE}" height="{TILE}" rx="{RX}" fill="{BG}"/><g transform="translate({ox:.2f},{oy:.2f}) scale({s:.4f})">{inner}</g></g>')
parts.append('</svg>')
out = '\n'.join(parts)
io.open('skill-icons.svg', 'w', encoding='utf-8').write(out)
print(f"生成 skill-icons.svg: {W}x{H}, {len(ICONS)} 图标, {len(rows)} 行")
