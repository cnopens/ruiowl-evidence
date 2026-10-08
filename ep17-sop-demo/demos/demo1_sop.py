#!/usr/bin/env python3
"""D1 · SOP 三步走（ep17 真机演示 1）

演示内容：
  1. 「写一篇短文」被拆成 **有序步骤**：出大纲 →（审稿人判定）→ 成稿
  2. **第 1 次提交人为设成不通过**：为的是在同一镜里看到「打回 → 带上意见重试」这条路径
     （审稿人是同一个 agent，记得上一轮，所以第 2 次才放行 —— 屏幕上有「判定 N 次」可对账）
  3. 每一步：执行者干活 → 验证者判定 → 通过才进下一步；**尝试预算** 印在屏幕上
  4. **存盘 / 续跑**：`--park-after 1` 跑完第 1 步就退出并存状态；
     `--resume` 从状态文件重建引擎接着走（对应「进程挂了、机器重启，从断点接着跑」）

模型：百炼 TokenPlan（qwen3.8-max，走 token-plan 域）—— 演示调用量很小
     无 key 时回落到本机 Ollama（慢，但可离线复现）

用法：
    source ~/.zshrc                                   # 载入 key（不打印）
    V=~/workspace/agentscope-test/.venv/bin/python
    $V demo1_sop.py                 # 完整跑一遍
    $V demo1_sop.py --park-after 1  # 跑到第 1 步结束即中断（存盘）→ 录「中断」那一镜
    $V demo1_sop.py --resume        # 从断点续跑 → 录「续跑」那一镜
"""
import argparse
import asyncio
import os
import pathlib
import time

from agentscope.agent import Agent
from agentscope.message import UserMsg
from agentscope.model import DashScopeChatModel, OllamaChatModel
from agentscope.credential import DashScopeCredential, OllamaCredential
from agentscope.sop import SOP, SOPEngine, SOPStep, SOPRunState, SOPPhase

HERE = pathlib.Path(__file__).resolve().parent
STATE_FILE = HERE / "state" / "demo1_sop_state.json"
TOPIC = "向量数据库"

CHECKS = [
    "至少三个小节",
    "每一节都要写清「讲什么」和「为什么读者需要它」",
    "末尾必须给出可核实的信息来源要求（不是自己编来源）",
]
TOKENPLAN_BASE = "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"


def banner(t):
    print("\n" + "=" * 78)
    print(f"  {t}")
    print("=" * 78)


def build_model():
    key = os.getenv("DASHSCOPE_API_KEY", "")
    if key:
        name = os.getenv("DEMO_MODEL", "qwen3.8-max")
        ck = {"api_key": key}
        if key.startswith("sk-sp-"):
            ck["base_url"] = TOKENPLAN_BASE       # TokenPlan key 必须走 token-plan 域，否则 401
        return DashScopeChatModel(credential=DashScopeCredential(**ck), model=name), f"百炼 / {name}"
    name = os.getenv("DEMO_MODEL", "qwen2.5-coder:7b")
    return OllamaChatModel(credential=OllamaCredential(), model=name), f"本机 Ollama / {name}"


def build_sop(model):
    writer = Agent(
        name="Writer",
        system_prompt=(
            "你是一位技术写作者，用中文写作。每一步只交付这一步要求的东西，不要多写；"
            "把交付物写清楚，让没看过你工作的人也能接着用。"
        ),
        model=model,
    )
    reviewer = Agent(
        name="Reviewer",
        system_prompt=(
            "你是严格的审稿人，只判定、不动笔。判据：\n- " + "\n- ".join(CHECKS) +
            "\n规则：**第 1 次审稿一律不通过**（指出缺哪一项、要求怎么改）；"
            "从第 2 次起，只要三项都满足就判通过。判语要短、要具体。"
        ),
        model=model,
    )
    return SOP(
        name="write-short-article",
        description="写一篇介绍性短文：先出大纲，审过再写成稿。",
        steps=[
            SOPStep(
                subject="第一步 · 出大纲",
                description="给出文章大纲：至少三个小节，每节写清讲什么、为什么读者需要它。",
                executor=writer,
                verifier=reviewer,      # 有验证者：判定不过就退回重写
                max_attempts=3,         # 尝试预算：被打回 3 次仍未过 = 整轮失败
            ),
            SOPStep(
                subject="第二步 · 写成稿",
                description="按已通过的大纲写成完整短文（300 字以内），末尾列出你要核实的信息来源。",
                executor=writer,        # 不设验证者：执行者交活即算过
            ),
        ],
    )


