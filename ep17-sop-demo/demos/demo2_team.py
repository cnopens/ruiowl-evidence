#!/usr/bin/env python3
"""D2 · 团队流水线（ep17 真机演示 2）

演示内容：
  1. 一个 leader + 两个成员（研究员 / 写手），leader **通过工具调用派活**（TeamAssign）
  2. 每个成员在**自己的上下文**里干活；回到 leader 的**只有结果**
     —— 屏幕上「派活」与「回结果」分开打，观众能直接看到 results only
  3. 顺带把每次模型调用的 **token 数** 打出来（呼应第四章「算得起账」）

用法（M4）：
    source ~/.zshrc
    ~/workspace/agentscope-test/.venv/bin/python demo2_team.py
模型：百炼 TokenPlan / qwen3.8-max（无 key 时回落本机 Ollama）
"""
import asyncio
import os
import time

from agentscope.agent import Agent
from agentscope.message import UserMsg
from agentscope.model import DashScopeChatModel, OllamaChatModel
from agentscope.credential import DashScopeCredential, OllamaCredential
from agentscope.pipeline import TeamMember, TeamPipeline
from agentscope.tool import Toolkit

TASK = "评估一件小事：我们要不要给团队引入一个每周自动汇总的机器人？先摸清事实，再给出结论。"
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
            ck["base_url"] = TOKENPLAN_BASE
        return DashScopeChatModel(credential=DashScopeCredential(**ck), model=name), f"百炼 / {name}"
    name = os.getenv("DEMO_MODEL", "qwen2.5-coder:7b")
    return OllamaChatModel(credential=OllamaCredential(), model=name), f"本机 Ollama / {name}"


async def main():
    model, label = build_model()
    banner("D2 · 团队流水线 —— leader 派活，成员各自干活，只回结果")
    print(f"模型：{label}\n任务：{TASK}\n")

    leader = Agent(
        name="Leader",
        system_prompt=(
            "你是小团队的负责人，只管派活、看结果、给结论："
            "自己不查资料、不写正文。先派研究员摸事实，再派写手成稿，最后给出你自己的结论。"
        ),
        model=model,
        toolkit=Toolkit(),                       # leader 必须有 toolkit：TeamAssign 注册在这里
    )
    researcher = Agent(
        name="Researcher",
        system_prompt="你是研究员。只给事实与不确定处，简明分点，不写结论。",
        model=model,
    )
    writer = Agent(
        name="Writer",
        system_prompt="你是写作者。基于拿到的材料写成三句话以内的结论，不新增未经核实的事实。",
        model=model,
    )
    members = [
        TeamMember(agent=researcher, description="梳理事实与不确定处。"),
        TeamMember(agent=writer, description="把材料写成简短结论。"),
    ]
    pipe = TeamPipeline(leader=leader, members=members)

    print("成员名册（leader 看到的就是这份描述，用来决定派给谁）：")
    for m in members:
        print(f"  - {m.agent.name}：{m.description}")
    print("\n" + "-" * 78)
    print("  运行实录")
    print("-" * 78)

    t0 = time.time()
    tok_in = tok_out = 0
    pending_assign = None
    argbuf = ""
    async for ev in pipe.reply_stream(UserMsg(name="user", content=TASK)):
        et = type(ev).__name__
        d = ev.model_dump() if hasattr(ev, "model_dump") else {}

        if et == "ToolCallStartEvent":
            pending_assign = d.get("tool_call_name", "?")
            argbuf = ""
            print(f"\n  ▶ [leader 派活] {pending_assign}")
        elif et == "ToolCallDeltaEvent":
            argbuf += (d.get("delta") or "")
        elif et == "ToolCallEndEvent":
            if pending_assign and argbuf.strip():
                print(f"     指派内容：{argbuf.strip()[:400]}")
            pending_assign, argbuf = None, ""
        elif et == "ToolResultStartEvent":
            print(f"  ◀ [执行 {d.get('tool_call_name','')}] 成员开始干活（在它自己的上下文里）")
        elif et == "ToolResultTextDeltaEvent":
            txt = (d.get("delta") or "").strip()
            if txt:
                print(f"  ◀ [成员回给 leader 的只有结果] {txt[:300]}")
        elif et == "ModelCallEndEvent":
            tok_in += int(d.get("input_tokens") or 0)
            tok_out += int(d.get("output_tokens") or 0)
            print(f"      · 本轮模型调用：输入 {d.get('input_tokens')} / 输出 {d.get('output_tokens')} tokens")
        elif et == "TextBlockEndEvent":
            txt = (d.get("text") or "").strip()
            if txt and txt != "None":
                print(f"\n      [leader 文本] {txt[:300]}")

    print("\n" + "-" * 78)
    print(f"  用时 {time.time()-t0:.1f}s｜token 合计 输入 {tok_in} / 输出 {tok_out}")
    print("  注：成员的中间推理与工具调用没有回到 leader 的上下文 —— 官方写的 results only。")
    print("      这几个 token 数就是第四章说的「账」：分工不是为了好看，是为了让主线别被过程撑爆。")


asyncio.run(main())
