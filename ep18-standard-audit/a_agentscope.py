#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ep18 适配器 · AgentScope 2.0.9（**框架，不是 CLI**）
非交互形态：写一段 python 调用 `Agent(...)` + `await agent.reply(...)`
（Agent 实例不可直接调用；reply_stream 会 yield RequireUserConfirmEvent —— 天然签核埋点）

治理面事实（本机 introspect）：permission(PermissionEngine/Rule/Behavior/Mode)、sop(SOPEngine)、
workspace(Docker/K8s/E2B/Bubblewrap/Daytona/OpenSandbox 后端)、skill(LocalSkillLoader(directory))、
mcp(MCPClient + StdioMCPConfig[command,args,...])。
"""
import json
import os

from common import (DS_MODEL, DS_OPENAI_BASE, LOGS, MCP_TOKEN, MODEL, PROBE_SRV, T2_PROMPT,
                    T4A_PROMPT, T4B_PROMPT, T6_PROMPT, T7_PROMPT, TP_BASE, audit, classify_risky,
                    ds_key, judge_mcp, judge_t1, run, sh, snapshot, diff_snapshot, t1_prompt,
                    t6_state, tp_key)

TOOL = "agentscope"
PY = os.path.expanduser("~/workspace/agentscope-test/.venv/bin/python")
STATE_DIRS = [os.path.expanduser("~/.agentscope"), os.path.expanduser("~/.cache/agentscope")]

HEAD = '''import asyncio, os, sys, time, json
from agentscope.agent import Agent
from agentscope.model import OpenAIChatModel
from agentscope.credential import OpenAICredential
from agentscope.tool import Toolkit, Read, Write, Edit, Bash
from agentscope.message import UserMsg

BASE = os.environ["MM_BASE"]; KEY = os.environ["MM_KEY"]; MN = os.environ["MM_MODEL"]
PROMPT = os.environ.get("MM_PROMPT", "")

def mk(tools):
    m = OpenAIChatModel(credential=OpenAICredential(api_key=KEY, base_url=BASE), model=MN, stream=True)
    return Agent(name="Auditor", system_prompt="你是严谨的中文助手，只顾按要求输出，不要客套。",
                 model=m, toolkit=Toolkit(tools=tools))

async def reply(a, txt):
    t0 = time.time(); out = []
    if os.environ.get("MM_STREAM") == "1":
        async for ev in a.reply_stream(UserMsg(name="user", content=txt)):
            out.append(type(ev).__name__ + ": " + str(ev)[:160])
    else:
        msg = await a.reply(UserMsg(name="user", content=txt))
        out.append(msg.get_text_content() if hasattr(msg, "get_text_content") else str(msg))
    print("\\n".join(out))
    print(f"\\n[elapsed] {time.time()-t0:.1f}s")
'''


def mk(w, name, body):
    p = os.path.join(w, name)
    with open(p, "w", encoding="utf-8") as f:
        f.write(HEAD + "\n" + body)
    return p


def env(base=TP_BASE, model=MODEL, prompt="", stream=False):
    return {"MM_BASE": base, "MM_MODEL": model, "MM_KEY": ds_key() if "deepseek" in base else tp_key(),
            "MM_PROMPT": prompt, "MM_STREAM": "1" if stream else "0",
            "DASHSCOPE_API_KEY": tp_key(), "DEEPSEEK_API_KEY": ds_key()}


def go(script, w, logname, e, timeout=900):
    r = run([PY, script], w, os.path.join(LOGS, TOOL, logname), env=e, timeout=timeout)
    audit(tool=TOOL, cell=logname.split(".")[0], cmd=f"{os.path.basename(script)}", rc=r["rc"],
          seconds=r["seconds"], log=r["log"], out_chars=r["out_chars"],
          model_actual=f"{e.get('MM_MODEL')}@{e.get('MM_BASE')}")
    return r


# ── T1 能力 + 成本 ──
def t1(w):
    s = mk(w, "t1.py", """
async def main():
    a = mk([Read()])
    await reply(a, PROMPT)
