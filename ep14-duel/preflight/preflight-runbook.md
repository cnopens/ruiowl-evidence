# Ep14 对决 · 预跑校准手册

> 对决前先各跑通一遍，验证任务难度落在「一个会话内可完成」区间。
> 太易/太难的任务在正式对决前替换。起草人校准已完成逻辑层（任务可解 + 判据可达），
> 本预跑校准的是 **agent 实际完成情况**（真实耗时、失败模式、陷阱是否过难）。

## 0. 环境检查（一次）

```bash
node -v          # ≥18
pnpm -v          # ≥9（task1/task3 用）
python3 --version  # task2 用：本机 = Homebrew 3.14（EXTERNALLY-MANAGED，pip 直装 pytest 必被拒！）
# task2 的 pytest 一律走仓库内 .venv（preflight.py 安装步自动建好），勿手动 pip install 到系统 python
claude --version # 预跑 claude 侧；dsh 侧在 M5：cd ~/workspace/research/deepseek-harness && pnpm dsh --help
```

## 1. 预跑一个任务

```bash
cd ~/workspace/ruiowl-content/ep14-dsh-vs-claude-code/preflight

# 用法: python3 preflight.py <task> <tool> [--desc 自定义]
#   task: t1 | t2 | t3      tool: claude | dsh

# 示例：claude 预跑 task1（修 bug）
python3 preflight.py t1 claude

# 示例：dsh 预跑 task2（在装有 dsh 的机器上）
python3 preflight.py t2 dsh
```

脚本自动完成：独立 clone（不碰源仓库）→ 装依赖 → headless 跑 agent（60min 超时）
→ 逐条验证判据 → 结果写入 `results/<task>-<tool>-<时间戳>.json` 并打印摘要。

## 2. 每任务判据（脚本自动验证）

| 任务 | 判据 |
|:--|:--|
| t1 修 bug | `pnpm test` 全绿（v2=11 测试 4 红）；git diff 无 test/ 改动；package.json+lockfile 无变化 |
| t2 加功能 | pytest 全绿（基线4+新增，走 `.venv/bin/python`）；`dedupe --help` 展示新命令；内置验收样例通过；**管道兼容**（dedupe 输出可被 parse 消费）；**性能**（10 万行 ≤60s 且输出行数精确） |
| t3 重构 | `pnpm build` + `pnpm test` 4/4；`grep -r ConfigLoader .`（排除 node_modules/.git/dist/pnpm-lock.yaml）零命中 |

## 任务版本说明（9-8 晚 v2 加强区分度）

- v1（8+4+2 红 / dedupe 单判据 / 34 处引用）全部 <4min 完成 → 完成率无区分度，用户拍板加强。
- **t1 v2**：11 测试 4 红（新增单价精度缺校验 + API 畸形 JSON 错误契约，含 HTTP 集成测试），README 陷阱扩至两处。baseline commit `beb91eb`。
- **t2 v2**：仓库不变，判据新增管道兼容 + 10 万行性能硬约束（校准实测 0.1s 完成）。verify 生成风暴日志格式见 preflight.py。
- **t3 v2**：引用面 34→112 处（新增 src/features/* 8 模块 + examples/docs），grep 判据扩至全仓（锁文件除外）。baseline commit `5e4f9b2`。
- v2 校准全部人工验证可达（修复→全绿→reset）；难度冒烟 9-8 晚执行中。

## 3. 指标记录（每任务每轮一张，填进 plan 的指标表）

```
任务 #___  轮次 (1/2)  工具 (dsh/claude)
──────────────┬─────────────┬─────────────
墙钟耗时       │  (json: elapsed_s)
首轮验收       │  脚本输出 FIRST_PASS: yes/no
终态验收       │  脚本输出 FINAL_PASS: yes/no（60min 内达成的最高状态）
违规检查       │  脚本输出 VIOLATIONS: ...（改了测试/新增依赖/残留旧名）
备注           │  陷阱是否被识破？卡点在哪？
```

## 4. 超时救援规则

- agent 跑满 60min 未完成 → 记「未完成」，单列不算失败（plan 风险自查第 4 条）
- 预跑建议把脚本超时调短（如 `--timeout 1800` = 30min）快速看难度

## 5. 公平性红线（预跑同样适用）

- 每次预跑 = 全新 clone，禁止复用上次 agent 改过的目录
- 源仓库（task-repos/ 下）永远保持 baseline 状态，任何 agent 产物不回流
- 两边 headless 参数对齐（都无人工介入）：claude 用 `-p --dangerously-skip-permissions`，dsh 用 `--profile headless`
- 预跑结果不写入对决正式成绩，只用于难度校准

## 6. 校准结论标准

| 结论 | 依据 | 动作 |
|:--|:--|:--|
| ✅ 难度合适 | agent 在 15-40min 内完成且判据全过 | 保留任务 |
| ⚠️ 偏易 | <10min 完成 | 加强埋点或接受（对决时看完成率区分度） |
| 🔴 太难 | 60min 未完成或 agent 反复绕弯 | 简化任务/换题 |

## 7. 坑记录

- **9-8 安装失败被静默吞掉 → 双 agent 假 FAIL**：t2 安装步 `python3 -m pip install pytest`
  在本机（Homebrew python3.14 EXTERNALLY-MANAGED）必失败，而旧版 main() 不查安装 returncode，
  静默继续 → agent 侧自己建临时 venv 自测全绿后清掉、校验侧 pytest 根本没装 → claude(00:05) 与
  dsh(06:41) 两条 t2 结果**一模一样假 FAIL**（pytest_all_green 挂 + help/sample 过 + agent 日志
  提到 externally-managed 临时 venv）。
  修复（9-8 已固化进 preflight.py）：安装步 = 仓库内建 `.venv` 再装 pytest（绕过 PEP 668）；
  任务描述明示 `.venv/bin/python` 为唯一验收环境；verify_t2 全程走 `.venv/bin/python`；
  安装失败 fail-fast 中止并打印 stderr。**结论：t2 那两条结果作废，修后重跑才算数。**
