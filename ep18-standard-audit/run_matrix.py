#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ep18 标准审计 · 跑批器 v2（5 对象 × 7 格）

用法：
  python3 run_matrix.py --list                     # 列出对象与格
  python3 run_matrix.py --dry                      # 只打印将执行什么
  python3 run_matrix.py --only dsh --cells t1,t3   # 单对象单格（冒烟）
  python3 run_matrix.py                            # 全批
  python3 run_matrix.py --archive                  # 生成 ARCHIVE.md + 归档快照
诚实原则：读不到的写 unknown；跑不了的写 manual，不假装跑过。
"""
import argparse
import datetime
import importlib
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (BASE, HERE, LOGS, MCP_TOKEN, MODEL, RES, ROOT, RUNLOG, audit, prepare,  # noqa: E402
                    sha256_file, snapshot, diff_snapshot, tp_key, ds_key)

TOOLS = ["agentscope", "dsh", "claude", "codex", "docker-agent"]
CELLS = ["t1", "t2", "t3", "t4", "t5", "t6", "t7"]
CELL_DESC = {
    "t1": "能力+成本（读长文→5 要点+3 待核）",
    "t2": "危险命令（改 note.txt 甲→乙）",
    "t3": "接口可替换（同配置换 provider）",
    "t4": "记忆分层（A 告知→重启→再问 B）",
    "t5": "制品可移植（搬到别处原样跑）",
    "t6": "治理可外置（权限/签核/审计落哪 + 危险动作）",
    "t7": "工具源可替换（同一个 MCP server 喂进来）",
}


def load(tool):
    mod = "a_" + tool.replace("-", "_")
    return importlib.import_module(mod)


def res_path(tool):
    return os.path.join(RES, f"{tool}.json")


def load_res(tool):
    p = res_path(tool)
    if os.path.exists(p):
        try:
            return json.load(open(p, encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_res(tool, rec):
    json.dump(rec, open(res_path(tool), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def run_one(tool, cell, dry=False):
    rec = load_res(tool)
    rec.setdefault("tool", tool)
    rec.setdefault("model_intended", MODEL)
    rec["run_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    mod = load(tool)
    fn = getattr(mod, "CELLS", {}).get(cell)
    if fn is None:
        rec[cell] = {"status": "manual", "notes": f"{tool} 未实现 {cell}"}
        save_res(tool, rec)
        print(f"  {tool:14s} {cell}  MANUAL (未实现)")
        return rec
    w = prepare(tool)
    print(f"  {tool:14s} {cell}  running ...", flush=True)
    try:
        out = fn(w)
    except Exception as ex:  # 适配器自身异常也要留痕，不许静默
        import traceback
        out = {"status": "adapter-error", "error": f"{type(ex).__name__}: {ex}",
               "traceback": traceback.format_exc()[-1200:]}
        audit(tool=tool, cell=cell, status="adapter-error", error=str(ex)[:300])
    rec[cell] = out
    save_res(tool, rec)
    brief = json.dumps(out, ensure_ascii=False)
    print(f"  {tool:14s} {cell}  rc/status={out.get('status', out.get('behavior', out.get('switchable', 'ok')))} "
          f"{brief[:150]}")
    return rec


def archive(note=""):
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    adir = os.path.join(RES, f"archive-{ts}")
    os.makedirs(adir, exist_ok=True)
    man = {"batch": ts, "note": note, "model_intended": MODEL,
           "mcp_token": MCP_TOKEN, "tools": TOOLS, "cells": CELLS,
           "artifacts": {}, "tool_versions": {}, "inputs": {}}
    for t in TOOLS:
        p = res_path(t)
        if os.path.exists(p):
            shutil.copyfile(p, os.path.join(adir, f"{t}.json"))
            man["artifacts"][t] = {"file": f"{t}.json", "sha256": sha256_file(p)}
    man["inputs"]["radar-2026-10-09.md"] = sha256_file(os.path.expanduser(
        "~/workspace/ruiowl-content/radar/2026-10-09.md"))
    for f in ["common.py", "run_matrix.py", "a_agentscope.py", "a_dsh.py", "a_claude.py",
              "a_codex.py", "a_docker_agent.py", "mcp/ep18_probe_server.py"]:
        fp = os.path.join(HERE, f)
        if os.path.exists(fp):
            man["artifacts"].setdefault("harness", {})[f] = sha256_file(fp)
    man["runs_jsonl"] = {"file": "runs.jsonl", "lines": sum(1 for _ in open(RUNLOG, encoding="utf-8")) if os.path.exists(RUNLOG) else 0}
    if os.path.exists(RUNLOG):
        shutil.copyfile(RUNLOG, os.path.join(adir, "runs.jsonl"))
    with open(os.path.join(adir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(man, f, ensure_ascii=False, indent=1)
    lines = [f"# ep18 实测批次归档 · {ts}", "", f"> 备注：{note or '—'}", f"> 统一模型（intended）：{MODEL}",
             f"> MCP 探针 token：`{MCP_TOKEN}`", f"> 批次目录：`results/archive-{ts}/`", "",
             "## 产物哈希（sha256）", ""]
    for t, v in man["artifacts"].items():
        if t == "harness":
            for k, h in v.items():
                lines.append(f"- `{k}` — `{h[:16]}…`")
        else:
            lines.append(f"- `{v['file']}` — `{v['sha256'][:16]}…`")
    lines += ["", f"## 输入哈希", f"- `radar-2026-10-09.md` — `{man['inputs']['radar-2026-10-09.md'][:16]}…`",
              "", f"## 流程记录", f"- `runs.jsonl` 共 {man['runs_jsonl']['lines']} 行（每次调用一行：cmd/rc/seconds/日志路径/哈希）"]
    open(os.path.join(adir, "ARCHIVE.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"\n[archive] {adir}")
    print(f"[archive] runs.jsonl {man['runs_jsonl']['lines']} 行")
    return adir


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--cells", default="")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--archive", action="store_true")
    ap.add_argument("--note", default="")
    a = ap.parse_args()

    if a.list:
        print("对象：", TOOLS)
        for c in CELLS:
            print(f"  {c}: {CELL_DESC[c]}")
        return
    if a.archive:
        archive(a.note)
        return

    tools = [a.only] if a.only else TOOLS
    cells = [c for c in (a.cells.split(",") if a.cells else CELLS) if c]
    if a.dry:
        for t in tools:
            for c in cells:
                print(f"[dry] {t} / {c} — {CELL_DESC.get(c, '?')}")
        return
    print(f"批次开始 {datetime.datetime.now().isoformat(timespec='seconds')}｜对象={tools}｜格={cells}")
    audit(batch_start=datetime.datetime.now().isoformat(timespec="seconds"), tools=tools, cells=cells)
    for t in tools:
        print(f"=== {t} ===")
        for c in cells:
            run_one(t, c)
    print("\n结果：", RES)


if __name__ == "__main__":
    main()
