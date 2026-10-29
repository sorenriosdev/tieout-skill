# BI tools and connectors

What the skill assumes about BI tools, what was verified, and what to do when a connector is or is not available. This file records facts with their source and date. Tool behavior changes between releases: when a fact here matters for an edit, confirm it against the user's installed version.

## How the skill uses connectors

- It consumes connectors (MCP servers or similar); it does not build or install them.
- In phase 0, list the tools you can call and ask the user which BI tool the work involves and whether its connector is connected.
- **Connector available:** use it for what it covers, following the normal cycle (read first, backup, approval, verify).
- **Connector missing:** say which one would help and what it would have done, in one or two sentences. Do not install it. Continue read-only or on files, within the rules below.
- A connector is an implementation of a capability, not a requirement. If the work can be done safely on files, say so.

## Power BI

Verified 2026-10-25 against Microsoft Learn pages "Power BI Desktop project report folder" and "Edit Power BI Desktop project files outside Power BI Desktop" (both dated 2026-09-23) and "Overview of the MCP Servers" (2026-09-24).

### Project files (PBIP)

- A report in PBIR format is a folder of small JSON files: `definition/report.json`, `definition/pages/pages.json` (page order and active page), one `page.json` per page, one `visual.json` per visual under `pages/<page>/visuals/<visual>/`. `definition.pbir` holds the reference to the semantic model. `.pbi/localSettings.json` holds settings for the current user and machine and is excluded from source control by default.
- Visual and bookmark files can persist data values (a filter on `Company = 'Contoso'` keeps the value in the file), so inherited values travel when a report is copied.
- Naming: object and folder names must be letters, digits, underscores or hyphens; a name that breaks the convention is ignored by Desktop.
- An invalid active page is a non-blocking error that Desktop repairs on open. A duplicate `pageBinding.name` between copied pages is a blocking error.

### Editing files while Desktop is open

Documented as a preview feature ("Detect and reload external PBIP changes"), August 2026 release or later:

1. Ask the user to save in Desktop first. Desktop does not write its latest changes to the files until it saves.
2. Edit a supported file and save it.
3. Ask the user to select "Apply external changes" in the banner. Desktop reloads the whole report or model, not single files.
4. If Desktop holds unsaved changes when the user applies external changes, those changes are discarded. Never apply on the user's behalf without saying so.
5. Files documented as not editable externally during the preview: `definition.pbir`, `report.json`, `mobileState.json`, `semanticModelDiagramLayout.json`. Do not edit them.
6. If the preview setting is off, or the Desktop version is older, treat Desktop as unable to detect changes: ask the user to close the project before editing files.
7. Re-read any file before editing it a second time. Desktop rewrites files when it opens or saves.

### Connectors

- Microsoft documents a **Power BI Authoring MCP server**: it reads and writes semantic models (tables, columns, measures, relationships, DAX validation, TMDL and PBIP files). A local server (stdio) is described as generally available and works with Desktop and PBIP folders; a Microsoft-hosted endpoint is described as preview and works with models in Fabric workspaces. Community material also calls it "Power BI Modeling MCP"; the name in the user's install may differ.
- It covers the **semantic model**, not the report's pages and visuals. Visuals are edited as PBIR files.
- **Fabric IQ** is a separate MCP endpoint for answering questions over governed data. It is a consumption tool, not an authoring tool; do not use it to edit.
- Connectors act with the signed-in user's permissions and may send metadata and results to the model provider. Mention this when asking permission to connect a connector to production objects.

## Tableau

Verified 2026-10-25 against the repository `tableau/tableau-mcp` (described there as Tableau's official MCP server).

- The published package serves Tableau Cloud and Tableau Server (web). A Tableau Desktop authoring server is built from the same repository and is not part of that package. A hosted version for Tableau Cloud is mentioned.
- Not verified here: the tool list and the support level. Read the project's documentation before relying on a specific tool.
- For Power BI semantic models, `scripts/bi_fields.py model` reads TMDL or `model.bim` files without a connector: Power Query steps, native queries, relationships and filter-context measures.
- Workbook files (`.twb`, `.twbx`) are XML (a `.twbx` is a zip containing a `.twb`). `scripts/bi_fields.py` reads field references from `.twb` files; see `playbooks/clone-bi.md`.

## Other BI tools

No facts have been verified. Apply principles 8 and 11 as written: find out whether the tool saves its own files, ask the user to save, edit only files the tool documents as editable, and check every field against the model.