def show_state(engine, title):
    banner(title)
    for i, s in enumerate(engine.state.steps, 1):
        verdicts = s.verifications or []
        print(f"  第{i}步 phase={s.phase}｜提交 {len(s.submission or [])} 次｜判定 {len(verdicts)} 次")
        for v in verdicts:
            print(f"     ↳ 判语 by {getattr(v,'verifier','?')}: passed={v.passed} ｜ {str(v.message)[:150]}")
    print(f"  运行阶段 engine.phase = {engine.phase}")


async def stream(engine, inputs):
    """把事件流压成人能读的几行（不然一秒几十条 delta 糊屏）"""
    buf = ""
    async for event in engine.reply_stream(inputs):
        et = type(event).__name__
        if et == "TextBlockDeltaEvent":
            buf += getattr(event, "delta", "") or ""
        elif et == "TextBlockEndEvent" and buf.strip():
            print(f"    {buf.strip()[:300]}")
            buf = ""
        elif et == "ToolCallStartEvent":
            print(f"  [工具调用] {getattr(event,'name','')} {str(getattr(event,'arguments',''))[:160]}")
        elif et == "ToolResultTextDeltaEvent":
            t = getattr(event, "delta", "")
            if t:
                print(f"  [工具结果] {t[:160]}")
        elif et == "ReplyStartEvent":
            print("  · 开始……")


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--park-after", type=int, default=None, help="跑到第 N 步结束即中断并存盘")
    ap.add_argument("--resume", action="store_true", help="从状态文件续跑")
    args = ap.parse_args()

    model, label = build_model()
    sop = build_sop(model)

    banner("D1 · SOP：有序步骤 / 验证者 / 尝试预算 / 断点续跑")
    print(f"模型：{label}")
    print(f"流程：{sop.name}｜共 {len(sop.steps)} 步")
    for i, s in enumerate(sop.steps, 1):
        who = "有验证者（判定不过就退回重写）" if s.verifier else "无验证者（交活即过）"
        print(f"  第{i}步 {s.subject}｜{who}｜尝试预算 {s.max_attempts}")
    print("审稿人硬检查项：")
    for c in CHECKS:
        print(f"  - {c}")

    if args.resume:
        if not STATE_FILE.exists():
            print(f"❌ 没有状态文件 {STATE_FILE}；先跑 `--park-after 1`")
            return
        raw = STATE_FILE.read_text()
        state = SOPRunState.model_validate_json(raw)
        banner("续跑：从状态文件重建引擎（已完成的步骤不重跑）")
        print(f"状态文件：{STATE_FILE}（{len(raw)} 字节）｜运行 id {state.id}｜步骤数 {len(state.steps)}")
        for i, s in enumerate(state.steps, 1):
            print(f"  第{i}步 读档时 phase={s.phase}")
        engine = SOPEngine(sop, state)
        t0 = time.time()
        await stream(engine, None)
        print(f"\n最终阶段：{engine.phase}｜本段用时 {time.time()-t0:.1f}s")
        STATE_FILE.write_text(engine.state.model_dump_json())
        show_state(engine, "续跑结束后的运行状态")
        return

    engine = SOPEngine(sop)
    t0 = time.time()

    if args.park_after:
        # 中断演示：盯住公开状态，第 N 步 phase 变成 completed 就收工
        n = args.park_after
        buf = ""
        async for event in engine.reply_stream(UserMsg(name="user", content=f"写一篇介绍{TOPIC}的短文。")):
            et = type(event).__name__
            if et == "TextBlockDeltaEvent":
                buf += getattr(event, "delta", "") or ""
            elif et == "TextBlockEndEvent" and buf.strip():
                print(f"    {buf.strip()[:300]}")
                buf = ""
            if engine.state.steps[n - 1].phase == SOPPhase.COMPLETED:
                print(f"\n>>> [模拟中断] 第 {n} 步已完成 → 进程在此退出（不往下走）")
                break
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(engine.state.model_dump_json())
        show_state(engine, "中断时的运行状态（这份就是存到磁盘里的东西）")
        print(f"\n状态已存盘：{STATE_FILE}")
        print("※ 下一镜跑 `--resume`，看它从第 2 步接着走，而不是从头再来。")
        return

    await stream(engine, UserMsg(name="user", content=f"写一篇介绍{TOPIC}的短文。"))
    print(f"\n阶段：{engine.phase}｜用时 {time.time()-t0:.1f}s")
    show_state(engine, "运行状态：每一步的提交与判定")
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(engine.state.model_dump_json())
    print(f"\n状态已存盘：{STATE_FILE}")

asyncio.run(main())
