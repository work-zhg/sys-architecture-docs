#!/usr/bin/env python3
"""生成「概览」页 —— 合并文档的第一个 tab。

★ 内容源是 atlas 仓库的 doc/ 目录（AI Platform 概要设计 01–12）。
  doc/ 是 AI Platform 的设计，atlas 是它 native 侧的落地载体，两者不是一回事。

★ 受众是**对外介绍**（5–10 分钟讲完），所以只留「是什么 / 凭什么这么设计 /
  取舍在哪」。实施细节一律不进这一页 —— 能力矩阵全表、loadSession 验证项、
  12 篇文档索引、seq 与 run_id 的技术说明，都属于内部评审材料。

用法：python3 build-overview.py
"""

from __future__ import annotations

import base64
import pathlib

HERE = pathlib.Path(__file__).parent
OUT = HERE / "atlas-overview.html"


def img(path: str) -> str:
    data = base64.b64encode(pathlib.Path(path).read_bytes()).decode("ascii")
    return f"data:image/png;base64,{data}"


# 两类 Agent 的对照（doc/native.html §01）
# ★ 早先文档把 native 简称「顾问」，暗示它只出谋划策 —— 加上 sandbox 与
#   subagent 之后该称呼已被作废：native 能写文件、跑命令、委派任务，
#   能力不比 acp 少。区别是编排权在谁手里。
ROLES = [
    ("编排", "我们写的图，工具与流程自己装配", "成品 CLI 内部，我们不介入"),
    ("提示词", "完全由我们控制", "CLI 自带，我们只能附加"),
    ("工具集", "完全由我们装配", "CLI 自带 + MCP"),
    ("执行环境", "会话级 Sandbox Pod", "会话级 CLI Pod"),
    ("上下文", "服务端的消息账本，每轮重建", "CLI 进程内"),
    ("重新生成", "可以，但环境已被上一轮改过", "不支持"),
]

CHOOSE = [
    ("cyan", "要精细控制行为，选 native",
     "提示词、工具集、中间件、记忆注入、委派策略都在我们手里，能针对场景调优。"),
    ("amber", "要立刻拿到成熟编码能力，选 acp",
     "Claude Code 这类成品 CLI 在代码理解与多步编辑上的积累，短期内自己写是追不上的。"),
]

THREADS = [
    ("cyan", "编排权", "两类 Agent 的区别不在能力多少。",
     "native 的流程是我们写的图，提示词与工具集自己装配；acp 是成品 CLI，我们不介入它内部。"
     "<b>能力两边相当，差别在编排权归谁</b> —— 这条分界线推导出后面所有的不对称。"),
    ("emerald", "单一真相源", "对话内容是唯一真相，过程流只是它怎么产生的。",
     "不保留第二份会话状态，也就没有两份数据对不上的问题 —— 那类问题出错时是"
     "<b>静默降级</b>，最难排查。代价很明确：一轮跑到一半中断，只能整轮重来。"),
    ("violet", "能力显式化", "差异不可抹平，只能显式暴露。",
     "每个智能体自带一份能力声明，界面按它决定哪些按钮可用。"
     "用户看到的不是「这个功能坏了」，而是<b>「这类智能体本来就没有这个能力」</b>。"),
]

# doc/session.html §02
OBJECTS = [
    ("Agent", "智能体定义。分 <b>native</b>（我们编排）与 <b>acp</b>（驱动成品 CLI）两型，自带能力声明"),
    ("Session", "一个会话。引用一个 Agent 版本，持有工作区与配置"),
    ("Run", "会话里的一条对话：一次提交 → 干完活 → 停下来。会话内串行"),
    ("Message", "会话内容账本，<b>展示的唯一真相</b>，永久保留"),
    ("Event", "过程流：增量文本、思考、工具中间态、审批请求"),
]

# doc/architecture.html §09 + native.html §03
DECISIONS = [
    ("native / acp 两型并存", "精细控制与成熟能力都能要，还能组合",
     "两类的界面语义不完全一致"),
    ("不保留第二份会话状态", "单一真相源，没有双源对齐问题", "一轮中断后整轮重来"),
    ("每个会话一个 Pod，而非每轮一个", "工作区跨轮连续，多步任务做得下去",
     "环境有状态，重新生成不等于重来一次"),
    ("出站流量统一经网关", "鉴权、限流、成本、审计只实现一次",
     "出站单点，可用性要求被拉高"),
]


