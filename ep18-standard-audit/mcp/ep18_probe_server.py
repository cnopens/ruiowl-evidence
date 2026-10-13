#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ep18 T7 共享 MCP 探针服务器（stdio, newline-delimited JSON-RPC 2.0）

为什么自己写而不装现成 server：
  1) 离线可复现，不依赖 npm/civitai 网络；
  2) 所有 runner 吃到的是**同一个 server、同一份字节**（公平性）；
  3) 工具返回固定 token，用来证明「agent 真的走了 MCP，而不是嘴上说接了」。

工具：
  ep18_probe()  -> 固定 token EP18-MCP-OK-<sha8>
  ep18_echo(text) -> 回显
"""
import hashlib
import json
import sys

TOKEN = "EP18-MCP-OK-" + hashlib.sha256(b"ep18-t7-probe").hexdigest()[:8]
PROTO = "2024-11-05"

TOOLS = [
    {
        "name": "ep18_probe",
        "description": "ep18 T7 探针：调用它可证明 MCP 通道已接通。返回固定 token。",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "ep18_echo",
        "description": "回显传入的文本（用于验证带参数的 MCP 工具调用）。",
        "inputSchema": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
    },
]


def reply(rid, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": rid}
    if error is not None:
        msg["error"] = error
    else:
        msg["result"] = result
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            continue
        method = req.get("method")
        rid = req.get("id")
        if method == "initialize":
            reply(rid, {
                "protocolVersion": PROTO,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "ep18-probe", "version": "1.0.0"},
            })
        elif method == "notifications/initialized":
            continue
        elif method == "tools/list":
            reply(rid, {"tools": TOOLS})
        elif method == "tools/call":
            params = req.get("params") or {}
            name = params.get("name")
            args = params.get("arguments") or {}
            if name == "ep18_probe":
                text = TOKEN
            elif name == "ep18_echo":
                text = "echo: " + str(args.get("text", ""))
            else:
                reply(rid, error={"code": -32601, "message": f"unknown tool {name}"})
                continue
            reply(rid, {"content": [{"type": "text", "text": text}], "isError": False})
        elif method == "ping":
            reply(rid, {})
        elif rid is not None:
            reply(rid, error={"code": -32601, "message": f"method not found: {method}"})


if __name__ == "__main__":
    main()
