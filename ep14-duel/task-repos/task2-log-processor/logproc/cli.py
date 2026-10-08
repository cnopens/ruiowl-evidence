"""log-processor command line interface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import count_levels, read_entries

EPILOG = "exit code 0 on success; 2 on usage errors; 1 on file errors"


def _load(path_str: str) -> Path:
    path = Path(path_str)
    if not path.is_file():
        raise FileNotFoundError(f"no such file: {path}")
    return path


def cmd_parse(args: argparse.Namespace) -> int:
    path = _load(args.file)
    entries, _ = read_entries(path)
    for entry in entries:
        print(json.dumps({
            "ts": entry.timestamp,
            "level": entry.level,
            "message": entry.message,
        }, ensure_ascii=False))
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    path = _load(args.file)
    entries, malformed = read_entries(path)
    counts = count_levels(entries)
    for level in ("DEBUG", "INFO", "WARN", "ERROR"):
        print(f"{level}: {counts.get(level, 0)}")
    print(f"total: {len(entries)}")
    if malformed:
        print(f"skipped: {malformed}", file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logproc",
        description="Parse and summarise application log files.",
        epilog=EPILOG,
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    p_parse = sub.add_parser("parse", help="print each log entry as JSON")
    p_parse.add_argument("file", help="path to the log file")
    p_parse.set_defaults(func=cmd_parse)

    p_stats = sub.add_parser("stats", help="print per-level counters")
    p_stats.add_argument("file", help="path to the log file")
    p_stats.set_defaults(func=cmd_stats)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except FileNotFoundError as exc:
        print(f"logproc: error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
