# Playbook: clone-bi

Use when a BI report is copied to another unit, entity or model, or when someone edits a report's files or checks a report before publishing. The goal is a copy that carries nothing that belongs to the source: no fields the target model lacks, no values saved from the source, no binding to the source's published report.

Cloning is mostly a business question wearing a technical costume. Which field replaces a missing one, whether a saved filter value is "inherited" or intended, whether a hidden visual is dead or someone's tool: those are decisions, not facts. The script lists; people decide.

Tool facts (which files may be edited while the tool is open, what connectors cover) are in `references/bi-tools.md`. Read it first.

## Phase 0. Capabilities

1. Run `scripts/check_capabilities.py`. The inventory script itself needs only Python.
2. Ask which BI tool is involved and whether its connector is connected (list the tools you can call). With a connector that reads the target model, use it to list the model's tables, columns and measures. Without one, recommend the one named in `bi-tools.md` in a sentence, and continue from files.
3. Ask whether the project is open in the BI tool right now.

## Phase 1. Spec

Fill `spec.md` with the user: the source report, the target model, what is supposed to differ in the copy (title, unit or entity filters, currency, language), which values are intentionally kept, who approves field mappings, and who approves publishing. If a figure check is wanted (the copy must show the same totals as the source on shared data), add tolerances; otherwise omit them.

## Phase 2. Inventory (read only)

- Power BI (PBIR): `python scripts/bi_fields.py pbir <target>.Report` (add `--model <target>.SemanticModel`, or `--against fields.txt` with one `Table.Field` per line from a connector or a data dictionary).
- Tableau: `python scripts/bi_fields.py twb <workbook>`.

For the semantic model itself, `python scripts/bi_fields.py model <target>.SemanticModel` lists the Power Query steps (with the ones that remove rows or change values flagged), the native SQL, the relationships and the measures that change filter context.

The script prints structure problems, every referenced field with where it is used, fields missing from the model, literal values stored in filters and titles, and the published-report binding. It writes nothing. Save its output to `evidence-log.md` with the date.

If the report is PBIR-Legacy (`report.json` only), the script stops: Microsoft documents that format as not editable externally. Ask the user to save the project as PBIR from the tool first.

## Phase 3. Classify the findings

Each finding is one row in `findings.md` with its status.

| Finding | What it usually means | Who decides |
|---|---|---|
| Field missing in the target model | The source model had something the target does not | Remove the visual, replace the field with another, or add the field to the model: a business choice when more than one replacement is plausible. Adding to the model is outside this playbook |
| Missing field only in a hidden visual or page | Often leftovers, sometimes someone's tool | Ask the owner. Hidden is not the same as unused. Do not delete silently |
| Saved filter value or slicer selection | Inherited from the source, or intended | Ask per value |
| Text such as a title naming the source's unit, entity or currency | Inherited label | Ask per text |
| Published-report binding points at the source's report | The next publish would overwrite the source's report | Confirm the intended report before any publish; never publish |
| `activePageName` or `landingPageName` points to no page, or duplicate page-binding names (a repeated filter name is only a note to check by hand) | Structure left by copying or deleting pages | Technical; propose the fix |
| Folder name outside letters, digits, underscore, hyphen | The tool ignores it | Technical |

Principle 11 applies to everything you plan to use as a replacement: check that it exists in the target model and holds data. A connector can run a count; otherwise label it `[assumption]` with the check.

## Phase 4. Propose

One proposal per decision, from the template. For the technical fixes, group them in one proposal. Every proposal states the expected result as a number: after the change the script reports 0 missing fields and 0 structure problems for the items it covers, and lists any literal values that remain on purpose.

Prefer copying a visual or page from a report that is known to work against the target model over patching fields in place, but only after confirming the fields it uses exist in the target model.

## Phase 5. Approve

As in `reconcile.md`: business decisions need the approver named in the Spec; permission to write needs the user.

## Phase 6. Apply

1. Ask the user to save the project in the BI tool. Do not continue until they confirm.
2. Copy the whole report folder to `tieout/backups/<name>.<timestamp>/` and say the path.
3. Edit only files that `bi-tools.md` lists as editable externally. `definition.pbir`, `report.json`, `mobileState.json` and `semanticModelDiagramLayout.json` are not editable while the project is open in Power BI Desktop; if one of them must change (for example, pointing a copied report at its own model), ask the user to close the project first.
4. Re-read each file just before editing it. The tool rewrites files when it opens or saves.
5. Ask the user to apply the external changes in the tool, or to reopen the project. Tell them that applying discards unsaved changes in the tool.

Never edit the source report. Never publish or change the published binding yourself.

## Phase 7. Verify

1. Re-run the inventory script. Expected: the findings you fixed are gone and nothing new appeared. Record before and after.
2. Say what you cannot verify. You cannot see the report render. Ask the user to open it and tell you what they see, and list "opens without errors" and "visuals show data" under "Not checked" until they do.
3. If a connector can run measures on both models, compare the key measures between source and target on shared data using `playbooks/reconcile.md`.

## Phase 8. Record

Add the decisions to `decision-register.md` (field mappings, kept values, hidden items removed or kept, binding confirmed), each with approver and date.

## Not covered

- Creating or changing the semantic model.
- Publishing, deployment pipelines and workspace permissions.
- Reports in the PBIR-Legacy format, and `.pbix` files (they are not text; ask the user to save as a project).
- Tableau workbook edits: the script inventories only. Edit workbooks in the tool or through a connector the user has; hand-editing the XML has no verified source here.