def main() -> None:
    roles = "\n".join(
        f"<tr><td>{k}</td><td>{a}</td><td>{b}</td></tr>" for k, a, b in ROLES
    )
    threads = "\n".join(
        f'<article class="tl tl-{c}"><h3>{t}</h3>'
        f'<p class="tl-lede">{lede}</p><p>{body}</p></article>'
        for c, t, lede, body in THREADS
    )
    objs = "\n".join(
        f"<tr><td><code>{n}</code></td><td>{d}</td></tr>" for n, d in OBJECTS
    )
    choose = "\n".join(
        f'<article class="tl tl-{c}"><p class="tl-lede">{t}</p><p>{d}</p></article>'
        for c, t, d in CHOOSE
    )
    decisions = "\n".join(
        f"<tr><td><b>{d}</b></td><td>{g}</td><td>{c}</td></tr>" for d, g, c in DECISIONS
    )

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Platform 概览</title>
<style>
  :root {{
    color-scheme: light dark;
    --bg:#f7f8fa; --fg:#101828; --muted:#667085; --card:#fff;
    --border:#e4e7ec; --accent:#0d9488; --code-bg:#f2f4f7;
    --cyan:#06b6d4; --emerald:#10b981; --violet:#8b5cf6; --amber:#f59e0b;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg:#0b0e14; --fg:#e6e8ec; --muted:#98a2b3; --card:#141922;
      --border:#242b36; --accent:#2dd4bf; --code-bg:#1b212b;
    }}
  }}
  * {{ box-sizing:border-box; }}
  body {{
    margin:0; background:var(--bg); color:var(--fg);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",
                "Hiragino Sans GB","Microsoft YaHei",sans-serif;
    font-size:14px; line-height:1.68; -webkit-font-smoothing:antialiased;
  }}
  .wrap {{ max-width:1080px; margin:0 auto; padding:38px 28px 96px; }}
  code {{
    font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
    font-size:.87em; background:var(--code-bg);
    padding:1.5px 5px; border-radius:4px;
  }}
  h1 {{ font-size:26px; font-weight:680; margin:0 0 8px; letter-spacing:.01em; }}
  h1 .dot {{
    display:inline-block; width:9px; height:9px; border-radius:50%;
    background:var(--accent); margin-right:11px; vertical-align:middle;
  }}
  .lede {{ font-size:15.5px; color:var(--muted); margin:0 0 30px; max-width:880px; }}
  .lede b {{ color:var(--fg); font-weight:600; }}
  h2 {{
    font-size:12px; font-weight:680; text-transform:uppercase; letter-spacing:.11em;
    color:var(--muted); margin:48px 0 16px;
    padding-bottom:9px; border-bottom:1px solid var(--border);
  }}
  figure {{ margin:0; }}
  figure img {{
    width:100%; display:block; border-radius:10px;
    border:1px solid var(--border); background:var(--card);
  }}
  figcaption {{ font-size:12.8px; color:var(--muted); margin-top:11px; }}
  figcaption b {{ color:var(--fg); font-weight:600; }}

  .hero {{
    background:var(--card); border:1px solid var(--border);
    border-left:3px solid var(--accent); border-radius:11px;
    padding:20px 23px; margin-top:28px;
  }}
  .hero h3 {{ margin:0 0 7px; font-size:15.5px; font-weight:660; }}
  .hero p {{ margin:0; font-size:13.8px; color:var(--muted); }}
  .hero b {{ color:var(--fg); font-weight:600; }}

  table {{ width:100%; border-collapse:collapse; font-size:13.2px; }}
  th {{
    text-align:left; font-weight:620; color:var(--muted);
    font-size:11.5px; text-transform:uppercase; letter-spacing:.07em;
    padding:0 13px 9px; border-bottom:1px solid var(--border);
  }}
  td {{ padding:10px 13px; border-bottom:1px solid var(--border); vertical-align:top; }}
  tr:last-child td {{ border-bottom:0; }}
  td:first-child {{ white-space:nowrap; width:1%; color:var(--muted); }}
  .roles td:nth-child(2), .roles td:nth-child(3) {{ width:42%; color:var(--fg); }}
  .roles th:nth-child(2) {{ color:var(--cyan); }}
  .roles th:nth-child(3) {{ color:var(--amber); }}
  .objs td:last-child {{ color:var(--fg); }}
  .dec td:first-child {{ color:var(--fg); width:26%; white-space:normal; }}

  .tls {{ display:grid; gap:12px; }}
  .tl {{
    background:var(--card); border:1px solid var(--border);
    border-left-width:3px; border-radius:10px; padding:17px 20px;
  }}
  .tl-cyan {{ border-left-color:var(--cyan); }}
  .tl-emerald {{ border-left-color:var(--emerald); }}
  .tl-violet {{ border-left-color:var(--violet); }}
  .tl h3 {{
    margin:0 0 5px; font-size:11.5px; font-weight:680;
    text-transform:uppercase; letter-spacing:.09em; color:var(--muted);
  }}
  .tl-lede {{ margin:0 0 7px; font-size:14px; font-weight:620; }}
  .tl p:last-child {{ margin:0; font-size:13px; color:var(--muted); }}
  .tl b {{ color:var(--fg); font-weight:600; }}

  .note {{
    margin-top:15px; font-size:12.8px; color:var(--muted);
    border-left:2px solid var(--border); padding-left:14px;
  }}
  .note b {{ color:var(--fg); font-weight:600; }}
