#!/bin/bash
# Ep14 正式对决执行器：3 任务 × 2 工具 × 2 轮（ABBA 交叉先手）
# 用法: bash duel-run.sh [超时秒数]   # 默认 3600 = 60min（按 plan 救援规则）
# 每轮独立 fresh clone → headless agent → 判据验证 → JSON 落 results/，全程无人介入
set -u
cd "$(dirname "$0")" || exit 2
TIMEOUT=${1:-3600}
LOG="results/duel-$(date +%Y%m%d-%H%M%S).log"
exec > >(tee -a "$LOG") 2>&1
echo "===== Ep14 正式对决开始 $(date '+%F %T') 超时=${TIMEOUT}s ====="

run() { # $1=轮次  $2=task  $3=tool
  echo; echo "########## [R$1] $2 $3 —— $(date '+%T') ##########"
  python3 preflight.py "$2" "$3" --timeout "$TIMEOUT"
  echo ">>> $2 $3 R$1 exit=$?"
}

for t in t1 t2 t3; do
  run 1 "$t" dsh;    run 1 "$t" claude   # 轮1：dsh 先手
  run 2 "$t" claude; run 2 "$t" dsh      # 轮2：claude 先手 → 每任务顺序 = A B B A
done

echo; echo "===== 对决结束 $(date '+%F %T') | 完整日志: $LOG ====="
