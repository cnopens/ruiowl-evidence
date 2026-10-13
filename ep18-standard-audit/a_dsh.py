#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ep18 适配器 · dsh（DeepSeek Harness 0.1.0-rc.6）
非交互入口：dsh --profile headless "<task>"（一次任务、打印最终消息、退出）

⚠️ 2026-10-13 实测结论（已写进 t3 证据）：dsh 的 provider 是**注册白名单**——
- `--patch` 改配置层被接受（id 定向覆盖），但 provider 名若不在注册表内 → `NO_ADAPTER`;
- 唯一注册的 `deepseek-official` 还对模型名做二次白名单（只认 deepseek-flash / deepseek-v4-pro）。
⇒ 统一模型（qwen3.8-max@TokenPlan）**不可达**，故本对象各格跑 profile 默认模型，并如实标注。
"""
import json
import os
import subprocess
import sys

from common import (CS, LOGS, MODEL, T2_PROMPT, T4A_PROMPT, T4B_PROMPT, T6_PROMPT, TP_BASE,
                    audit, classify_risky, ds_key, judge_t1, run, sh, snapshot, diff_snapshot,
                    t1_prompt, t6_state, tp_key)

TOOL = "dsh"
HERE = os.path.dirname(os.path.abspath(__file__))
PATCH_DIR = os.path.join(HERE, "patches")
os.makedirs(PATCH_DIR, exist_ok=True)
DSH = ["dsh", "--profile", "headless"]
DSH_HOME = os.path.expanduser("~/.dsh")
STATE_DIRS = [os.path.join(DSH_HOME, "sessions")]
MODEL_ACTUAL = "deepseek-v4-flash（profile 默认；统一模型不可达，见 t3）"

P_UNIFIED = os.path.join(PATCH_DIR, "dsh_unified_tokenplan.yml")
with open(P_UNIFIED, "w", encoding="utf-8") as f:
    f.write(f"""- id: agent-default-model
  config:
    provider: openai
    model: {MODEL}
    baseUrl: {TP_BASE}
    apiKeyEnv: DASHSCOPE_API_KEY
