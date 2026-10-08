# ep17 · AgentScope SOP / 验证者 / 断点续跑（本机演示）

## 这是什么
AgentScope 2.0.9 的三段本机演示：**SOP 里程碑**、**验证者 + 尝试预算**、**TeamPipeline 与断点续跑**，含控制台调试观察。

## 环境
- `local`：M4 本机 · AgentScope 2.0.9 · 百炼（TokenPlan）模型

## 文件
```
demos/demo1_sop.py             SOP：把任务写成有序里程碑（含两步判定的打回/重来）
demos/demo2_team.py            TeamPipeline：谁能被派、结果回到哪
demos/demo3_console.py         终端调试台观察
demos/run.sh                   一键跑
demos/state/demo1_sop_state.json  SOP 状态文件（断点续跑的落盘物）
demos/RUNBOOK.md               复现步骤与依赖
ep17-demo-recording.md         演示素材与运行记录说明（含静帧素材来源）
```

## 状态文件字段
`id` · `inputs` · `steps`（里程碑与判定结果）· `created_at` · `phase`

## 口径
- 这些是**单次运行读数**（不是基准分数），环境写死在上面，换机换版本会变。
- 文章里提到的状态文件字节数与本仓这份**属两次不同运行**（同一脚本、不同输入），数量级一致但不是同一份；要逐字节复现请照 `RUNBOOK.md` 重跑。

## 复现
```bash
cd demos && bash run.sh        # 详见 RUNBOOK.md（需百炼 key 与 agentscope 2.0.9）
```
