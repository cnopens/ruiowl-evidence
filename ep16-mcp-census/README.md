# ep16 · MCP Registry 全量快照统计

## 这是什么
对官方 MCP registry 做的一次**全量抓取**，用来回答「这个生态到底有多大、治理问题在哪」。

## 文件
```
mcp_registry_census.py   抓取 + 统计脚本（唯一入口）
ep16-mcp-census.json     统计结果（快照时刻写在 snapshot_utc 里）
census.log               抓取日志
```

## 结果字段（`ep16-mcp-census.json`）
| 字段 | 含义 |
|:--|:--|
| `fetched_pages` / `version_rows` | 抓取页数 / 版本行数 |
| `unique_servers` / `unique_publishers` | 去重服务端数 / 发布者数 |
| `median_versions_per_server` / `servers_with_single_version` / `single_version_share` | 单版本服务器占比（生态碎片化） |
| `top10_publisher_share` / `largest_publisher` | 头部集中度 |
| `remote_capable_servers` / `remote_without_auth_field` / `remote_without_auth_share` | 远端可达服务端中**未声明鉴权字段**的占比 |
| `snapshot_utc` | 快照时刻（UTC） |

## 口径（重要）
- 这是**某一时刻的快照**：官方源一直在变，跨时点**不可直接比**（要比重跑一次）。
- 与第三方统计（例如「30,375 个 server」）**筛选口径与时点不同，不混比**。
- 「未声明鉴权字段」≠「没有鉴权」，只说明清单里没写；结论以文章口径为准。

## 复现
```bash
python3 mcp_registry_census.py     # 需公网；重跑即得新快照（snapshot_utc 会变）
```
