"""Log parsing and statistics core for log-processor."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

# 2026-09-07 08:15:30.123 INFO  user login from 10.0.0.8
_LINE_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})[ \t]+"
    r"(?P<level>DEBUG|INFO|WARN|ERROR)[ \t]+"
    r"(?P<message>.+)$"
)

LEVELS = ("DEBUG", "INFO", "WARN", "ERROR")


@dataclass(frozen=True)
class LogEntry:
    timestamp: str
    level: str
    message: str


def parse_line(line: str) -> LogEntry | None:
    """Parse one raw log line into a LogEntry, or None if malformed."""
    m = _LINE_RE.match(line.rstrip("\n"))
    if m is None:
        return None
    return LogEntry(
        timestamp=m.group("ts"),
        level=m.group("level"),
        message=m.group("message"),
    )


def read_entries(path: Path) -> tuple[list[LogEntry], int]:
    """Read a log file, returning (valid entries, number of malformed lines)."""
    entries: list[LogEntry] = []
    malformed = 0
    for raw in path.read_text(encoding="utf-8").splitlines():
        entry = parse_line(raw)
        if entry is None:
            malformed += 1
        else:
            entries.append(entry)
    return entries, malformed


def count_levels(entries: list[LogEntry]) -> Counter[str]:
    """Count entries per level. Levels with zero entries are absent."""
    return Counter(e.level for e in entries)
