# Playbook: reconcile

Use when two versions of the same figure disagree: an engine migration, a refactored query, a changed metric definition, a report against its source, an audit. The goal is a closed case: the difference is fully explained by measured effects, the residual is within the Spec's tolerance, and every change made on the way was approved and recorded.

This playbook follows the cycle in `SKILL.md`. Each phase lists what to do, what to write, and when to stop.

## Phase 0. Capabilities and mode

1. Run `python scripts/check_capabilities.py --require sqlglot` if either side needs a dialect translation; otherwise without `--require`.
2. Create `tieout/<case-id>/session.md` with the script output, the declared mode, and the list of agent tools you can use (BI connectors, database tools).
3. If the script exits 1, the first sentence of your reply names what is missing and what is therefore unverified. Then choose with the user: stop, or continue in a named reduced mode (for example "code-only, no dialect translation: queries are written for the reference dialect only"). A hand-written translation is allowed only in a reduced mode the user accepted, labelled `[assumption]` and delivered with the query that would verify it; never present it as ready to run.

## Phase 1. Spec

Fill `spec.md` from the template with the user. Ask for anything missing; do not fill gaps with your own guesses.

- Objects A (reference) and B (candidate), exactly: system, query or table, version.
- Grain and key: what one row is, and which column identifies it.
- Measure: name, definition on each side, unit, currency.
- Period, filters, cut-off date (the moment both sides are compared).
- Tolerances ε_abs and ε_rel, and what must tie out: the total only, or also the breakdown by period or dimension.
- Approvers: who decides which kind of rule (definitions, filters, calendar, mappings).

Stop if tolerances, key or cut-off are missing. Without them, "equal" is undefined and nothing can close.

## Phase 2. Baseline

Run ladder rungs L1 to L3 (`references/ladder.md`) and record each in `evidence-log.md` with its label and capture time. In `code-only` mode, write the queries for both sides and record the rungs as pending.

Before going further, check the totals against the Spec: if Δ is already within tolerance at every level the Spec requires, say so, record it, and propose closing (phase 8) instead of searching for causes.

## Phase 3. Localize

0. If a reference report or dashboard exists, or the symptom is a breakdown that differs while the total ties, run `trace.md` first and compare the field paths. Continue here only for what remains.
1. Pick hypotheses from the symptom index (`references/hypotheses.md`, section 3) using what L1 to L3 showed. Order them: high-power, cheap tests first.
2. Run U1 (`scripts/u1_query.py`) for rungs L4 and L5 when the key is known.
3. For each hypothesis, translate its test to the engine's dialect with sqlglot (never by hand), run it on the side(s) it names, and record the status: `confirmed`, `ruled out`, `ambiguous` or `not verified`.
4. **Measure each confirmed effect by neutralizing it, one at a time, in a fixed order.** The test's `evidence` column shows exposure, not necessarily the effect on Δ. To measure the effect, compute Δ with the cause removed (apply B's filter to A, deduplicate B, use the same rounding on both sides, and so on). With causes 1..n neutralized in order:

   e_i = Δ(causes 1..i−1 neutralized) − Δ(causes 1..i neutralized)

   Measured this way, the effects plus the final residual add up to Δ exactly, even when causes interact. Record the order you used.
5. Write the effects to `effects.csv` (`id,description,effect,evidence`) and run:

   `python scripts/waterfall.py close --a <A> --b <B> --effects effects.csv --eps-abs <ε_abs> --eps-rel <ε_rel>`

6. Copy the script output into `findings.md`. If the result is OPEN, continue down the ladder or test more hypotheses. If you have run out of hypotheses, say so: the catalog is incomplete, and an unexplained residual is a finding too.

Neutralizing a cause for measurement is an analysis step on copies or in queries. It is not a fix and does not touch the user's objects.

In `code-only` mode:

- Read both queries and list the concrete differences between them (joins and their type, filters and how they treat NULL, rounding, grouping, window functions). Each difference maps to a catalog hypothesis.
- Order the hypotheses by **cost and power of their test**: cheapest, highest-power first. Say that this is a testing order. Do not say, and do not imply, that one cause is more probable than another: that is a claim you cannot support without data (principle 10). Phrases like "most likely", "probably the cause", "the biggest candidate" or "unlikely to matter" are untested claims.
- Every hypothesis is `not verified`. For each, give the diagnostic query in the **reply itself**, not only in `findings.md`, so the person with database access can run it from the conversation. Use `scripts/u1_query.py` for the key decomposition.
- Business questions you notice (do NULL types count? do inactive stores count?) go in the reply as questions for a named approver, without a recommendation.
- Offer to compute the waterfall when they bring back the results.

## Phase 4. Propose

For each cause that calls for a change, write `proposals/NNN-<slug>.md` from the template:

- Classification: technical equivalent, business rule, or assumption (see `SKILL.md`).
- For a business rule with more than one plausible reading: the question, the options, the evidence for each option, and no recommendation presented as a decision.
- The exact change, as a diff or the full before and after.
- **The expected difference after the change, as a number**, with the base and tolerance to compare it against. Without it, phase 7 has nothing to check.
- How to revert, and where the backup will be.

Assumptions get a proposal too, with status `proposed` and the note "not applicable until confirmed".

## Phase 5. Approve

Record in the proposal who approved it and when, and who gave permission to apply it. A business rule needs the named approver from the Spec. A technical equivalent needs the user's permission to write. If the answer is "no" or "later", set the status and stop that proposal.

## Phase 6. Apply

1. If the target file is open in a tool that saves it, ask for it to be saved and closed.
2. Copy the current version to `backups/<file>.<timestamp>` and state the path in your reply.
3. Make the smallest change that implements the approved proposal. Nothing else in the same edit.

Never publish, deploy or create objects in a source system without the explicit permission recorded in phase 5.

## Phase 7. Verify

1. Re-run the same ladder rungs with the same queries as the baseline.
2. Measure the actual difference the change produced, and run:

   `python scripts/waterfall.py compare --expected <from proposal> --actual <measured> --base <A> --eps-abs <ε_abs> --eps-rel <ε_rel>`

3. If the result is MISMATCH, do not close. Report both numbers and the gap, keep the proposal `approved` but not verified, and go back to phase 3: the change did something other than what was expected.
4. If it is MATCH, re-run `waterfall.py close` for the case. Close the case only if that also passes.

## Phase 8. Record

Add a row to `decision-register.md` for each decision: date, who, what changed, which version is affected, and the evidence entries. Mark the case closed with the final waterfall output, or open with what is left.

## What this playbook does not do

- It does not decide which definition of a metric is right.
- It does not estimate the business or financial impact of a difference.
- It does not fix the source system. Source problems (late loads, duplicates at origin) are reported to their owner.
