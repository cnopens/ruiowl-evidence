# M2-b 第二批（key_points + evidence_facts）落库报告

> 执行：2026-10-03（本地 M4 Mac mini，colima 容器 `ruiowl-db`）｜分支 `v2`
> 依据：用户 2026-10-03 对 dry-run 清单六项「都按推荐进行」｜`docs/harness-report-M2b2-dryrun.md`
> 铁律执行情况：**线上零改动**（对生产只做只读查询；生产迁移仍未执行）

## 状态

**完成（本地库已落库 + 逐项对账 0 不一致）** ｜ 生产库迁移（001 → 002 → 003）仍待切换窗口，需用户点头。

## 做了什么

1. **写迁移 `003_key_points.sql`**：`knowledge_nodes` 加 `key_points JSONB NOT NULL DEFAULT '[]'`（只加不改）+ 1 条 CHECK（上限 5 条 / 必须是数组）+ 回滚块；**幂等**（连跑两遍，第二遍 `already exists, skipping`）。
2. **拍板前备份**：`pg_dump -Fc` → `m2b2-dryrun/backup/local-pre-m2b2-1003-1201.dump`（316,894 B）；**并在 scratch 库真恢复一次验证备份可用**（约 1 分钟后清理）。
3. **写回填脚本 `scripts/backfill_m2b2.py`**（`--dry-run` / `--apply` / `--verify`）：key_points 逐节点「整列赋值」（幂等）；`evidence_facts` 先按 27 节点 DELETE 再 INSERT（幂等）；日期不可考的行**主动跳过**并进清单。
4. **本地执行 + 三项对账**：迁移 → apply → `--verify`（key_points 逐节点全等 + evidence_facts 逐行全等）→ 约束探针 → 老数据指纹 → 幂等复跑。
5. **落地第⑥条**：ep15（node 42）的要点**改用冻结样张原文**——脚本从 `docs/design/p2-hybrid/episode.html` 的 `.points` 列表里现场提取（不硬编码），5 条与你微调过的版本逐字一致。
6. **出补齐清单**：`docs/m2b2-gap-list.md`（原始记录待公开 / 缺日期未落库 / 其余缺证据项）。

## 证据（可复跑）

| 项 | 命令 | 结果 |
|:--|:--|:--|
| 迁移幂等 | 同一份 `003` 连跑两次 | 两次 `COMMIT`；第二次 `NOTICE: column "key_points" … already exists, skipping` |
| 备份可恢复 | 恢复进 scratch 库后 `count(*)` | 50 行、指纹与原库一致；恢复演练后清理 |
| apply | `python3 scripts/backfill_m2b2.py --apply` | **27 节点 key_points / 64 行 evidence_facts**（跳过 6 行：日期不可考） |
| 逐项对账 | `python3 scripts/backfill_m2b2.py --verify` | **不一致 0 处**（key_points 122 条逐节点全等；evidence_facts 64 行逐字段全等） |
| 幂等复跑 | 再跑一次 `--apply` + `--verify` | 仍 **0 处不一致** |
| 老数据未动 | 全表指纹 `md5(string_agg(id\|slug\|parent_id\|category\|md5(content_md)\|published\|title))` | 落库前（备份库）与落库后**均 `9809bf2af219e985bc977cacd64b2325`** |
| 约束探针·超 5 条 | `UPDATE … key_points='["1".."6"]'` | ❌ 被拒 `ck_nodes_key_points` |
| 约束探针·非数组 | `UPDATE … key_points='{"a":1}'` | ❌ 被拒 `ck_nodes_key_points` |
| 约束探针·合法 | `UPDATE … key_points='["1","2"]'` | ✅ `UPDATE 1`（随后用幂等 apply 复原） |
| 约束探针·env 非法 | `INSERT evidence_facts … env='bogus'` | ❌ 被拒 `evidence_facts_env_check` |
| 约束探针·无日期 | `INSERT evidence_facts … measured_at 省略` | ❌ 被拒 `not-null constraint` |

## 落地分布

| kind | 节点 | 本期要点 | 关键实测数据 |
|:--|--:|--:|--:|
| episode（期） | 13 | 61 条 | 39 行 |
| article（早期文章） | 14 | 61 条 | 25 行 |
| **合计** | **27** | **122 条** | **64 行** |

