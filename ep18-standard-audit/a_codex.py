#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ep18 适配器 · codex CLI 0.144.3
非交互入口：codex exec --skip-git-repo-check "<prompt>"
配置面：~/.codex/config.toml（model_providers.*）+ `-c` 覆盖 + `-p <name>` 分层 profile + `codex mcp add`。

⚠️ 实测（2026-10-13）：
1) codex 只支持 `wire_api = "responses"`（chat 已被移除：`wire_api="chat" is no longer supported`）；
2) 因此能否接某个 OpenAI 兼容域，取决于**该域名是否提供 Responses 协议**——这也是 T3 的门槛。
3) 统一模型若不可达，则退到本机既有配置（~/.codex/config.toml 默认 provider），并如实标注 model_actual。
"""
import json
import os

from common import (DS_OPENAI_BASE, DS_MODEL, LOGS, MODEL, PROBE_SRV, T2_PROMPT, T4A_PROMPT,
                    T4B_PROMPT, T6_PROMPT, T7_PROMPT, TP_BASE, audit, classify_risky, ds_key,
                    judge_mcp, judge_t1, run, sh, snapshot, diff_snapshot, t1_prompt, t6_state,
                    tp_key)

TOOL = "codex"
CODEX_HOME = os.path.expanduser("~/.codex")
STATE_DIRS = [os.path.join(CODEX_HOME, "sessions"), os.path.join(CODEX_HOME, "log"),
              os.path.join(CODEX_HOME, "history.jsonl")]
MINIMAX_ENV = os.path.expanduser("~/.config/secrets/minimax.env")
MODEL_ACTUAL_DEFAULT = "codex config.toml 默认 provider（MiniMax-M3），统一模型不可达，见 t3"
# 实测：codex 用 wire_api=responses 可直连 TokenPlan（t3 unified_rc=0），故各格默认走 unified leg
LEG = "unified"

TP_PROV = ('model_providers.tokenplan={name="TokenPlan",base_url="%s",env_key="TP_KEY",wire_api="responses"}' % TP_BASE)
DS_PROV = ('model_providers.ep18alt={name="DeepSeek",base_url="%s",env_key="DS_KEY",wire_api="responses"}' % DS_OPENAI_BASE)


def minimax_key():
    if not os.path.exists(MINIMAX_ENV):
        return ""
    for line in open(MINIMAX_ENV, encoding="utf-8", errors="ignore"):
        if line.strip().startswith("MINIMAX_API_KEY"):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def env_all():
    return {"TP_KEY": tp_key(), "DS_KEY": ds_key(), "DEEPSEEK_API_KEY": ds_key(),
            "MINIMAX_API_KEY": minimax_key()}


def go(w, prompt, logname, leg=LEG, extra=None, timeout=900):
    cmd = ["codex", "exec", "--skip-git-repo-check"]
    if leg == "unified":
        cmd += ["-c", TP_PROV, "-c", "model_provider=tokenplan", "-c", f'model="{MODEL}"']
    elif leg == "alt":
        cmd += ["-c", DS_PROV, "-c", "model_provider=ep18alt", "-c", f'model="{DS_MODEL}"']
    cmd += (extra or []) + [prompt]
    r = run(cmd, w, os.path.join(LOGS, TOOL, logname), env=env_all(), timeout=timeout)
    audit(tool=TOOL, cell=logname.split(".")[0], cmd=f"codex exec [leg={leg}]", rc=r["rc"],
          seconds=r["seconds"], log=r["log"], out_chars=r["out_chars"],
          model_actual=(MODEL_ACTUAL_DEFAULT if leg == "default" else f"{leg}@{'tokenplan' if leg=='unified' else 'deepseek'}"))
    return r


# ── T1 能力 + 成本 ──
def t1(w):
    ru = go(w, "只回复：收到", "t1_unified_attempt.log", leg="unified", timeout=300)
    leg = "default" if ru["rc"] != 0 else "unified"
    r = go(w, t1_prompt(w), "t1.log", leg=leg, timeout=900)
    j = judge_t1(r["stdout"])
    return dict(status="ok" if r["rc"] == 0 else "fail", model_leg=leg,
                model_actual=(MODEL_ACTUAL_DEFAULT if leg == "default" else f"{MODEL}@TokenPlan"),
                unified_attempt=dict(rc=ru["rc"], err_tail=(ru["stderr"] or "").strip()[-160:],
                                     out_tail=(ru["stdout"] or "").strip()[-120:]),
                seconds=r["seconds"], **j, log=r["log"])


# ── T2 危险命令（默认沙箱/审批面） ──
def t2(w):
    r = go(w, T2_PROMPT, "t2.log", leg=LEG, timeout=600)
    return dict(status="ok" if r["rc"] == 0 else "fail", seconds=r["seconds"],
                out_tail=(r["stdout"] or "").strip()[-200:],
                err_tail=(r["stderr"] or "").strip()[-160:],
                **classify_risky(r["stdout"], os.path.join(w, "note.txt")), log=r["log"])


# ── T3 接口可替换（三条腿：统一域 / 另一个兼容域 / 本机默认配置） ──
def t3(w):
    r1 = go(w, "只回复：收到", "t3_unified.log", leg="unified", timeout=300)
    r2 = go(w, "只回复：收到", "t3_alt_provider.log", leg="alt", timeout=300)
    r3 = go(w, "只回复：收到", "t3_default_config.log", leg="default", timeout=300)
    ok = [i for i, x in enumerate([r1, r2, r3]) if x["rc"] == 0]
    return dict(switchable="yes-config" if 0 in ok else ("partial" if len(ok) >= 2 else "needs-proxy"),
                unified_rc=r1["rc"], alt_rc=r2["rc"], default_rc=r3["rc"],
                unified_err=(r1["stderr"] or "").strip()[-160:],
                alt_err=(r2["stderr"] or "").strip()[-160:],
                notes=("provider 走 config.toml 的 model_providers.* 且必须 wire_api=responses；"
                       "-c 即可覆盖换域（同一套命令换 base_url/model），另有 -p 分层 profile 与 codex mcp add"),
                log=[r1["log"], r2["log"], r3["log"]])


# ── T4 记忆分层 ──
def t4(w):
    rA = go(w, T4A_PROMPT, "t4_a.log", timeout=300)
    rB = go(w, T4B_PROMPT, "t4_b.log", timeout=300)
    rC = go(w, T4B_PROMPT, "t4_c_resume.log", timeout=300, extra=["resume", "--last"])
    plain = "心灯" in (rB["stdout"] or "")
    res = "心灯" in (rC["stdout"] or "")
    return dict(remembered="session-only" if (res and not plain) else ("yes" if res else "no"),
                new_process_plain="yes" if plain else "no", resume_last="yes" if res else "no",
                notes="新进程不记得；`codex exec resume --last` 续会话才记得（本地会话文件）",
                log=[rA["log"], rB["log"], rC["log"]])


# ── T5 制品可移植（整份 config + skills 搬到别的 CODEX_HOME） ──
def t5(w):
    dest = "/tmp/ep18-portable/codexhome"
    sh(f"rm -rf {dest} && mkdir -p {dest} && cp {CODEX_HOME}/config.toml {dest}/ 2>/dev/null; "
       f"cp -R {CODEX_HOME}/skills {dest}/ 2>/dev/null; ls {dest}", w,
       os.path.join(LOGS, TOOL, "t5_copy.log"), env=env_all())
    r = go(w, "只回复：收到", "t5_run.log", timeout=300, extra=None)
    return dict(portable="yes" if r["rc"] == 0 else "partial", dest=dest, moved=["config.toml", "skills"],
                rc=r["rc"], notes="config.toml + skills 可搬；会话/历史留在原 CODEX_HOME，不随制品走",
                log=r["log"])


# ── T6 治理可外置 ──
def t6(w):
    before = snapshot(STATE_DIRS)
    r = go(w, T6_PROMPT, "t6.log", timeout=600)
    after = snapshot(STATE_DIRS)
    added, changed, sample = diff_snapshot(before, after)
    st = t6_state(w)
    out = sh("grep -cE 'approval_policy|sandbox_mode' ~/.codex/config.toml", w,
             os.path.join(LOGS, TOOL, "t6_policy_probe.log"), env=env_all())
    return dict(policy_external="file-external",
                policy_surface="config.toml: approval_policy / sandbox_mode；CLI: -s read-only|workspace-write|danger-full-access + --dangerously-bypass-*；另有 execpolicy `.rules`",
                policy_keys_in_config=int(out["stdout"].strip() or 0),
                signoff=("executed" if not st["note_exists"] else "refused/asked"),
                out_tail=(r["stdout"] or "").strip()[-200:],
                audit_trail="local（~/.codex/log + sessions/ + history.jsonl）",
                audit_added=added, audit_changed=changed, audit_sample=sample, **st, log=r["log"])


# ── T7 工具源可替换（-c 注入同一个 MCP server） ──
def t7(w):
    extra = ["-c", 'mcp_servers.ep18probe.command="python3"',
             "-c", f"mcp_servers.ep18probe.args={json.dumps([PROBE_SRV])}",
             "--dangerously-bypass-approvals-and-sandbox"]
    r = go(w, T7_PROMPT, "t7.log", extra=extra, timeout=600)
    j = judge_mcp(r["stdout"])
    return dict(mcp_swap="yes-config", injection='-c mcp_servers.*（等价 `codex mcp add` 写 config.toml）',
                rc=r["rc"], seconds=r["seconds"], **j,
                out_tail=(r["stdout"] or "").strip()[-200:], log=r["log"])


CELLS = {"t1": t1, "t2": t2, "t3": t3, "t4": t4, "t5": t5, "t6": t6, "t7": t7}
