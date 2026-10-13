#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ep18 · 把 results/<tool>.json 汇总成《标准审计表 v1》（只搬观测值，不加评价）

用法：python3 make_matrix.py [> MATRIX.md]
"""
import json
import os

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
TOOLS = ["agentscope", "dsh", "claude", "codex", "docker-agent"]
CELLS = ["t1", "t2", "t3", "t4", "t5", "t6", "t7"]


def load(t):
    p = os.path.join(RES, f"{t}.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


def cell_value(tool, c, r):
    d = r.get(c) or {}
    if not isinstance(d, dict) or not d:
        return "—"
    if c == "t1":
        return f"{d.get('status', d.get('error','?'))}｜{d.get('seconds','?')}s｜读到文件={d.get('read_file')}｜专名命中={d.get('proper_noun_hits','?')}"
    if c == "t2":
        return f"{d.get('behavior','?')}｜note 改={d.get('note_changed')}｜自述={'有' if d.get('self_report') else '无'}"
    if c == "t3":
        return f"{d.get('switchable','?')}（注册/可用腿：{d.get('registered_providers', d.get('notes','')[:0]) or ''}）"
    if c == "t4":
        cross = d.get('cross_process') or d.get('resume_last') or d.get('new_process_continue') or (str(d.get('answer',''))[:12] if d.get('answer') else '—')
        return f"{d.get('remembered','?')}｜同进程={d.get('same_process', d.get('same_process_cell','—'))}｜跨进程={cross}"
    if c == "t5":
        return f"{d.get('portable','?')}｜搬了 {', '.join(d.get('moved', []) or []) or '—'}"
    if c == "t6":
        return (f"{d.get('policy_external','?')}｜签核={d.get('signoff') or d.get('signoff_default','?')}｜审计新增文件={d.get('audit_added','?')}"
                f"｜面={str(d.get('policy_surface',''))[:48]}")
    if c == "t7":
        tok = d.get("token_seen")
        return f"{d.get('mcp_swap','?')}｜token 实证={'✅' if tok else ('❌' if tok is False else '—')}"
    return str(d)[:60]


def main():
    recs = {t: load(t) for t in TOOLS}
    print("# ep18《标准审计表 v1》（框架/运行时层 · 4+1 对象 × 7 格）\n")
    print("> 只搬观测值，不加评价；缺格写 `—`。每格的原始记录见 `results/<tool>.json` 与 `logs/<tool>/*.log`。\n")
    hdr = "| 对象 | T1 能力+成本 | T2 危险命令 | T3 接口可替换 | T4 记忆分层 | T5 制品可移植 | T6 治理可外置 | T7 工具源可替换 |"
    print(hdr)
    print("|:--|:--|:--|:--|:--|:--|:--|:--|")
    for t in TOOLS:
        vals = [cell_value(t, c, recs[t]) for c in CELLS]
        print(f"| **{t}** | " + " | ".join(v.replace("|", "/") for v in vals) + " |")
    print("\n## 模型实跑口径（统一条件的例外，如实列出）\n")
    print("| 对象 | model_intended | model_actual（逐格） |")
    print("|:--|:--|:--|")
    for t in TOOLS:
        r = recs[t]
        actuals = sorted({(r.get(c) or {}).get("model_actual") for c in CELLS if isinstance(r.get(c), dict) and (r.get(c) or {}).get("model_actual")})
        print(f"| {t} | {r.get('model_intended','')} | {'；'.join(actuals) or '—'} |")
    print("\n## 五条表征 → 取证格 对照\n")
    print("| 表征 | 取证格 | 说明 |")
    print("|:--|:--|:--|")
    print("| 接口可替换 | T3（换模型）+ 脚本内换 provider 腿 | T7 补工具源一侧 |")
    print("| 制品可移植 | T5 | 记搬了什么、还需什么 |")
    print("| 行为可预期 | T2 | asked/executed/refused |")
    print("| 治理可外置 | T6 | 权限面是否文件化 + 审计落哪 |")
    print("| 成本可计量 | T1 | 耗时/字数；token 读不到写 unknown |")
    print("\n## 诚实边界\n")
    print("- 单次观测，不作统计结论；每个数字带时间戳（见 runs.jsonl）。")
    print("- 五条表征与七格判据**都是本团队设计的**，不是行业公认标准。")
    print("- 产品层（Gemini agent / 千问办公 / Qoder / WorkBuddy 等）不可本地复现 → 只做文档对照，不进本表。")
    print("- 读不到的字段写 `unknown`；跑不出来的写 `manual`，不推算、不假装跑过。")


if __name__ == "__main__":
    main()
