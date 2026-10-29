# Using tieout with Codex

*[Leer en español](codex.es.md)*

`tieout` is a standard Agent Skills folder (`SKILL.md` plus `scripts/`, `references/`, `assets/`). OpenAI's Codex documentation (read 2026-10-29) says Codex loads skills of that shape. **This has not been run in Codex**: there was no Codex here to test it. Treat this page as the expected path and report what differs.

## Install without cloning the repository

Use the branch or tag that has the release you want in place of `main` below. A private repository needs credentials on that machine (`gh auth login`, or a token in `GITHUB_TOKEN`); a public one does not.

**Option A: Codex's installer.** OpenAI's page says you can prompt the installer to download skills from other repositories. In Codex:

```
$skill-installer install https://github.com/sorenriosdev/tieout-skill/tree/main/skills/tieout
```

Third-party descriptions of the installer (not OpenAI's page) say it accepts a tree URL or `--repo owner/repo --path skills/tieout`, installs into `$CODEX_HOME/skills` (default `~/.codex/skills`), and refuses to overwrite an existing folder. OpenAI's page lists `~/.agents/skills` as the user location and does not mention `~/.codex/skills`. So after installing, run `/skills`; if `tieout` is not listed, move the folder to `~/.agents/skills/tieout` and restart Codex.

**Option B: only git, no full clone.**

```
git clone --depth 1 --filter=blob:none --sparse --branch main https://github.com/sorenriosdev/tieout-skill.git /tmp/tieout-src
git -C /tmp/tieout-src sparse-checkout set skills/tieout
mkdir -p ~/.agents/skills && cp -r /tmp/tieout-src/skills/tieout ~/.agents/skills/tieout
rm -rf /tmp/tieout-src
```

**Option C: the open `skills` CLI** (a third-party tool that needs npm; check your company's policy on running third-party packages). Its public documentation shows:

```
npx skills add sorenriosdev/tieout-skill --list
npx skills add sorenriosdev/tieout-skill --skill tieout -a codex -g
```

Check `npx skills add --help` first: flags and supported agents change between versions.

To update, remove `~/.agents/skills/tieout` and install again. To use it in one repository only, copy it to `<repo>/.agents/skills/tieout` instead.

The skill needs Python 3.11 or later. `scripts/bi_fields.py` uses only the standard library; install the rest with `pip install sqlglot duckdb` if your environment allows it (the scripts name what is missing and stop).

**What the scripts do:** they make no network calls and start no other programs. The only file any of them can write is the new file you pass to `transpile_sql.py --out`, and it refuses to overwrite.

## Smoke test (three minutes, no data)

1. Restart Codex and run `/skills`: `tieout` should be listed.
2. Run in a shell: `python3 ~/.agents/skills/tieout/scripts/waterfall.py --help`.
3. In Codex: `$tieout list which tools you have available for SQL work and say which mode you are in`. It should run `check_capabilities.py`, name what is missing, and declare `code-only`, `one-system` or `both`.

## Use

- Explicit: type `$tieout` (or run `/skills` and pick it), followed by the task. For example: `$tieout the Channel breakdown of this query does not match the reference report; the total ties`.
- Implicit: Codex may select it from the description when the task matches. Do not depend on that, especially for read-only investigations: in the Claude Code tests an agent that thought "read-only" did not apply the skill. Name it.
- Scripts live in the skill folder (`scripts/`). The skill refers to them relative to its own folder; if the agent cannot find them, tell it the folder you copied to.

## If Codex does not load the skill

Codex also reads `AGENTS.md`. Append `adapters/AGENTS.md` (the 12 rules, the three weights and the closing block, about 470 words) to your project's `AGENTS.md`. You lose the playbooks and scripts but keep the discipline. Without the skill folder the agent cannot run the scripts; point it at a copy of `skills/tieout/` if it can read files.

## Things to check the first time

- The skill list in Codex is limited (about 2 % of the context window, or 8,000 characters if unknown). Codex shortens descriptions first and may omit skills with a warning. If `tieout` does not appear, remove other skills or raise `skills.max_context_tokens`.
- Codex's sandbox and approval settings decide whether it can run `python3 scripts/...` and write the `tieout/` folder. A read-only configuration is fine for investigations: the skill creates no files in `code-only` mode or when told it is read-only.
- Check what it prints before trusting it: every claim should carry a label (`[verified: ...]`, `[assumption]`) and every reply should end with Backup, Checked, Not checked and Pending.

## Not covered here

Codex plugins and `agents/openai.yaml` (UI and invocation policy) are not provided. Hooks, status lines and other host-specific parts are out of scope.
