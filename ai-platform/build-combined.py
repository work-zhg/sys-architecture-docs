#!/usr/bin/env python3
"""把两张 archify 图打包成一个自包含 HTML。

两个 viewer 各自带完整 runtime（~650KB、上百处 getElementById、无 shadow DOM），
直接拼进同一个 document 会撞 id 与全局状态 —— 缩放、搜索、guided views、导出
全都会坏。所以用 iframe 隔离，再把两份 HTML 以 base64 内联进来，
保持「单文件」的同时让两张图的交互各自完整。

懒加载：切到哪张才解码注入哪张，首屏只付一张图的代价。

用法：python3 build-combined.py
"""

from __future__ import annotations

import base64
import pathlib

HERE = pathlib.Path(__file__).parent

DIAGRAMS = [
    ("overview", "概览", "atlas-overview.html",
     "AI Platform 设计：两类 Agent、对象模型、能力矩阵、决策与代价"),
    ("arch", "调用链路", "atlas-architecture.html",
     "atlas 实现：一次请求怎么流动、分层与事件回传"),
    ("deploy", "组件与部署", "atlas-deployment.html",
     "atlas 实现：组件构成、部署位置与外部依赖"),
]

OUT = HERE / "atlas-architecture-overview.html"


def main() -> None:
    panels, scripts, tabs = [], [], []
    for i, (key, title, filename, desc) in enumerate(DIAGRAMS):
        src = HERE / filename
        if not src.exists():
            raise SystemExit(f"缺少 {filename} —— 先跑 archify deliver 生成它")
        b64 = base64.b64encode(src.read_bytes()).decode("ascii")
        active = " is-active" if i == 0 else ""
        tabs.append(
            f'<button class="tab{active}" data-key="{key}" role="tab" '
            f'aria-selected="{"true" if i == 0 else "false"}" '
            f'title="{desc}">{title}</button>'
        )
        panels.append(
            f'<div class="panel{active}" data-key="{key}">'
            f'<iframe data-key="{key}" title="{title}" loading="lazy"></iframe></div>'
        )
        # base64 里只有 [A-Za-z0-9+/=]，不会提前闭合 script 标签
        scripts.append(
            f'<script type="text/plain" id="src-{key}">{b64}</script>'
        )

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Platform · 架构总览</title>
<style>
  :root {{
    color-scheme: light dark;
    --bg: #f7f8fa;
    --fg: #101828;
    --muted: #667085;
    --card: #ffffff;
    --border: #e4e7ec;
    --accent: #0ea5a4;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg: #0b0e14;
      --fg: #e6e8ec;
      --muted: #98a2b3;
      --card: #141922;
      --border: #242b36;
    }}
  }}
  * {{ box-sizing: border-box; }}
  html, body {{ height: 100%; }}
  body {{
    margin: 0;
    background: var(--bg);
    color: var(--fg);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                 "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  }}
  /* iframe 占满整个视口 —— 里面的 viewer 按自身视口高度决定阅读宽度，
     外层每占走一条页头，图就窄一圈。所以切换器改成浮层，不参与布局。 */
  main {{ position: fixed; inset: 0; }}
  .panel {{ position: absolute; inset: 0; display: none; }}
  .panel.is-active {{ display: block; }}
  iframe {{ width: 100%; height: 100%; border: 0; display: block; background: var(--bg); }}

  .switcher {{
    position: fixed;
    bottom: 14px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 10;
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 4px;
    border-radius: 999px;
    border: 1px solid var(--border);
    background: color-mix(in srgb, var(--card) 86%, transparent);
    backdrop-filter: saturate(1.6) blur(10px);
    -webkit-backdrop-filter: saturate(1.6) blur(10px);
    box-shadow: 0 6px 22px rgba(16, 24, 40, .14);
  }}
  .brand {{
    font-size: 12px;
    font-weight: 650;
    color: var(--muted);
    padding: 0 10px 0 12px;
    white-space: nowrap;
  }}
  .brand .dot {{
    display: inline-block;
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--accent);
    margin-right: 7px;
    vertical-align: middle;
  }}
  .tabs {{ display: flex; gap: 3px; }}
  .tab {{
    appearance: none;
    border: 0;
    background: transparent;
    color: var(--muted);
    font: inherit;
    font-size: 12.5px;
    padding: 6px 15px;
    border-radius: 999px;
    cursor: pointer;
    white-space: nowrap;
    transition: background .15s, color .15s;
  }}
  .tab:hover {{ color: var(--fg); }}
  .tab.is-active {{
    background: var(--accent);
    color: #fff;
    font-weight: 600;
  }}
  @media (max-width: 560px) {{
    .brand {{ display: none; }}
  }}
</style>
</head>
<body>
<main>
  {chr(10).join("  " + p for p in panels).strip()}
</main>
<nav class="switcher" role="tablist">
  <span class="brand"><span class="dot"></span>AI Platform</span>
  <div class="tabs">
    {chr(10).join("    " + t for t in tabs).strip()}
  </div>
</nav>

{chr(10).join(scripts)}
<script>
(function () {{
  var loaded = {{}};

  function load(key) {{
    if (loaded[key]) return;
    var raw = document.getElementById('src-' + key).textContent;
    var bin = atob(raw);
    var bytes = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    var html = new TextDecoder('utf-8').decode(bytes);
    document.querySelector('iframe[data-key="' + key + '"]').srcdoc = html;
    loaded[key] = true;
  }}

  function show(key) {{
    document.querySelectorAll('.tab').forEach(function (t) {{
      var on = t.dataset.key === key;
      t.classList.toggle('is-active', on);
      t.setAttribute('aria-selected', on ? 'true' : 'false');
    }});
    document.querySelectorAll('.panel').forEach(function (p) {{
      p.classList.toggle('is-active', p.dataset.key === key);
    }});
    load(key);
    if (history.replaceState) history.replaceState(null, '', '#' + key);
  }}

  document.querySelectorAll('.tab').forEach(function (t) {{
    t.addEventListener('click', function () {{ show(t.dataset.key); }});
  }});

  var initial = (location.hash || '').replace('#', '');
  show(document.querySelector('.tab[data-key="' + initial + '"]') ? initial : '{DIAGRAMS[0][0]}');
}})();
</script>
</body>
</html>
"""
    OUT.write_text(html, encoding="utf-8")
    print(f"{OUT.name}  {OUT.stat().st_size / 1024 / 1024:.2f} MB")


if __name__ == "__main__":
    main()