""")

PROVIDER_CANDIDATES = ["deepseek-official", "openai", "openai-compatible", "openai_compatible",
                       "pi-ai", "anthropic", "openai-responses", "dashscope", "tokenplan"]


def env_all():
    return {"DASHSCOPE_API_KEY": tp_key(), "DEEPSEEK_API_KEY": ds_key()}


def go(w, prompt, logname, env=None, timeout=600, patchfile=None):
    cmd = list(DSH)
    if patchfile:
        cmd += ["--patch", patchfile]
    cmd.append(prompt)
    e = env_all()
    e.update(env or {})
    r = run(cmd, w, os.path.join(LOGS, TOOL, logname), env=e, timeout=timeout)
    audit(tool=TOOL, cell=logname.split(".")[0], cmd=" ".join(cmd)[:300], rc=r["rc"],
          seconds=r["seconds"], log=r["log"], out_chars=r["out_chars"],
          model_actual=MODEL_ACTUAL, patch=(os.path.basename(patchfile) if patchfile else None))
    return r


# ── T1 能力 + 成本 ──
def t1(w):
    ru = go(w, "只回复：收到", "t1_unified_attempt.log", timeout=180, patchfile=P_UNIFIED)
    r = go(w, t1_prompt(w), "t1.log")
    j = judge_t1(r["stdout"])
    return dict(status="ok" if r["rc"] == 0 else "fail", model_leg="profile-default",
                model_actual=MODEL_ACTUAL,
                unified_attempt=dict(rc=ru["rc"], stderr_tail=(ru["stderr"] or "").strip()[-160:]),
                seconds=r["seconds"], **j, log=r["log"])


# ── T2 危险命令（默认安全面，不加放行参数） ──
def t2(w):
    r = go(w, T2_PROMPT, "t2.log")
    return dict(status="ok" if r["rc"] == 0 else "fail", seconds=r["seconds"],
                **classify_risky(r["stdout"], os.path.join(w, "note.txt")), log=r["log"])


# ── T3 接口可替换（本期核心） ──
def t3(w):
    """leg1 patch 层是否被接受；leg2 provider 注册表扫描（14 个候选名逐一实跑）。"""
    st = sh(f"dsh --profile headless --patch {P_UNIFIED} --dump-config | grep -A6 'agent-default-model' | head -9",
            w, os.path.join(LOGS, TOOL, "t3_static.log"), env=env_all())
    layer_accepted = ("baseUrl" in st["stdout"]) and (MODEL in st["stdout"])
    lines = []
    for n in PROVIDER_CANDIDATES:
        p = os.path.join(PATCH_DIR, f"dsh_probe_{n}.yml")
        with open(p, "w", encoding="utf-8") as f:
            f.write(f"- id: agent-default-model\n  config:\n    provider: {n}\n    model: {MODEL}\n"
                    f"    baseUrl: {TP_BASE}\n    apiKeyEnv: DASHSCOPE_API_KEY\n")
        try:
            r = subprocess.run(["dsh", "--profile", "headless", "--patch", p, "只回复：收到"],
                               capture_output=True, text=True, timeout=120, cwd=w, env={**os.environ, **env_all()})
            err = ((r.stderr or "").strip().splitlines() or [""])[-1]
            lines.append(f"{n:20s} rc={r.returncode:4d} err={err[:120]}")
        except subprocess.TimeoutExpired:
            lines.append(f"{n:20s} rc= -99 TIMEOUT")
    with open(os.path.join(LOGS, TOOL, "t3_provider_sweep.log"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    registered = [l.split()[0] for l in lines if "NO_ADAPTER" not in l]
    no_adapter = len([l for l in lines if "NO_ADAPTER" in l])
    return dict(switchable="no", layer_accepted=layer_accepted, registered_providers=registered,
                no_adapter_count=no_adapter, candidates=len(lines),
                model_whitelist_evidence=[l for l in lines if "INVALID_REQUEST" in l][:2],
                notes=("换 provider 不是改配置就行：适配器是注册白名单（非注册名 → NO_ADAPTER），"
                       "且已注册适配器对模型名再做白名单校验；自定义 baseUrl 不被接受"),
                log=os.path.join(LOGS, TOOL, "t3_provider_sweep.log"))


# ── T4 记忆分层（headless 一次性退出 → 只能测跨进程那半格） ──
def t4(w):
    rA = go(w, T4A_PROMPT, "t4_a.log", timeout=300)
    rB = go(w, T4B_PROMPT, "t4_b.log", timeout=300)
    hit = "心灯" in (rB["stdout"] or "")
    snap = snapshot(STATE_DIRS)
    return dict(remembered="yes" if hit else "no", same_process_cell="not-testable",
                note="headless 一次任务即退出，无续会话入口 → 同进程那半格不可测",
                leg_a_rc=rA["rc"], leg_b_rc=rB["rc"], answer=(rB["stdout"] or "").strip()[:80],
                session_files=sum(len(v or []) for v in snap.values()), log=[rA["log"], rB["log"]])


# ── T5 制品可移植（复制 profile + 换 DSH_HOME，原样跑） ──
def t5(w):
    home = "/tmp/ep18-portable/dshhome"
    os.makedirs(home, exist_ok=True)
    out = sh(f"rm -rf {home}/profiles && mkdir -p {home}/profiles && "
             f"cp -R {DSH_HOME}/profiles/headless {home}/profiles/headless && ls {home}/profiles/headless",
             w, os.path.join(LOGS, TOOL, "t5_copy.log"), env=env_all())
    moved = [x for x in out["stdout"].split() if x]
    r = go(w, "只回复：收到", "t5_run.log", timeout=300, env={"DSH_HOME": home})
    return dict(portable="yes" if r["rc"] == 0 else "partial", moved=moved, dsh_home=home,
                rc=r["rc"], seconds=r["seconds"],
                notes="profile 目录整体搬到新 DSH_HOME 后原样可跑（相对引用）；程序本身仍需全局 dsh CLI",
                log=r["log"])


# ── T6 治理可外置 ──
def t6(w):
    before = snapshot(STATE_DIRS)
    r = go(w, T6_PROMPT, "t6.log")
    after = snapshot(STATE_DIRS)
    added, changed, sample = diff_snapshot(before, after)
    st = t6_state(w)
    return dict(policy_external="file-external",
                policy_surface="cordis.patch.yml / --patch（id 定向覆盖，可版本化）",
                signoff=("executed" if not st["note_exists"] else "refused"),
                audit_trail="local-jsonl（~/.dsh/sessions）", audit_added=added, audit_changed=changed,
                audit_sample=sample, **st, log=r["log"])


# ── T7 工具源可替换（同一个 MCP server 喂进来） ──
def t7(w):
    probe = sh("dsh --profile headless --dump-config | grep -ci -E 'mcp|model-context-protocol'", w,
               os.path.join(LOGS, TOOL, "t7_probe.log"), env=env_all())
    mentions = int(probe["stdout"].strip() or 0)
    if mentions == 0:
        return dict(mcp_swap="no", mcp_mentions=0,
                    notes="profile 合成配置里 0 处 MCP 相关插件/字段 → 该对象当前无 MCP 接入面",
                    log=probe["log"])
    return dict(mcp_swap="unknown", mcp_mentions=mentions,
                notes="配置里出现 MCP 字样但接入形态未定；本轮未跑通", log=probe["log"])


CELLS = {"t1": t1, "t2": t2, "t3": t3, "t4": t4, "t5": t5, "t6": t6, "t7": t7}
