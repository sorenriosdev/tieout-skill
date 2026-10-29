#!/usr/bin/env python3
"""Build adapters/AGENTS.md, the compact rule file for agents without skill support.

  python dev/build_agents_md.py --write    # regenerate adapters/AGENTS.md
  python dev/build_agents_md.py --check    # exit 1 if it is out of date

The principles and the closing block are copied from skills/tieout/SKILL.md, so
the compact file cannot drift from the skill. The rest (the three weights) is
written here and kept short on purpose: an always-on rule file costs tokens on
every turn, so it carries the rules, not the method. The full method lives in
skills/tieout/.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "tieout" / "SKILL.md"
OUT = ROOT / "adapters" / "AGENTS.md"


def section(text, heading):
    m = re.search(rf"^## {re.escape(heading)}.*?\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    if not m:
        sys.exit(f"build_agents_md: section '{heading}' not found in SKILL.md")
    return m.group(1)


def build():
    text = SKILL.read_text(encoding="utf-8")
    principles = [l.replace("`references/", "`skills/tieout/references/")
                  for l in section(text, "Principles (always on)").splitlines() if re.match(r"^\d+\. ", l)]
    if len(principles) != 12:
        sys.exit(f"build_agents_md: expected 12 principles in SKILL.md, found {len(principles)}")
    closing = re.search(r"```\n(Backup:.*?)```", section(text, "Step 3: the closing block"), re.S)
    if not closing:
        sys.exit("build_agents_md: closing block not found in SKILL.md")
    return f"""# tieout: change-safety rules for data work

Compact rules for agents that read a rules file but not skills. They apply when the task changes or compares SQL, data models, schemas, pipelines or BI reports. For anything else, ignore this file. The full method (modes, phases, playbooks, scripts, templates) is in `skills/tieout/`; if the agent can read files, point it at `skills/tieout/SKILL.md`.

Reply and write in the user's language.

## Before you start

- If the task needs a tool you do not have (SQL translation needs sqlglot, running queries needs a database client or connector, BI work needs the BI tool's connector), the **first sentence of your reply** names it and says what is therefore unverified. Then stop, or continue in a reduced mode you name. Never do the tool's job by hand without saying so.
- Pick the weight and say which: **light** (one object, exact change already stated or approved, no open business-rule choice: back up, change, add one row to a decision register), **decision** (a rule has two plausible readings or the choice is someone else's: write the question with options and evidence, change nothing), or **full** (figures differ between two versions, or a migration or audit: follow the phases in `skills/tieout/SKILL.md`).

## Principles

{chr(10).join(principles)}

## End every reply with

```
{closing.group(1).rstrip()}
```

The reply must stand on its own: queries to run, evidence labels and open questions are in the reply, not only in files.
"""


def main():
    mode = sys.argv[1] if len(sys.argv) == 2 else ""
    if mode not in ("--write", "--check"):
        sys.exit(__doc__)
    content = build()
    if mode == "--write":
        OUT.parent.mkdir(exist_ok=True)
        OUT.write_text(content, encoding="utf-8")
        print(f"wrote {OUT.relative_to(ROOT)} ({len(content.split())} words)")
        return
    if not OUT.is_file() or OUT.read_text(encoding="utf-8") != content:
        print("adapters/AGENTS.md is out of date: run python dev/build_agents_md.py --write", file=sys.stderr)
        sys.exit(1)
    print("adapters/AGENTS.md is in sync with SKILL.md")


if __name__ == "__main__":
    main()