- 有实测数据的节点 **11 个**（对决篇 10 行、权限边界 10 行、OCReS 2 行、DSH Ep5 8 行、AgentScope Ep6 6 行、早期横评 23 行等）。
- **16 个节点无自测数据** → 按拍板②**不落 sentinel 行**，页面侧显式写「本期无新增实测」（渲染口径，M3 落地）。
- `evidence_facts.raw_url` **全部 NULL**（拍板④）。取代它的是 `docs/m2b2-gap-list.md` 的 A 项：**哪一行、靠哪份本地原始记录支撑，逐条列明**（其中 ep14 的 12 份 run json + 2 份日志、ep15 的 30 份 run json、ep16 census json 等磁盘均已确认存在）。
- 论文/第三方数字**一条未进库**（拍板⑤）：R-SWA 的 500M vs 235B、FlashAttention 论文加速比、ep19 GitHub star 数等，全部留在 `sources` 表与缺证据项说明里。

## 六项拍板落地对照

| # | 拍板 | 落地 |
|:--|:--|:--|
| ① | key_points 取 JSONB 数组 | `003` 已落；探针证明「数组 + ≤5」被强制 |
| ② | 无自测数据不造 sentinel，页面显式写 | 16 个节点 `evidence_facts` 为空数组；口径写入补齐清单与本文档 |
| ③ | 只落日期可考的行 | 跳过 6 行（OCReS 本地 M5，正文未标日期）→ 补齐清单 B 项待你一句话 |
| ④ | raw_url 一律 NULL + 待公开清单 | 64 行全 NULL；清单 A 项逐行列明原始记录 |
| ⑤ | 论文/第三方数字不进 evidence_facts | 0 条混入；已在缺证据项里逐条说明去向 |
| ⑥ | ep15 用冻结样张原文 | node 42 的 5 条要点 = 样张 `.points` 原文（脚本现场提取）；并**补 1 行**「有效运行 30 次（3 模型 × 2 臂 × N=5）」以支撑样张的数据块（依据正文 §4 首段原文，非编造） |

## 变更面

| 类型 | 内容 |
|:--|:--|
| 迁移 | `backend/migrations/003_key_points.sql`（新增列 + 1 约束 + 回滚块） |
| 脚本 | `scripts/backfill_m2b2.py` · `m2b2_export_sources.py` · `m2b2_manifest.py` · `m2b2_verify.py` · `m2b2_report.py` · `m2b2_gap_list.py` |
| 数据（本地库） | `knowledge_nodes.key_points` 27 行（122 条）· `evidence_facts` 64 行；**老列/老行未动**（指纹一致） |
| 文档 | `docs/harness-report-M2b2-dryrun.md` · 本报告 · `docs/m2b2-gap-list.md` |
| 未动 | 线上任何东西；旧 `frontend/`；`web/` 渲染层 |

## 回滚方式

```bash
# 数据级（回到落库前）
docker cp m2b2-dryrun/backup/local-pre-m2b2-1003-1201.dump ruiowl-db:/tmp/pre.dump
docker exec ruiowl-db psql -U ruiowl -d postgres -c "DROP DATABASE IF EXISTS ruiowl;" -c "CREATE DATABASE ruiowl OWNER ruiowl;"
docker exec ruiowl-db pg_restore -U ruiowl -d ruiowl --no-owner --no-acl /tmp/pre.dump
# DDL 级（只撤本次新增）
#   ALTER TABLE knowledge_nodes DROP CONSTRAINT IF EXISTS ck_nodes_key_points;
#   ALTER TABLE knowledge_nodes DROP COLUMN IF EXISTS key_points;
#   DELETE FROM evidence_facts;
```
（备份可恢复性已在 scratch 库演练过。）

## 未做的事（明确列出）

1. **生产库未执行任何迁移**：`001`（access）/ `002`（内容模型）/ `003`（key_points）均只在本地验过；切换顺序必须是 **001 → 002 → 003**。
2. **后端接口未加字段**：`/api/v1/knowledge/` 与单篇接口还没有 `key_points`，也没有 `evidence` 只读接口——属 **M3 渲染层**（期页「本期要点」「关键实测数据」块换真内容、`/evidence` 证据索引页）。
3. **6 行缺日期未落库**、**原始记录未公开**、**16 期「无新增实测」文案**——见 `docs/m2b2-gap-list.md`，等你一句话即可补。
