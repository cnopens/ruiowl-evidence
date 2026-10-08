"""Baseline tests for the parse and stats commands."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SAMPLE = """\
2026-09-07 08:15:30.123 INFO  user login from 10.0.0.8
this line is malformed and must be skipped
2026-09-07 08:15:31.002 ERROR disk full on /dev/sda1
2026-09-07 08:15:31.900 INFO  user login from 10.0.0.9
2026-09-07 08:16:02.411 WARN  slow query took 412ms
"""


def run_cli(args: list[str], cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "logproc", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=30,
    )


def test_parse_emits_json_per_entry(tmp_path: Path) -> None:
    log = tmp_path / "app.log"
    log.write_text(SAMPLE, encoding="utf-8")

    proc = run_cli(["parse", str(log)])

    assert proc.returncode == 0
    lines = [json.loads(ln) for ln in proc.stdout.strip().splitlines()]
    assert len(lines) == 4  # the malformed line is skipped
    assert lines[0] == {
        "ts": "2026-09-07 08:15:30.123",
        "level": "INFO",
        "message": "user login from 10.0.0.8",
    }
    assert lines[1]["level"] == "ERROR"
    assert lines[1]["message"] == "disk full on /dev/sda1"


def test_parse_missing_file_fails_gracefully(tmp_path: Path) -> None:
    proc = run_cli(["parse", str(tmp_path / "nope.log")])
    assert proc.returncode == 1
    assert "no such file" in proc.stderr


def test_stats_counts_levels_and_total(tmp_path: Path) -> None:
    log = tmp_path / "app.log"
    log.write_text(SAMPLE, encoding="utf-8")

    proc = run_cli(["stats", str(log)])

    assert proc.returncode == 0
    stdout = proc.stdout
    assert "INFO: 2" in stdout
    assert "ERROR: 1" in stdout
    assert "WARN: 1" in stdout
    assert "DEBUG: 0" in stdout
    assert "total: 4" in stdout


def test_stats_on_empty_file(tmp_path: Path) -> None:
    log = tmp_path / "empty.log"
    log.write_text("", encoding="utf-8")

    proc = run_cli(["stats", str(log)])

    assert proc.returncode == 0
    assert "DEBUG: 0" in proc.stdout
    assert "total: 0" in proc.stdout
