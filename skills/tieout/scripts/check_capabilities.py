#!/usr/bin/env python3
"""Report which libraries and command-line tools are available, as a dated
markdown block to paste into session.md (phase 0).

It does not decide the working mode: whether you can reach the data is
something the user states. It also cannot see MCP servers or other agent
tools; list those yourself from what your environment exposes.

Usage:
  python check_capabilities.py
  python check_capabilities.py --require sqlglot,duckdb   # exit 1 if any is missing

Exit codes: 0 everything required is present (or nothing was required),
1 something required is missing.
"""
import argparse
import datetime
import importlib.metadata
import importlib.util
import platform
import shutil
import sys

LIBRARIES = {
    "sqlglot": "SQL parsing and dialect translation (needed for any dialect work)",
    "duckdb": "Local SQL engine for tests and the synthetic example",
    "data_diff": "Row-level diff between databases (optional adapter)",
}

CLIS = {
    "git": "Version history and diffs of queries",
    "duckdb": "DuckDB shell",
    "sqlite3": "SQLite shell",
    "psql": "PostgreSQL client",
    "mysql": "MySQL client",
    "sqlcmd": "SQL Server client",
    "bq": "BigQuery client",
    "databricks": "Databricks CLI",
    "snowsql": "Snowflake client",
    "data-diff": "data-diff CLI (optional adapter)",
}


def library_status(name):
    if importlib.util.find_spec(name) is None:
        return None
    try:
        return importlib.metadata.version(name.replace("_", "-"))
    except importlib.metadata.PackageNotFoundError:
        return "installed (version unknown)"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--require", default="", help="comma-separated libraries or CLIs the task needs")
    args = ap.parse_args()
    required = {r.strip() for r in args.require.split(",") if r.strip()}

    now = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    available = set()
    lines = [
        f"## Capabilities [verified: check_capabilities.py, {now}]",
        "",
        f"- Python {platform.python_version()} on {platform.system()}",
        "",
        "| Kind | Name | Status | Used for |",
        "|---|---|---|---|",
    ]
    for name, purpose in LIBRARIES.items():
        version = library_status(name)
        if version:
            available.add(name)
        lines.append(f"| library | {name} | {version or 'missing'} | {purpose} |")
    for name, purpose in CLIS.items():
        path = shutil.which(name)
        if path:
            available.add(name)
        lines.append(f"| cli | {name} | {'found' if path else 'missing'} | {purpose} |")

    missing = sorted(required - available)
    lines += ["", "Not detectable from this script: MCP servers, BI connectors and other agent tools. List them from your environment."]
    if required:
        lines.append(f"Required for this task: {', '.join(sorted(required))}. "
                     + (f"**Missing: {', '.join(missing)}.** Stop, or continue in a reduced mode you declare."
                        if missing else "All present."))
    print("\n".join(lines))
    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()
