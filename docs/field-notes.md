# Field notes: measuring tieout at work without carrying work material out

*[Leer en español](field-notes.es.md)*

The goal is to learn whether the skill helps and how to improve it, without moving anything that belongs to an employer or client into this repository.

## Rules

1. **Raw material stays where it was made.** Queries, dashboards, model files, outputs, agent transcripts, names and figures stay on the employer's systems.
2. **What you take out is a note you write yourself,** in your own words, about the *pattern*, with invented names. No copy and paste, no screenshots, no paraphrase close enough to identify a client, a table or a figure.
3. **Check before taking anything out.** Keep a list of terms that must not leave (client, system, table and person names, figures), outside any repository, and scan the note:

   `TIEOUT_BANNED_TERMS=/path/to/your-terms.txt python3 dev/check_banned_terms.py --file notes.md`

   The checker prints the line and the term number, never the term, and exits with 1 if it finds one. It only catches terms on your list: it is a safety net, not a review.
4. **Fixtures are invented.** Scenarios and examples in this repository are made up; a new one is written from the pattern, never from the original case.
5. **Develop elsewhere.** Use the skill at work; change the skill on your own time, equipment and accounts.

## One row per task

Mostly categories and counts, so there is little to leak. Fill the last two in your own words.

| Field | Example |
|---|---|
| Date | |
| Task type | tie-out / logic review / migration / trace / clone / schema change |
| Agent and model | |
| Skill used | explicit `$tieout` / by itself / no |
| Outcome | cause found / partial / not found / wrong |
| Minutes and turns (approximate) | |
| Field path traced before any theory? | yes / no |
| Claims made without a test (count) | |
| Questions left to a person that were theirs (count) | |
| Business rules chosen silently (count) | |
| Script outputs that helped | `bi_fields model`, `sql_review diff`, none |
| Pattern learned, with invented names | |
| Suggested change to the skill | principle / playbook / script / description |

Compare a task done with the skill against a similar one done without it, when you have one. Two rows is an anecdote; twenty is a signal.

## Bringing a lesson home

A lesson that is useful to the skill is a *pattern*: "a report took a classification field from a dimension table while the reference took it from the fact table; the total tied and the split did not". Write that, with invented tables and no figures. If you cannot write it without the original names, it is not ready to leave.
