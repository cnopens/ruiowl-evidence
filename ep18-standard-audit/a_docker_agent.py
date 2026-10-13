#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ep18 适配器 · docker-agent 1.149.0（Docker AI Agent Runner）
非交互入口：docker-agent run <agent.yaml> [message] --exec
标准面：YAML 声明（版本化）+ OCI 分发 + toolsets(MCP) + --safety 权限档 + hooks（外部审计钩子）+ session-db。
"""
import json
import os

from common import (CS, DS_MODEL, DS_OPENAI_BASE, LOGS, MCP_TOKEN, MODEL, PROBE_SRV, T2_PROMPT,
                    T4A_PROMPT, T4B_PROMPT, T6_PROMPT, T7_PROMPT, TP_BASE, audit, classify_risky,
                    ds_key, judge_mcp, judge_t1, run, sh, snapshot, diff_snapshot, t1_prompt,
                    t6_state, tp_key)

TOOL = "docker-agent"
STATE_DIRS = [os.path.expanduser("~/.cagent"), os.path.expanduser("~/.config/cagent")]
SESSION_DB = os.path.join(os.path.expanduser("~/.cagent"), "session.db")


def env_all(alt=False):
    return {"OPENAI_BASE_URL": DS_OPENAI_BASE if alt else TP_BASE,
            "OPENAI_API_KEY": ds_key() if alt else tp_key(),
            "TELEMETRY_ENABLED": "false"}


SYS_PROMPT = "你是严谨的中文助手，只按要求输出，不要客套。"


def yaml_for(w, model=MODEL, toolsets=None):
    """指令固定为系统提示；**任务文本走 run 的 message 参数**（docker-agent 无 message 会报错）。"""
    p = os.path.join(w, "agent.yaml")
    body = ["agents:", "  auditor:", f"    model: openai/{model}", "    instruction: |",
            "      " + SYS_PROMPT]
    if toolsets:
        body.append("    toolsets:")
        for t in toolsets:
            body.append("      - type: mcp")
            body.append(f"        command: {t['command']}")
            body.append("        args:")
            for a in t["args"]:
                body.append(f"          - {a}")
    with open(p, "w", encoding="utf-8") as f:
        f.write("\n".join(body) + "\n")
    return p


def go(w, instruction, logname, model=MODEL, alt=False, extra=None, toolsets=None, timeout=900):
    y = yaml_for(w, model=model, toolsets=toolsets)
    cmd = ["docker-agent", "run", y, instruction, "--exec"] + (extra or [])
    r = run(cmd, w, os.path.join(LOGS, TOOL, logname), env=env_all(alt), timeout=timeout)
    audit(tool=TOOL, cell=logname.split(".")[0], cmd=" ".join(cmd), rc=r["rc"], seconds=r["seconds"],
          log=r["log"], out_chars=r["out_chars"], model_actual=f"{model}@{'deepseek' if alt else 'tokenplan'}")
    return r


# ── T1 能力 + 成本 ──
def t1(w):
    r = go(w, t1_prompt(w), "t1.log")
    j = judge_t1(r["stdout"])
    return dict(status="ok" if r["rc"] == 0 else "fail", model_leg="unified(qwen3.8-max@TokenPlan)",
                seconds=r["seconds"],
                stderr_tail=(r["stderr"] or "").strip()[-300:], **j, log=r["log"])


# ── T2 危险命令（默认 safety 档，不加 --yolo/--safety） ──
def t2(w):
    r = go(w, T2_PROMPT, "t2.log", timeout=600)
    return dict(status="ok" if r["rc"] == 0 else "fail", seconds=r["seconds"],
                stderr_tail=(r["stderr"] or "").strip()[-200:], default_safety="(未指定，用官方默认)",
                **classify_risky(r["stdout"], os.path.join(w, "note.txt")), log=r["log"])


# ── T3 接口可替换 ──
def t3(w):
    r1 = go(w, "只回复：收到", "t3_unified.log", timeout=300)
    r2 = go(w, "只回复：收到", "t3_alt_provider.log", model=DS_MODEL, alt=True, timeout=300)
    out = sh("docker-agent run --help 2>&1 | grep -cE '\\-\\-model|\\-\\-safety'", w,
             os.path.join(LOGS, TOOL, "t3_surface.log"), env=env_all())
    return dict(switchable="yes-config" if (r1["rc"] == 0 and r2["rc"] == 0) else "partial",
                unified_rc=r1["rc"], unified_seconds=r1["seconds"],
                alt_provider_rc=r2["rc"], alt_provider_seconds=r2["seconds"],
                notes=("provider 走 YAML model 字段或 --model [agent=]provider/model；换 OpenAI 兼容域只改配置/环境变量"),
                surface_flags=int(out["stdout"].strip() or 0), log=[r1["log"], r2["log"]])


# ── T4 记忆分层（session-db 续会话） ──
def t4(w):
    rA = go(w, T4A_PROMPT, "t4_a.log", extra=["--session", "ep18t4"], timeout=300)
    rB = go(w, T4B_PROMPT, "t4_b.log", extra=["--session", "ep18t4"], timeout=300)
    hit = "心灯" in (rB["stdout"] or "")
    return dict(remembered="yes" if hit else "no", session_id="ep18t4",
                session_db_exists=os.path.exists(SESSION_DB), leg_a_rc=rA["rc"], leg_b_rc=rB["rc"],
                answer=(rB["stdout"] or "").strip()[-120:],
                notes="--session <id> 复用同一会话（本地 session.db）→ 跨进程可续",
                log=[rA["log"], rB["log"]])


# ── T5 制品可移植（单个 agent.yaml 搬走） ──
def t5(w):
    dest = "/tmp/ep18-portable/docker-agent"
    os.makedirs(dest, exist_ok=True)
    sh(f"cp {os.path.join(w, 'agent.yaml')} {dest}/agent.yaml", w,
       os.path.join(LOGS, TOOL, "t5_copy.log"), env=env_all())
    r = go(dest, "只回复：收到", "t5_run.log", timeout=300)
    return dict(portable="yes" if r["rc"] == 0 else "partial", dest=dest, moved=["agent.yaml"],
                rc=r["rc"], seconds=r["seconds"],
                notes="单文件 YAML 声明；另有 OCI 分发能力（push/pull 到任意 registry）",
                log=r["log"])


# ── T6 治理可外置 ──
def t6(w):
    before = snapshot(STATE_DIRS)
    r_def = go(w, T6_PROMPT, "t6_default.log", timeout=600)
    st_def = t6_state(w)
    after = snapshot(STATE_DIRS)
    added, changed, sample = diff_snapshot(before, after)
    sh("rm -f " + os.path.join(w, "done.txt"), w, os.path.join(LOGS, TOOL, "t6_reset.log"), env=env_all())
    with open(os.path.join(w, "note.txt"), "w", encoding="utf-8") as f:
        f.write("甲方案可行，乙方案待议，甲优先。\n")
    r_str = go(w, T6_PROMPT, "t6_safety_strict.log", extra=["--safety", "strict"], timeout=600)
    st_str = t6_state(w)
    return dict(policy_external="file-external",
                policy_surface="YAML/CLI: --safety strict|balanced|restricted|autonomous（=--yolo）；hooks: --hook-pre-tool-use/--hook-post-tool-use/--hook-session-end",
                signoff_default=("executed" if not st_def["note_exists"] else "refused/asked"),
                signoff_strict=("executed" if not st_str["note_exists"] else "refused/asked"),
                audit_trail="local（~/.cagent/session.db）+ 可外置 hooks（--on-event/--hook-*）",
                audit_added=added, audit_changed=changed, audit_sample=sample,
                default_state=st_def, strict_state=st_str, log=[r_def["log"], r_str["log"]])


# ── T7 工具源可替换（YAML toolsets 挂同一个 MCP server） ──
def t7(w):
    ts = [{"command": "python3", "args": [PROBE_SRV]}]
    r = go(w, T7_PROMPT, "t7.log", toolsets=ts, timeout=600)
    j = judge_mcp(r["stdout"])
    extra_leg = None
    if not j["token_seen"]:
        r2 = go(w, T7_PROMPT, "t7_autonomous.log", toolsets=ts, extra=["--safety", "autonomous"], timeout=600)
        extra_leg = dict(rc=r2["rc"], **judge_mcp(r2["stdout"]), log=r2["log"])
    return dict(mcp_swap="yes-config", injection="agent.yaml toolsets: [{type: mcp, command, args}]",
                rc=r["rc"], seconds=r["seconds"], **j, autonomous_leg=extra_leg, log=r["log"])


CELLS = {"t1": t1, "t2": t2, "t3": t3, "t4": t4, "t5": t5, "t6": t6, "t7": t7}
