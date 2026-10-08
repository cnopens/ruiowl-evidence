# ep17 演示素材：从「录屏」改为「终端静帧」（2026-09-29 定）

## 结论（用户决定：统一做静帧）
四段演示**全部用终端静帧卡**，不用录屏视频片段。理由：关键信息一帧看全、无等待无鼠标干扰、时长按旁白为准更稳。

## 素材来源
- 录屏原件（已归档）：`raw/ep17-full-take-1434.mov`（197s，桌面原件同名，2026-09-29 14:34:26）
- 抽帧静帧：`raw/stills/term_{sopretry,sopresume,team,tui}.png`（2032px 宽，已裁掉窗口标题栏）

## 时间点映射（取自上述录屏）
| 静帧 | 录屏时间点 | 卡号 | 关键信息 |
|:--|:--|:--|:--|
| `term_sopretry.png` | t=56s | `scene_15.png` | 判定 2 次：passed=False（打回）→ passed=True；整段 23.9s；状态已存盘 |
| `term_sopresume.png` | t=72s | `scene_16.png` | 状态文件 2,688 字节 · 已恢复 1 步；本次只跑第 2 步 9.7s |
| `term_team.png` | t=120s | `scene_17.png` | leader 派活 2 次 → 成员只回结果；39.6s；token 输入 4,249 / 输出 1,635 |
| `term_tui.png` | t=196s | `scene_18.png` | TUI 问答节选：**只保留「SOP 是什么？做什么用的？」这段**（提问行写着旧版本号 2.0.7，且模型在版本问题上回避——「无法准确列出该假设版本的最新特性」，故整段裁掉，不出现版本号讨论） |

## 复现命令
```bash
cd ~/workspace/ruiowl-content/ep17-agentscope-ep6
# 1) 抽静帧（可换时间点重取）
/usr/bin/python3 ~/.hermes/scripts/grab_term_still.py raw/ep17-full-take-1434.mov 56 raw/stills/term_sopretry.png
# 2) 生成卡片（1920×1080，含标题/底注/窗口边框）
/usr/bin/python3 gen_term_cards.py
# 3) 重合成（scene_map.json 是唯一真源，其中已无 demo 录屏引用）
/usr/bin/python3 compose.py --out draft3
```

## 注意
- `scene_map.json` 的 `demo` 字段：**当前全部为空**（统一静帧）。若将来某段改回视频片段，把片段放 `raw/ep17-demo-<tag>*.mp4|.mov` 并在对应 item 加 `"demo": "<tag>"` 即可（compose 会自动用片段并以其时长为准）。
- 静帧卡文案与旁白口径一致：D1 审稿人 prompt 是故意设「第 1 次一律不通过」，视频中必须说明，不得表述成模型自己打回。
- 助手（我）复核时间：2026-09-29 15:0x；成片 `output/ep17-draft3.mp4`（5:44.4，音画差 0.04s，QA 四关全绿）。
