# log-processor

A small command-line tool for parsing and summarising application log files.
Written in pure Python (standard library only).

## Log line format

Each log line follows this fixed format:

```
2026-09-07 08:15:30.123 INFO  user login from 10.0.0.8
2026-09-07 08:15:31.002 ERROR disk full on /dev/sda1
```

- timestamp: `YYYY-MM-DD HH:MM:SS.mmm`
- level: one of `DEBUG`, `INFO`, `WARN`, `ERROR`
- message: free text (may contain spaces)

## Commands

### `parse`

Print every log entry as one JSON object per line:

```bash
python3 -m logproc parse app.log
```

### `stats`

Print a per-level counter summary and the total number of entries:

```bash
python3 -m logproc stats app.log
```

```
INFO: 12
ERROR: 3
WARN: 5
DEBUG: 0
total: 20
```

Malformed lines are skipped by both commands (they are counted nowhere and
printed nowhere).

## Getting started

```bash
python3 -m pip install pytest   # dev dependency, for the test suite
python3 -m pytest               # run all tests
```
