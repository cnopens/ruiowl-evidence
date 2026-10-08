#!/usr/bin/env python3
"""Ep14 对决 · 预跑校准执行器。

独立 clone 任务仓库 → 装依赖 → headless 跑 agent（可配超时）→ 逐条验证判据
→ 结果写 results/<task>-<tool>-<ts>.json 并打印摘要。

用法:
    python3 preflight.py t1 claude [--timeout 1800] [--keep]
    python3 preflight.py t2 dsh
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path.home() / "workspace/ruiowl-content/ep14-dsh-vs-claude-code"
SOURCE_DIR = REPO_ROOT / "task-repos"
RESULTS_DIR = Path(__file__).resolve().parent / "results"

TASKS = {
    "t1": {
        "repo": "task1-invoice-api",
        "install": ["pnpm", "install"],
        "desc": (
            "仓库中有一组失败的测试。修复代码使所有测试通过。"
            "不要修改任何测试文件、不要修改 package.json。完成后运行 pnpm test 验证。"
        ),
        "verify": "verify_t1",
    },
    "t2": {
        "repo": "task2-log-processor",
        "install": [
            "bash", "-c",
            "python3 -m venv .venv && .venv/bin/python -m pip install -q pytest",
        ],
        "desc": (
            "为这个 Python CLI 新增 dedupe 子命令：按「时间戳(精确到秒，忽略毫秒) + 级别 + "
            "消息前 50 字符」去重相邻重复行（同秒内的日志风暴视为重复），支持 --keep first|last "
            "参数（重复组保留首行/末行）和 -o 输出文件。硬性要求：① 输出必须保持与输入相同的"
            "固定行格式（timestamp level message），保证 parse/stats 能直接管道消费 dedupe 输出；"
            "② 算法必须 O(n)：验收会生成 10 万行日志实测，60 秒内完成且不得把整个文件在内存里"
            "复制多份做二次遍历。实现后为它编写测试并确保 pytest 全部通过。"
            "仓库已预置 .venv/（基于本机 python3 创建，已装 pytest）——这是唯一的验收运行环境："
            "必须用 .venv/bin/python -m pytest 验证全绿，禁止删除/重建 .venv，禁止用其它解释器跑测试。"
            "可修改 CLI 结构但不得破坏现有子命令行为（parse/stats 基线测试不许改）。"
        ),
        "verify": "verify_t2",
    },
    "t3": {
        "repo": "task3-config-lib",
        "install": ["pnpm", "install"],
        "desc": (
            '将代码库中的核心类 ConfigLoader 重命名为 ConfigSource：包括类定义、所有 import/export '
            '引用、类型声明（如 ConfigLoaderOptions → ConfigSourceOptions）与 README 等文档。完成后'
            '全仓库（pnpm-lock.yaml、node_modules 除外）不得出现 "ConfigLoader" 字样（grep 验证，'
            '含字符串与注释），且 build 与测试必须通过。不要改变任何行为逻辑。'
            '注意：仓库含 src/features 等大量消费方模块与 examples/docs 文档，漏改任何一处都会被 grep 抓住。'
        ),
        "verify": "verify_t3",
    },
}

TIMEOUT_S = 60 * 60  # 60 分钟上限，可用 --timeout 覆盖


def deepseek_env() -> dict:
    """注入 DEEPSEEK_API_KEY：优先环境变量，否则自动读 ~/.hermes/.env。

    免去每次跑前手动 export（key 值不落盘、不回显）。
    """
    env = os.environ.copy()
    if env.get("DEEPSEEK_API_KEY"):
        return env
    env_file = Path.home() / ".hermes/.env"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            m = re.match(r'^DEEPSEEK_API_KEY\s*=\s*(.*)$', line.strip())
            if m:
                env["DEEPSEEK_API_KEY"] = m.group(1).strip().strip('"').strip("'")
                break
    return env


def claude_backend_settings(backend: str) -> tuple[list[str], Path | None]:
    """claude CLI 后端选择。

    minimax：什么都不做（沿用 ~/.claude/settings.json 的 MiniMax 路由，即现状）。
    deepseek：生成临时 --settings 文件，把 claude 指向 DeepSeek Anthropic 兼容端点
    （https://api.deepseek.com/anthropic），模型对齐 dsh 侧 headless 实际用的
    deepseek-v4-flash —— 排除模型变量，只比工具本身。key 从 DEEPSEEK_API_KEY 读，
    临时文件权限 600，进程结束后删除，不留盘。
    """
    if backend != "deepseek":
        return [], None
    key = deepseek_env().get("DEEPSEEK_API_KEY", "")
    if not key:
        print("❌ 找不到 DEEPSEEK_API_KEY（~/.hermes/.env），无法切换 claude 到 DeepSeek",
              file=sys.stderr)
        sys.exit(2)
    settings = {
        "env": {
            "ANTHROPIC_BASE_URL": "https://api.deepseek.com/anthropic",
            "ANTHROPIC_AUTH_TOKEN": key,
            "ANTHROPIC_MODEL": "deepseek-v4-flash",
            "ANTHROPIC_DEFAULT_OPUS_MODEL": "deepseek-v4-flash",
            "ANTHROPIC_DEFAULT_SONNET_MODEL": "deepseek-v4-flash",
            "ANTHROPIC_DEFAULT_HAIKU_MODEL": "deepseek-v4-flash",
            "CLAUDE_CODE_SUBAGENT_MODEL": "deepseek-v4-flash",
            "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "786432",
        }
    }
    p = Path(tempfile.mkstemp(prefix="claude-ep14-", suffix=".json")[1])
    p.write_text(json.dumps(settings, ensure_ascii=False), encoding="utf-8")
    p.chmod(0o600)
    print(f"ℹ️  claude 后端 = deepseek（api.deepseek.com/anthropic，模型 deepseek-v4-flash，"
          f"临时 settings: {p.name}）")
    return ["--settings", str(p)], p


def sh(cmd: list[str], cwd: Path, timeout: int = 120, silent: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout)


# ---------- 判据验证 ----------

def verify_t1(work: Path) -> dict:
    r = sh(["pnpm", "test"], work, timeout=300)
    # vitest: 全绿退出码 0 且输出含 "passed"；有失败时退出码非 0
    passed = r.returncode == 0 and "passed" in r.stdout
    diff = sh(["git", "diff", "--name-only"], work)
    touched_tests = any("test/" in f or "tests/" in f for f in diff.stdout.splitlines())
    pkg_diff = sh(["git", "diff", "--", "package.json", "pnpm-lock.yaml"], work)
    violations = []
    if touched_tests:
        violations.append("改动了测试文件")
    if pkg_diff.stdout.strip():
        violations.append("改动了 package.json/lockfile")
    return {"test_8_8": passed, "violations": violations,
            "test_tail": "\n".join(r.stdout.strip().splitlines()[-3:])}


def verify_t2(work: Path) -> dict:
    py = work / ".venv/bin/python"
    if not py.is_file():  # 环境故障要响亮失败，不许静默假 FAIL
        return {"pytest_all_green": False, "help_ok": False, "sample_ok": False,
                "sample_output": f"[env] .venv/bin/python 缺失——安装步可能失败，请查日志"}
    r = sh([str(py), "-m", "pytest", "-q"], work, timeout=300)
    passed = "passed" in r.stdout and "failed" not in r.stdout
    help_r = sh([str(py), "-m", "logproc", "dedupe", "--help"], work, timeout=60)
    help_ok = help_r.returncode == 0 and "dedupe" in help_r.stdout
    # 内置验收样例：同秒同消息风暴应合并
    sample = (
        "2026-09-07 08:15:30.123 INFO  retry attempt failed\n"
        "2026-09-07 08:15:30.777 INFO  retry attempt failed\n"
        "2026-09-07 08:15:31.002 ERROR disk full\n"
        "2026-09-07 08:15:31.050 ERROR disk full\n"
    )
    tmp = work / "_dedupe_sample.log"
    tmp.write_text(sample, encoding="utf-8")
    dr = sh([str(py), "-m", "logproc", "dedupe", str(tmp)], work, timeout=60)
    lines = [ln for ln in dr.stdout.strip().splitlines() if ln.strip()]
    sample_ok = len(lines) == 2 and "08:15:30.123" in lines[0] and "08:15:31.002" in lines[1]

    # 管道兼容：dedupe 输出必须保持固定行格式，parse 能直接消费
    pipe_ok = False
    deduped_out = ""
    if sample_ok:
        out_f = work / "_dedupe_out.log"
        dr2 = sh([str(py), "-m", "logproc", "dedupe", "-o", str(out_f), str(tmp)], work, timeout=60)
        if dr2.returncode == 0 and out_f.is_file():
            deduped_out = out_f.read_text(encoding="utf-8")
            pr = sh([str(py), "-m", "logproc", "parse", str(out_f)], work, timeout=60)
            parsed_n = len([ln for ln in pr.stdout.splitlines() if ln.strip()])
            pipe_ok = pr.returncode == 0 and parsed_n == 2

    # 性能：10 万行风暴日志，60s 内完成（O(n) 单遍）
    perf_ok = False
    perf_elapsed = -1
    big = work / "_dedupe_big.log"
    n_groups = 20_000
    rows = []
    for g in range(n_groups):
        # 每组 5 行同秒同消息 → dedupe 后每组剩 1 行；跨组消息不同不合并
        rows.append(f"2026-09-08 10:{(g // 60) % 60:02d}:{g % 60:02d}.{g % 1000:03d} ERROR  msg-{g:05d} worker pool starved waiting on queue lock\n" * 5)
    big.write_text("".join(rows), encoding="utf-8")
    started_perf = dt.datetime.now()
    pr = sh([str(py), "-m", "logproc", "dedupe", str(big)], work, timeout=65)
    perf_elapsed = round((dt.datetime.now() - started_perf).total_seconds(), 1)
    out_lines = [ln for ln in pr.stdout.splitlines() if ln.strip()]
    perf_ok = pr.returncode == 0 and perf_elapsed <= 60 and len(out_lines) == n_groups

    return {"pytest_all_green": passed, "help_ok": help_ok, "sample_ok": sample_ok,
            "pipe_ok": pipe_ok, "perf_ok": perf_ok, "perf_elapsed_s": perf_elapsed,
            "sample_output": dr.stdout.strip()}


def verify_t3(work: Path) -> dict:
    b = sh(["pnpm", "build"], work, timeout=300)
    build_ok = b.returncode == 0
    t = sh(["pnpm", "test"], work, timeout=300)
    test_ok = t.returncode == 0 and "4 passed" in t.stdout
    g = subprocess.run(
        ["grep", "-r", "-n", "--exclude-dir=node_modules", "--exclude-dir=.git",
         "--exclude-dir=dist", "--exclude=pnpm-lock.yaml", "ConfigLoader", "."],
        capture_output=True, text=True, cwd=work,
    )
    no_residue = g.returncode != 0  # grep 无命中 → exit 1
    return {"build_ok": build_ok, "test_4_4": test_ok, "grep_clean": no_residue,
            "grep_hits": g.stdout.strip()[:500]}


# ---------- 主流程 ----------

def main() -> int:
    ap = argparse.ArgumentParser(description="Ep14 预跑校准执行器")
    ap.add_argument("task", choices=sorted(TASKS))
    ap.add_argument("tool", choices=["claude", "dsh"])
    ap.add_argument("--timeout", type=int, default=TIMEOUT_S, help="agent 超时秒数")
    ap.add_argument("--keep", action="store_true", help="保留工作目录不删")
    ap.add_argument("--claude-backend", choices=["minimax", "deepseek"], default="deepseek",
                    help="claude CLI 后端：deepseek=统一模型对决(默认,对齐dsh)，minimax=走 settings.json 现状")
    args = ap.parse_args()

    spec = TASKS[args.task]
    src = SOURCE_DIR / spec["repo"]
    if not src.is_dir():
        print(f"❌ 找不到源仓库: {src}", file=sys.stderr)
        return 2

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix=f"preflight-{args.task}-{args.tool}-"))
    print(f"[1/5] clone 源仓库 → {work}")
    if sh(["git", "clone", "-q", str(src), str(work)], SOURCE_DIR).returncode != 0:
        print("❌ clone 失败", file=sys.stderr)
        return 2

    print(f"[2/5] 安装依赖 ({spec['install'][0]})…")
    inst = sh(spec["install"], work, timeout=600)
    if inst.returncode != 0:
        print("❌ 依赖安装失败，中止（避免静默假 FAIL）", file=sys.stderr)
        print((inst.stderr or inst.stdout)[-800:], file=sys.stderr)
        shutil.rmtree(work, ignore_errors=True)
        return 2

    print(f"[3/5] headless 跑 agent（超时 {args.timeout}s）…")
    started = dt.datetime.now()
    tmp_settings = None
    if args.tool == "claude":
        _, tmp_settings = claude_backend_settings(args.claude_backend)
        if tmp_settings is not None:
            cmd = ["claude", "--settings", str(tmp_settings), "-p", spec["desc"],
                   "--dangerously-skip-permissions"]
        else:
            cmd = ["claude", "-p", spec["desc"], "--dangerously-skip-permissions"]
    else:
        # dsh 全局 CLI：cwd=任务仓库（headless 无 --cwd 参数，工作目录=进程 cwd）
        cmd = ["dsh", "--profile", "headless", spec["desc"]]
    try:
        agent = subprocess.run(cmd, capture_output=True, text=True, cwd=work, timeout=args.timeout, env=deepseek_env())
        elapsed_s = round((dt.datetime.now() - started).total_seconds())
        timed_out = False
    except subprocess.TimeoutExpired:
        agent = None
        elapsed_s = args.timeout
        timed_out = True
        print("⏰ agent 超时（60min 上限），按救援规则记「未完成」")
    finally:
        if tmp_settings is not None:  # 临时 settings 含 key，用完即删
            try:
                tmp_settings.unlink()
            except OSError:
                pass

    print(f"[4/5] 验证判据…")
    verifier = globals()[spec["verify"]]
    verdict = verifier(work) if not timed_out else {"timeout": True}
    # 判定：所有 bool 判据全 true 且无违规 = pass（按任务各自的判据字段数）
    bool_checks = [k for k, v in verdict.items() if isinstance(v, bool)]
    all_true = len(bool_checks) > 0 and all(verdict[k] for k in bool_checks)
    passed = all_true and not (verdict.get("violations")) and "timeout" not in verdict
    final_pass = passed

    # 终态：超时时也试一次判据（agent 可能已完成大部分）
    if timed_out:
        try:
            verdict = verifier(work)
        except Exception:
            pass

    print(f"[5/5] 清理…")
    log_tail = ""
    if agent is not None:
        log_tail = (agent.stdout or "")[-600:] + (agent.stderr or "")[-400:]

    record = {
        "task": args.task, "tool": args.tool,
        "started": started.isoformat(timespec="seconds"),
        "elapsed_s": elapsed_s, "timed_out": timed_out,
        "verdict": verdict, "final_pass": final_pass,
        "workdir": str(work) if args.keep else None,
        "agent_log_tail": log_tail,
    }
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    out_file = RESULTS_DIR / f"{args.task}-{args.tool}-{stamp}.json"
    out_file.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "=" * 60)
    print(f"结果: task={args.task} tool={args.tool} 耗时={elapsed_s}s 超时={timed_out}")
    print(f"FINAL_PASS: {'✅ 是' if final_pass else '❌ 否'}")
    for k, v in verdict.items():
        if isinstance(v, bool):
            print(f"  {k}: {'✅' if v else '❌'}")
    if verdict.get("violations"):
        print(f"  VIOLATIONS: {verdict['violations']}")
    print(f"详情: {out_file}")
    print("=" * 60)

    if not args.keep:
        shutil.rmtree(work, ignore_errors=True)
    return 0 if final_pass else 1


if __name__ == "__main__":
    sys.exit(main())