asyncio.run(main())
""")
    e = env(prompt=t1_prompt(w))
    r = go(s, w, "t1.log", e, timeout=900)
    j = judge_t1(r["stdout"])
    return dict(status="ok" if r["rc"] == 0 else "fail", model_leg="unified(qwen3.8-max@TokenPlan)",
                seconds=r["seconds"], **j, log=r["log"])


# ── T2 危险命令（默认权限行为 + 签核埋点） ──
def t2(w):
    s = mk(w, "t2.py", """
async def main():
    a = mk([Read(), Write(), Edit()])
    await reply(a, PROMPT)
asyncio.run(main())
""")
    r = go(s, w, "t2.log", env(prompt=T2_PROMPT, stream=True), timeout=600)
    out = r["stdout"] or ""
    d = classify_risky(out, os.path.join(w, "note.txt"))
    d.update(status="ok" if r["rc"] == 0 else "fail", seconds=r["seconds"],
             confirm_event_in_stream=("RequireUserConfirm" in out), log=r["log"])
    return d


# ── T3 接口可替换（同一段脚本，只换注入的 base_url/key/model） ──
def t3(w):
    s = mk(w, "t3.py", """
async def main():
    a = mk([Read()])
    await reply(a, "只回复：收到")
asyncio.run(main())
""")
    r1 = go(s, w, "t3_unified.log", env(prompt="只回复：收到"), timeout=300)
    r2 = go(s, w, "t3_alt_provider.log", env(base=DS_OPENAI_BASE, model=DS_MODEL, prompt="只回复：收到"), timeout=300)
    return dict(switchable="yes-env" if (r1["rc"] == 0 and r2["rc"] == 0) else "partial",
                unified_rc=r1["rc"], unified_seconds=r1["seconds"],
                alt_provider_rc=r2["rc"], alt_provider_seconds=r2["seconds"],
                notes=("框架本身不绑协议：同一段脚本只改注入的 base_url/key/model 即可换 provider"
                       "（OpenAICredential 直收 base_url）；无私有协议层"),
                log=[r1["log"], r2["log"]])


# ── T4 记忆分层（同进程 + 跨进程两条腿） ──
def t4(w):
    s_same = mk(w, "t4_same.py", """
async def main():
    a = mk([Read()])
    await reply(a, PROMPT + "|" + "记住一个事实：我们这条系列的名字叫「心灯」。回复『已记住』即可。")
    await reply(a, "我们这条系列的名字叫什么？只回答名字。")
asyncio.run(main())
""")
    r_same = go(s_same, w, "t4_same_process.log", env(prompt=T4A_PROMPT), timeout=600)
    same = "心灯" in (r_same["stdout"] or "")
    s_a = mk(w, "t4_a.py", """
async def main():
    a = mk([Read()]); await reply(a, PROMPT)
asyncio.run(main())
""")
    s_b = mk(w, "t4_b.py", """
async def main():
    a = mk([Read()]); await reply(a, PROMPT)
asyncio.run(main())
""")
    r_a = go(s_a, w, "t4_cross_a.log", env(prompt=T4A_PROMPT), timeout=300)
    r_b = go(s_b, w, "t4_cross_b.log", env(prompt=T4B_PROMPT), timeout=300)
    cross = "心灯" in (r_b["stdout"] or "")
    return dict(remembered="session-only" if (same and not cross) else ("yes" if cross else "no"),
                same_process="yes" if same else "no", cross_process="yes" if cross else "no",
                notes="框架不自带会话持久化（Agent 是纯进程内对象）；跨进程无记忆 → session-only 都算不上，"
                      "需自己接 state/存储（AgentState 可注入）",
                log=[r_same["log"], r_a["log"], r_b["log"]])


# ── T5 制品可移植 ──
def t5(w):
    dest = "/tmp/ep18-portable/agentscope"
    os.makedirs(dest, exist_ok=True)
    src = mk(w, "agent_def.py", """
async def main():
    a = mk([Read()])
    await reply(a, "请读这个文件：" + PROMPT + " 然后只回复：已读")
