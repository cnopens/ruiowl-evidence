# ep14 · DeepSeek Harness 对决 Claude Code（12 场统一模型实测）

## 这是什么
同一个模型、同一份任务、同一句话描述下，比较 **dsh（DeepSeek Harness）** 与 **Claude Code** 两个 harness 的表现：**3 个任务 × 2 个工具 × 2 轮 = 12 场**。

## 环境
- `local`：本机 Mac（无头运行：dsh 走 `--profile headless`，claude 走 `-p`，全程无人工介入）

## 任务（见 `plan-ep14-duel-tasks.md`）
| 任务 | 类型 | 仓库 | 考点 |
|:--|:--|:--|:--|
| t1 | 修 bug | `task-repos/task1-invoice-api` | 信测试还是信文档（埋了「文档陷阱」） |
| t2 | 加功能 + 补测试 | `task-repos/task2-log-processor` | 需求完整性 + 不破坏存量 |
| t3 | 跨文件重构 | `task-repos/task3-config-lib` | 大面机械替换 + 零残留 |

## 文件
```
preflight/results/*.json       每场一条记录（正式轮 + 校准期存档 archive-calibration-0908/）
preflight/results/duel-*.log   正式轮全程日志（两轮、含时间戳）
preflight/duel-run.sh          跑法脚本
preflight/preflight-runbook.md 跑前检查与流程
plan-ep14-duel-tasks.md        三个任务的题目与判据定义
task-repos/                    三个中立任务仓库（不含任何指向 dsh / Claude / Anthropic 的痕迹）
```

## 字段（`*.json`）
| 字段 | 含义 |
|:--|:--|
| `task` / `tool` | 任务（t1/t2/t3）／工具（`dsh` / `claude`） |
| `started` / `elapsed_s` | 开始时刻／该场耗时（秒） |
| `timed_out` | 是否触到超时上限（3600s） |
| `verdict.violations` | 违规项（改测试/改依赖/越目录等，空数组=无） |
| `verdict.test_tail` | 判据跑完的测试输出尾部 |
| `final_pass` | 判据是否全过 |
| `agent_log_tail` | 该场 agent 自述的收尾片段 |

## 口径
- **A-B-B-A 两轮，两轮都留**：不挑好看的那次；波动幅度见文章 §4。
- `archive-calibration-0908/` 是**校准期**记录（当时还是双变量，不计入正式结论），保留作留痕。
- 结论只针对「这一份任务集 + 本机 + 无头模式」，不外推。

## 复现
```bash
cd preflight
bash duel-run.sh          # 详见 preflight-runbook.md（依赖：node/pnpm、claude CLI、dsh）
```
