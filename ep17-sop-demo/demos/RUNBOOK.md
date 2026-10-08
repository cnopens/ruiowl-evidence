# ep17 真机演示 · 操作手册（远程可用）

> 面向：**你自己操作录屏**（可远程 SSH 到 M4）。我只交手册 + 脚本，不反复试跑。
> 环境已在本机**实测跑通**（2026-09-29 10:40–10:55），不是纸面步骤。
> 目录：`~/workspace/ruiowl-content/ep17-agentscope-ep6/demos/`

---

## 0. 环境状态（已就绪，不用再装）

| 项 | 状态 |
|:--|:--|
| AgentScope | **2.0.9**（已升级，装在 `~/workspace/agentscope-test/.venv`，Python 3.11.15） |
| TUI 支持 | 已装 `agentscope[tui]`（textual 8.2.8）→ `agentscope.tui` 可导入 |
| 模型 | **百炼 TokenPlan / qwen3.8-max**（token-plan 域） |
| 密钥 | 在 `~/.zshrc`（`sk-sp-` 开头 = TokenPlan key）→ **每次开新终端先 `source ~/.zshrc`** |
| 备用模型 | 本机 Ollama `qwen2.5-coder:7b`（离线可用，但慢很多、结构化输出不稳，仅兜底） |

⚠️ **TokenPlan key 必须走 token-plan 域**：`https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1`。
脚本里已自动判别（`sk-sp-` 前缀即切域）——之前 401 就是因为 key 打在标准 `dashscope.aliyuncs.com` 上。
⚠️ 录屏时**不要**把 `echo` 密钥的命令录进去（脚本从不打印密钥）。

```bash
# 每个新终端的第一步
source ~/.zshrc
V=~/workspace/agentscope-test/.venv/bin/python
cd ~/workspace/ruiowl-content/ep17-agentscope-ep6/demos
```

---

## 1. D1 · SOP 三步走（对应第一章）——**分三镜录**

| 镜 | 命令 | 预期输出/用时 | 录屏要点 |
|:--|:--|:--|:--|
| ① 完整跑一遍 | `$V demo1_sop.py` | 步骤推进 + **第1次判定 passed=False** + 第2次通过；约 20–40s | 让「判定 2 次」这一行停在屏幕上 |
| ② 中断存盘 | `$V demo1_sop.py --park-after 1` | 打 `>>> [模拟中断] 第 1 步已完成 → 进程在此退出`；第2步 phase=**pending**；状态写到 `state/demo1_sop_state.json` | 停在「第2步 phase=pending / engine.phase=running」 |
| ③ 续跑 | `$V demo1_sop.py --resume` | 从状态文件重建引擎，**只跑第 2 步**（约 6s），最终 completed | 停在「第1步读档时 phase=completed」那一行——这就是「不重跑」的证据 |

**必须如实说明的一点（写进旁白）**：审稿人的 system prompt 里写了「**第 1 次审稿一律不通过**」——这是我们为了在同一镜里看到「打回 → 带意见重试」路径而**故意设严**的（真实使用中由判据决定过不过）。脚本注释与输出里都有标注，视频里说一句即可，别当成"模型自己打回"。

---

## 2. D2 · 团队流水线（对应第二章）

```bash
$V demo2_team.py
```
- 用时实测 **40.7s**；输出里能看到：`▶ [leader 派活] TeamAssign` 两次（先 Researcher 后 Writer）→ `◀ [成员回给 leader 的只有结果]` → 每轮模型调用的 token 数 → 最后 token 合计。
- 录屏要点：让「派活」和「回结果」两行连续出现（这就是 results only 的可视证据）；token 那一行留 2–3 秒（对应第四章「算得起账」）。
- 材料：`图：leader → 成员 → 结果` 的流向图（我出场景卡时一起给）。

---

## 3. D3 · 全屏终端界面（对应第四章）

```bash
$V demo3_console.py          # 单 agent 对话
$V demo3_console.py --team   # 团队流水线在 TUI 里跑
```
- 这是**交互式**界面：进去后自己问一句即可（例如「AgentScope 2.0.9 的 SOP 是干什么的，一句话」）。
- 远程 SSH 下也能跑（真 TTY）。**退出**：`Ctrl+C`。
- 录屏建议：终端**全屏 + 字号不小于 16**，黑底；录 15–25s 足够。
- 语音会话（`launch_realtime_ui`）**本轮不录**：需要麦克风与实时 API 凭证，机器上没有；脚本里不做假。

---

## 4. 收工与归档

```bash
# 演示产出（状态文件、日志）留在 demos/ 下，勿删：续跑那一镜依赖 state/demo1_sop_state.json
ls -l ~/workspace/ruiowl-content/ep17-agentscope-ep6/demos/state/
```
录好的屏请放到：`~/workspace/ruiowl-content/ep17-agentscope-ep6/recordings/`（目录我建好，文件名建议 `d1-full.mov` / `d1-park.mov` / `d1-resume.mov` / `d2-team.mov` / `d3-tui.mov`）。

---

## 5. 出问题时的判据（别硬试）

| 现象 | 判据/处置 |
|:--|:--|
| `AuthenticationError 401` | key 打错域。确认 `$DASHSCOPE_API_KEY` 是 `sk-sp-` 开头 → 脚本会自动走 token-plan 域；若仍 401，说明 key 过期 |
| `429` 持续 | TokenPlan 配额问题 → 停，别空烧；改用 Ollama 兜底 |
| `ModuleNotFoundError: agentscope.tui` | 重装：`UV_HTTP_TIMEOUT=120 uv pip install --python ~/workspace/agentscope-test/.venv/bin/python "agentscope[tui]==2.0.9"` |
| 第 2 步续跑报 `ValueError` | 状态文件与流程定义不一致（步骤数变了）→ 删 `state/demo1_sop_state.json` 重跑 ② |
| 输出乱、卡住 | 先 `Ctrl+C`；再跑一次（模型偶发抖动，非脚本问题） |