</style>
</head>
<body>
<div class="wrap">

  <h1><span class="dot"></span>AI Platform</h1>
  <p class="lede">
    一套服务端抽象同时承载两类 Agent：<b>native</b> 的流程由我们编排 —— 提示词、工具集、
    委派策略都在手里；<b>acp</b> 直接驱动成品 CLI，拿它在代码上的全部积累。
    两类都能写文件、跑命令、委派子任务，<b>差别在编排权归谁</b>。
    执行环境可以是 Kubernetes Pod，也可以是用户自己的电脑。
    前端只面对一套对象模型和一套事件流。
  </p>

  <figure>
    <img src="{img('/tmp/aip-prototype.png')}" alt="会话页">
    <figcaption>
      会话页。右栏上方是这个智能体的<b>能力清单</b> —— 灰色的「重新生成 / 编辑历史 /
      分支」对 <code>acp</code> 不成立，绿色的「Run 内审批 / 会话恢复」才可用。
      中间是一次写文件前的确认：<b>任务停在这里等人点头，而不是先做了再说</b>。
    </figcaption>
  </figure>

  <div class="hero">
    <h3>整套设计的那条分界线：编排权在谁手里</h3>
    <p>
      两类 Agent 的区别<b>不在能力多少</b> —— 两边都能写文件、跑命令、委派子任务。
      区别在于 <code>native</code> 的流程是我们写的图，提示词与工具集自己装配；
      <code>acp</code> 是成品 CLI，我们不介入它内部。上下文归属、能不能重跑、
      审批怎么走，每一处不对称都从这一条推导出来。
    </p>
  </div>

  <h2>两类 Agent</h2>
  <table class="roles">
    <thead><tr><th></th><th>native</th><th>acp</th></tr></thead>
    <tbody>
{roles}
    </tbody>
  </table>
  <p class="note">
    <code>native</code> 的 agent 逻辑跑在服务端，Pod 只是它的执行环境；
    <code>acp</code> 的 Pod 里跑的是完整的 agent。两者的工作区都<b>按会话持久</b>，
    上一轮建的文件下一轮还在 —— 所以「重新生成」不是重来一次，而是在已被改过的环境上再跑一次。
    这一点在界面上如实说明，<b>比悄悄关掉这个能力、或者不说就让它跑，都更好</b>。
  </p>

  <h2>怎么选</h2>
  <div class="tls">
{choose}
  </div>
  <div class="hero">
    <h3>最有价值的是把两者组合起来</h3>
    <p>
      <code>native</code> 做业务编排，把重型编码任务作为子任务委派给 <code>acp</code> ——
      业务逻辑由我们精细控制，编码能力直接用成品 CLI 的。
      委派是父任务里的一次工具调用，<b>只有结论回到对话，中间过程不污染上下文</b>。
    </p>
  </div>

  <h2>三条主线</h2>
  <div class="tls">
{threads}
  </div>

  <h2>一套对象模型</h2>
  <p class="note" style="margin:0 0 16px; border:0; padding:0;">
    两类 Agent 性质完全不同，但对外是同一套对象、同一套事件流。
    前端不需要知道对面是哪一型。
  </p>
  <table class="objs">
    <tbody>
{objs}
    </tbody>
  </table>
  <p class="note">
    核心分层：<b>Message 是「会话内容」，Event 是「它怎么产生的」</b>。
    一轮结束后前者即为真相，后者可以丢弃。
  </p>

  <h2>关键取舍</h2>
  <table class="dec">
    <thead><tr><th>决策</th><th>买到了</th><th>代价</th></tr></thead>
    <tbody>
{decisions}
    </tbody>
  </table>

  <h2>本期边界</h2>
  <p class="note" style="border:0; padding:0; margin:0;">
    <b>不做会话在两型之间的任务移交</b> —— 一个会话只绑定一个智能体。
    需要换一型时由用户手工发起新会话。注意这与上面的<b>委派</b>不同：
    委派是一次调用、一个结论、不改变会话归属，所以可以做；
    移交要改变会话的归属，需要先有真实用例才能定得对，过早设计只会得到一个没人用的抽象。
  </p>

</div>
</body>
</html>
"""
    OUT.write_text(html, encoding="utf-8")
    print(f"{OUT.name}  {OUT.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