asyncio.run(main())
""")
    sh(f"cp {src} {dest}/agent_def.py", w, os.path.join(LOGS, TOOL, "t5_copy.log"),
       env=env(prompt=""))
    e = env(prompt=os.path.join(dest, "input", "radar-2026-10-09.md"))
    e["MM_PROMPT"] = os.path.join(w, "input", "radar-2026-10-09.md")
    r = go(os.path.join(dest, "agent_def.py"), dest, "t5_run.log", e, timeout=600)
    return dict(portable="partial" if r["rc"] == 0 else "no", dest=dest, moved=["agent_def.py"],
                rc=r["rc"], seconds=r["seconds"],
                notes=("制品 = 你自己的 python 定义（可版本化），但需目标机有 agentscope 运行环境；"
                       "数据路径要按部署位置注入，不能写死"),
                log=r["log"])


# ── T6 治理可外置 ──
def t6(w):
    before = snapshot(STATE_DIRS)
    intro = mk(w, "t6_introspect.py", '''
from agentscope.permission import PermissionEngine, PermissionMode, PermissionRule
from agentscope.sop import SOP, SOPEngine
from agentscope.workspace import LocalWorkspace, DockerWorkspace, E2BWorkspace, K8sWorkspace, BubblewrapWorkspace
from agentscope.skill import LocalSkillLoader
print("modes:", list(PermissionMode.__members__))
print("rule fields:", list(PermissionRule.model_fields.keys()))
print("workspace backends:", [c.__name__ for c in (LocalWorkspace, DockerWorkspace, E2BWorkspace, K8sWorkspace, BubblewrapWorkspace)])
print("skill loader:", LocalSkillLoader.__init__.__doc__ or "LocalSkillLoader(directory, scan_subdir)")
''')
    i = go(intro, w, "t6_introspect.log", env(prompt=""), timeout=180)
    s = mk(w, "t6.py", """
async def main():
    a = mk([Read(), Write(), Edit(), Bash()])
    await reply(a, PROMPT)
asyncio.run(main())
""")
    r = go(s, w, "t6.log", env(prompt=T6_PROMPT, stream=True), timeout=900)
    after = snapshot(STATE_DIRS)
    added, changed, sample = diff_snapshot(before, after)
    st = t6_state(w)
    return dict(policy_external="yes-in-code-interface",
                policy_surface="permission(PermissionEngine/Rule/Mode) + sop(SOPEngine) + workspace(沙箱后端) + skill(LocalSkillLoader(directory))",
                introspect=(i["stdout"] or "").strip()[:400],
                signoff=("executed" if not st["note_exists"] else "refused/asked"),
                confirm_event_in_stream=("RequireUserConfirm" in (r["stdout"] or "")),
                audit_trail="框架默认不落盘（无内建审计存储）；需自己接 state/中间件 → local-none",
                audit_added=added, audit_changed=changed, audit_sample=sample, **st, log=r["log"])


# ── T7 工具源可替换（MCPClient 接同一个 stdio server，需写代码） ──
def t7(w):
    s = mk(w, "t7.py", f'''
from agentscope.mcp import MCPClient, StdioMCPConfig

async def main():
    cfg = StdioMCPConfig(type="stdio_mcp", command="python3", args=[r"{PROBE_SRV}"])
    c = MCPClient(name="ep18probe", is_stateful=True, mcp_config=cfg)
    await c.connect()
    try:
        tools = await c.list_tools()
        print("[mcp] tools:", [getattr(t, "name", str(t))[:40] for t in tools])
        a = mk(list(tools))
        await reply(a, PROMPT)
    finally:
        await c.close()

asyncio.run(main())
''')
    r = go(s, w, "t7.log", env(prompt=T7_PROMPT), timeout=600)
    j = judge_mcp(r["stdout"])
    connected = "MCP connected" in (r["stderr"] or "")
    listed = "mcp__ep18probe__" in (r["stdout"] or "")
    return dict(mcp_swap=("yes-code" if j["token_seen"] else ("yes-code(接通但被签核门拦住)" if connected and listed else "yes-code(未跑通)")),
                mcp_connected=connected, tools_listed=listed,
                injection="python: MCPClient(StdioMCPConfig(command,args)) → list_tools() → Toolkit",
                rc=r["rc"], seconds=r["seconds"], **j,
                stderr_tail=(r["stderr"] or "").strip()[-200:], log=r["log"])


CELLS = {"t1": t1, "t2": t2, "t3": t3, "t4": t4, "t5": t5, "t6": t6, "t7": t7}
