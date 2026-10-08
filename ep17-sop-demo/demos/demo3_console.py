#!/usr/bin/env python3
"""D3 · 全屏终端界面（ep17 真机演示 3）

演示内容：`agentscope.tui` / console —— 直接在终端里起一个 agent（或整条团队流水线）对话。
录屏要点：全屏终端（字号调大、关闭无关窗口），让它自然跑一遍即可。

用法（M4，交互式终端里跑；远程 SSH 也可以）：
    source ~/.zshrc
    V=~/workspace/agentscope-test/.venv/bin/python
    $V demo3_console.py            # 单 agent 对话
    $V demo3_console.py --team     # 团队流水线（leader + 研究员 + 写手）在终端里跑
退出：TUI 里的退出键（通常是 Ctrl+C / Ctrl+D）
"""
import asyncio
import os
import sys

from agentscope.agent import Agent
from agentscope.console import launch_console
from agentscope.model import DashScopeChatModel, OllamaChatModel
from agentscope.credential import DashScopeCredential, OllamaCredential
from agentscope.pipeline import TeamMember, TeamPipeline
from agentscope.tool import Toolkit

TOKENPLAN_BASE = "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"


def build_model():
    key = os.getenv("DASHSCOPE_API_KEY", "")
    if key:
        name = os.getenv("DEMO_MODEL", "qwen3.8-max")
        ck = {"api_key": key}
        if key.startswith("sk-sp-"):
            ck["base_url"] = TOKENPLAN_BASE
        return DashScopeChatModel(credential=DashScopeCredential(**ck), model=name)
    return OllamaChatModel(credential=OllamaCredential(), model=os.getenv("DEMO_MODEL", "qwen2.5-coder:7b"))


async def main():
    model = build_model()
    if "--team" in sys.argv:
        leader = Agent(name="Leader", system_prompt="你是负责人，只管派活、看结果、给结论。", model=model, toolkit=Toolkit())
        researcher = Agent(name="Researcher", system_prompt="你是研究员，给事实与不确定处。", model=model)
        writer = Agent(name="Writer", system_prompt="你是写作者，给简短结论。", model=model)
        pipe = TeamPipeline(
            leader=leader,
            members=[
                TeamMember(agent=researcher, description="梳理事实与不确定处。"),
                TeamMember(agent=writer, description="把材料写成简短结论。"),
            ],
        )
        await launch_console(agent=pipe)
    else:
        agent = Agent(
            name="Assistant",
            system_prompt="你是一位技术助教，用中文简短回答，必要时说明不确定处。",
            model=model,
        )
        await launch_console(agent=agent)


asyncio.run(main())
