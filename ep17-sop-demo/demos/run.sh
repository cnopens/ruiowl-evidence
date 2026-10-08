#!/bin/bash
# ep17 录屏一键脚本（你自己录，我只交手册 + 脚本）
#   用法：./run.sh 1 | 2a | 2b | 3 | 4
#   前置：先执行  source ~/.zshrc   （演示走百炼 TokenPlan，key 在该文件里）
#   注意：必须用 venv 的 python —— 系统 python3 里没装 agentscope
set -u
cd "$(dirname "$0")"

if [ -z "${1:-}" ]; then
  echo "用法：./run.sh 1|2a|2b|3|4"
  echo "  1  = SOP 打回重试      → raw/ep17-demo-sopretry.mp4"
  echo "  2a = 中断存盘          ┐ 合成一个文件"
  echo "  2b = 断点续跑          ┘ → raw/ep17-demo-sopresume.mp4"
  echo "  3  = 团队流水线        → raw/ep17-demo-team.mp4"
  echo "  4  = 全屏终端界面      → raw/ep17-demo-tui.mp4"
  echo "前置：先执行 source ~/.zshrc（key 在该文件里，脚本不打印）"
  exit 2
fi

if [ -z "${DASHSCOPE_API_KEY:-}" ]; then
  echo "❌ 环境变量里没有 DASHSCOPE_API_KEY（脚本不打印它的值）"
  echo "   先执行：source ~/.zshrc   然后再跑本脚本"
  exit 1
fi

V="$HOME/workspace/agentscope-test/.venv/bin/python"
[ -x "$V" ] || { echo "❌ 找不到 venv python：$V"; exit 1; }

case "${1:-}" in
  1)   echo "▶ 片段 1 · SOP 打回重试（拍到这里存 raw/ep17-demo-sopretry.mp4）"; exec "$V" demo1_sop.py ;;
  2a)  echo "▶ 片段 2 上 · SOP 跑到一半中断存盘（记下屏幕上的「已存盘」那两行）"; exec "$V" demo1_sop.py --park-after 1 ;;
  2b)  echo "▶ 片段 2 下 · 断点续跑（只跑第 2 步）"; exec "$V" demo1_sop.py --resume ;;
  3)   echo "▶ 片段 3 · 团队流水线（派活 → 只回结果 → token 合计）"; exec "$V" demo2_team.py ;;
  4)   echo "▶ 片段 4 · 全屏终端界面（需真 TTY，SSH 也行）"; exec "$V" demo3_console.py ;;
  *)   echo "❌ 未知参数：$1（用法：./run.sh 1|2a|2b|3|4）"; exit 2 ;;
esac
