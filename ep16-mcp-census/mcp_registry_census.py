#!/usr/bin/env python3
"""mcp_registry_census.py — 直接抓官方 MCP registry 全量，自己算口径（不引三方数字）

输出：ep16-mcp-census.json（计数 + 分布），并打印摘要。
口径与 ep16 数据卡一致：唯一服务端数 / 版本行数 / 发布者分布 / 单版本占比 / 远程无认证占比。
"""
import json
import time
import urllib.request
from collections import Counter

OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
BASE = "https://registry.modelcontextprotocol.io/v0/servers?limit=100"


def get(url, tries=3):
    for i in range(tries):
        try:
            with OPENER.open(url, timeout=40) as r:
                return json.loads(r.read().decode())
        except Exception as e:                                    # noqa: BLE001
            if i == tries - 1:
                raise
            time.sleep(2)
    return {}


def main():
    rows, cursor, pages = [], None, 0
    while True:
        url = BASE + (f"&cursor={cursor}" if cursor else "")
        d = get(url)
        servers = d.get("servers", [])
        rows.extend(servers)
        pages += 1
        cursor = (d.get("metadata") or {}).get("nextCursor")
        if pages % 20 == 0:
            print(f"  … {pages} 页 / {len(rows)} 行", flush=True)
        if not cursor or not servers:
            break
        time.sleep(0.15)

    ver_by_name = Counter()
    publishers = Counter()
    remotes_total = remotes_no_auth = remotes_any_auth_field = 0
    versions_per_server_max = Counter()
    for row in rows:
        s = row.get("server", {})
        name = s.get("name", "")
        ver_by_name[name] += 1
        publishers[name.split("/")[0] if "/" in name else name] += 1
        if s.get("remotes"):
            remotes_total += 1
            hdrs = [h for r in s["remotes"] for h in (r.get("headers") or [])]
            names = " ".join(str(h.get("name", "")).lower() for h in hdrs)
            if "authorization" in names or "auth" in names or "token" in names or "key" in names:
                remotes_any_auth_field += 1
            else:
                remotes_no_auth += 1

    counts = sorted(ver_by_name.values())
    med = counts[len(counts) // 2] if counts else 0
    one_version = sum(1 for c in counts if c == 1)
    out = {
        "fetched_pages": pages,
        "version_rows": len(rows),
        "unique_servers": len(ver_by_name),
        "unique_publishers": len(publishers),
        "median_versions_per_server": med,
        "servers_with_single_version": one_version,
        "single_version_share": round(one_version / len(ver_by_name), 4) if ver_by_name else None,
        "top10_publisher_share": round(sum(c for _, c in publishers.most_common(10)) / len(rows), 4) if rows else None,
        "largest_publisher": publishers.most_common(1),
        "remote_capable_servers": remotes_total,
        "remote_without_auth_field": remotes_no_auth,
        "remote_without_auth_share": round(remotes_no_auth / remotes_total, 4) if remotes_total else None,
        "snapshot_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with open("ep16-mcp-census.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    print("CENSUS_DONE")


if __name__ == "__main__":
    main()
