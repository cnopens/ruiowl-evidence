#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ep18 适配器 · Claude Code 2.1.273
非交互入口：claude -p "<prompt>" --output-format text

接入配方沿用 ep14 已验证做法：**临时 --settings 文件**注入 ANTHROPIC_*（键值不落盘、用完即删），
不改 ~/.claude/settings.json（避免污染日常 MiniMax 路由）。

⚠️ 统一条件例外（如实标注）：Claude Code 只吃 Anthropic 协议，TokenPlan 是 OpenAI 兼容域 →
统一模型不可达（这本身就是 T3 的一手证据）。各格跑在「DeepSeek Anthropic 兼容域」并标注 model_actual。
"""
import json
import os
import tempfile

from common import (DS_ANTHROPIC_BASE, DS_MODEL, LOGS, MCP_TOKEN, MODEL, PROBE_SRV, T2_PROMPT,
                    T4A_PROMPT, T4B_PROMPT, T6_PROMPT, T7_PROMPT, TP_BASE, audit, classify_risky,
                    ds_key, judge_mcp, judge_t1, run, sh, snapshot, diff_snapshot, t1_prompt,
                    t6_state, tp_key)

TOOL = "claude"
STATE_DIRS = [os.path.expanduser("~/.claude/projects"), os.path.expanduser("~/.claude/settings.json")]
MODEL_ACTUAL = f"{DS_MODEL} @ api.deepseek.com/anthropic（统一模型不可达，见 t3）"
TP_ANTHROPIC = TP_BASE.replace("/compatible-mode/v1", "")
LEGS = {
    "unified": (TP_ANTHROPIC, MODEL, tp_key),
    "work": (DS_ANTHROPIC_BASE, DS_MODEL, ds_key),
}


def settings_for(leg):
    base, model, keyf = LEGS[leg]
    s = {"env": {"ANTHROPIC_BASE_URL": base, "ANTHROPIC_AUTH_TOKEN": keyf(), "ANTHROPIC_MODEL": model,
                 "ANTHROPIC_DEFAULT_OPUS_MODEL": model, "ANTHROPIC_DEFAULT_SONNET_MODEL": model,
                 "ANTHROPIC_DEFAULT_HAIKU_MODEL": model, "CLAUDE_CODE_SUBAGENT_MODEL": model}}
    p = tempfile.mkstemp(prefix="claude-ep18-", suffix=".json")[1]
    with open(p, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False)
    os.chmod(p, 0o600)
    return p


def go(w, prompt, logname, leg="work", extra=None, timeout=900):
    sp = settings_for(leg)
    try:
        cmd = ["claude", "-p", prompt, "--output-format", "text", "--settings", sp] + (extra or [])
        r = run(cmd, w, os.path.join(LOGS, TOOL, logname), env={}, timeout=timeout)
    finally:
        try:
            os.unlink(sp)
        except OSError:
            pass
    audit(tool=TOOL, cell=logname.split(".")[0], cmd=f"claude -p … --settings <tmp> [{leg}]",
          rc=r["rc"], seconds=r["seconds"], log=r["log"], out_chars=r["out_chars"],
          model_actual=(MODEL_ACTUAL if leg == "work" else f"{MODEL}@TokenPlan(anthropic-shape)"))
    return r


# ── T1 能力 + 成本 ──
def t1(w):
    ru = go(w, "只回复：收到", "t1_unified_attempt.log", leg="unified", timeout=180)
    r = go(w, t1_prompt(w), "t1.log", leg="work", timeout=900)
    j = judge_t1(r["stdout"])
    return dict(status="ok" if r["rc"] == 0 else "fail", model_leg="anthropic-compat-substitute",
                model_actual=MODEL_ACTUAL,
                unified_attempt=dict(rc=ru["rc"], out_tail=(ru["stdout"] or "").strip()[-160:],
                                     err_tail=(ru["stderr"] or "").strip()[-160:]),
                seconds=r["seconds"], **j, log=r["log"])


# ── T2 危险命令（默认权限面，不加 --dangerously-skip-permissions） ──
def t2(w):
    r = go(w, T2_PROMPT, "t2.log", leg="work", timeout=600)
    return dict(status="ok" if r["rc"] == 0 else "fail", seconds=r["seconds"],
                out_tail=(r["stdout"] or "").strip()[-200:],
                **classify_risky(r["stdout"], os.path.join(w, "note.txt")), log=r["log"])


# ── T3 接口可替换（本期核心） ──
def t3(w):
    ru = go(w, "只回复：收到", "t3_unified.log", leg="unified", timeout=180)
    ok = go(w, "只回复：收到", "t3_anthropic_compat.log", leg="work", timeout=300)
    return dict(switchable="needs-proxy",
                unified_attempt=dict(rc=ru["rc"], out_tail=(ru["stdout"] or "").strip()[-200:],
                                     err_tail=(ru["stderr"] or "").strip()[-150:]),
                anthropic_compat=dict(rc=ok["rc"], seconds=ok["seconds"],
                                      out_tail=(ok["stdout"] or "").strip()[-80:]),
                notes=("只吃 Anthropic 协议：TokenPlan（OpenAI 兼容）直指必失败；"
                       "换成『Anthropic 兼容域』+ 临时 --settings 注入即可通 → 门槛 = 需协议转换层"),
                log=[ru["log"], ok["log"]])


# ── T4 记忆分层 ──
def t4(w):
    rA = go(w, T4A_PROMPT, "t4_a.log", leg="work", timeout=300)
    rB = go(w, T4B_PROMPT, "t4_b.log", leg="work", timeout=300)
    rC = go(w, T4B_PROMPT, "t4_c_continue.log", leg="work", extra=["--continue"], timeout=300)
    plain = "心灯" in (rB["stdout"] or "")
    withc = "心灯" in (rC["stdout"] or "")
    return dict(remembered="session-only" if (withc and not plain) else ("yes" if withc else "no"),
                new_process_plain="yes" if plain else "no",
                new_process_continue="yes" if withc else "no",
                answer_plain=(rB["stdout"] or "").strip()[:60],
                answer_continue=(rC["stdout"] or "").strip()[:60],
                notes=("实测两条腿都答出『心灯』→ **跨进程确实记得**。载体是 agent 自己写的项目级记忆文件："
                       "~/.claude/projects/<项目slug>/memory/{MEMORY.md,series-name-xindeng.md}，新进程重新加载"),
                memory_files=["~/.claude/projects/<slug>/memory/MEMORY.md",
                              "~/.claude/projects/<slug>/memory/series-name-xindeng.md"],
                log=[rA["log"], rB["log"], rC["log"]])


# ── T5 制品可移植（CLAUDE.md + skills 搬目录） ──
def t5(w):
    dest = "/tmp/ep18-portable/claude"
    os.makedirs(dest, exist_ok=True)
    moved = []
    for src, name in [(os.path.expanduser("~/.claude/CLAUDE.md"), "CLAUDE.md"),
                      (os.path.expanduser("~/.claude/skills"), "skills")]:
        if os.path.exists(src):
            sh(f"rm -rf {dest}/{name} && cp -R {src} {dest}/{name}", w,
               os.path.join(LOGS, TOOL, "t5_copy.log"), env={})
            moved.append(name)
    r = go(dest, "只回复：收到", "t5_run.log", leg="work", timeout=300)
    return dict(portable="partial" if moved else "no", moved=moved, dest=dest, rc=r["rc"],
                notes="CLAUDE.md/skills 是文件级可搬运；会话历史与权限面留在 ~/.claude 用户目录（换机=另起一套本地状态）",
                log=r["log"])


# ── T6 治理可外置 ──
def t6(w):
    before = snapshot(STATE_DIRS)
    r = go(w, T6_PROMPT, "t6.log", leg="work", timeout=600)
    after = snapshot(STATE_DIRS)
    added, changed, sample = diff_snapshot(before, after)
    st = t6_state(w)
    settings = os.path.expanduser("~/.claude/settings.json")
    has_perm, hooks = False, False
    if os.path.exists(settings):
        try:
            d = json.load(open(settings, encoding="utf-8"))
            has_perm, hooks = ("permissions" in d), ("hooks" in d)
        except Exception:
            pass
    return dict(policy_external="file-external",
                policy_surface=f"~/.claude/settings.json（permissions={has_perm} / hooks={hooks}）+ --settings 注入 + --add-dir/--strict-mcp-config",
                signoff=("executed" if not st["note_exists"] else "refused/asked"),
                out_tail=(r["stdout"] or "").strip()[-200:],
                audit_trail="local-jsonl（~/.claude/projects/**/*.jsonl 会话转写）",
                audit_added=added, audit_changed=changed, audit_sample=sample, **st, log=r["log"])


# ── T7 工具源可替换（--mcp-config 喂同一个 MCP server） ──
def t7(w):
    cfg = os.path.join(w, "mcp.json")
    with open(cfg, "w", encoding="utf-8") as f:
        json.dump({"mcpServers": {"ep18probe": {"command": "python3", "args": [PROBE_SRV]}}}, f)
    r = go(w, T7_PROMPT, "t7.log", leg="work",
           extra=["--mcp-config", cfg, "--strict-mcp-config", "--dangerously-skip-permissions"], timeout=600)
    j = judge_mcp(r["stdout"])
    return dict(mcp_swap="yes-config", config_file=cfg, rc=r["rc"], seconds=r["seconds"], **j,
                out_tail=(r["stdout"] or "").strip()[-200:], log=r["log"])


CELLS = {"t1": t1, "t2": t2, "t3": t3, "t4": t4, "t5": t5, "t6": t6, "t7": t7}
