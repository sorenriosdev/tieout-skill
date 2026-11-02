#!/usr/bin/env python3
"""Inventory the fields a BI report references and check them against its model.

Read-only. Never writes to the report. Standard library only.

  python bi_fields.py pbir <Report folder> [--model <SemanticModel folder>] [--against fields.txt]
  python bi_fields.py model <SemanticModel folder>
  python bi_fields.py twb  <workbook.twb|.twbx> [--against fields.txt]

pbir  A Power BI report in PBIR format (a "<name>.Report" folder with a
      "definition" subfolder). Reports:
        - structure: pages.json against the page folders, active and landing
          page, JSON validity, names, duplicated binding names (repeated filter names are notes)
        - every field each visual, page and report filter references,
          including hidden visuals and hidden pages
        - fields that do not exist in the semantic model (TMDL or model.bim)
        - literal values stored in filters and titles (values inherited when a
          report is cloned from another one)
        - the semantic-model reference and the published-report binding
model A Power BI semantic model (TMDL folder or model.bim). Lists, per table, the
      Power Query steps and which of them can remove rows, change the row count or
      change values (filters, duplicate removal, joins and their kind, type
      changes, relative-date and incremental-refresh filters), the native SQL
      sent to the source, the relationships (inactive, bidirectional) and the
      measures that change filter context. This is where a figure can be lost
      between the warehouse and the visual without any visual-level filter.
twb   A Tableau workbook. Reports fields used by each worksheet, those not
      declared in their data source, filter values, hidden worksheets and
      worksheets used by dashboards.

--against FILE  one "Table.Field" per line (or "Field" for Tableau) coming from
                anywhere: DESCRIBE output, a connector, a data dictionary. It
                replaces model auto-detection. Lines starting with # are ignored.

The format knowledge comes from Microsoft's published PBIR JSON schemas and
documentation (checked 2026-10-25) and from the structure of .twb files. It was
tested on small synthetic projects, not on production reports: read the output
as an inventory to verify, not as proof that a report opens without errors.

Exit codes: 0 no findings, 1 findings (missing fields or structural problems),
2 invalid input or unsupported format.
"""
import argparse
import json
import pathlib
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

NAME_RE = re.compile(r"^[\w-]+$")


def fail(msg):
    print(f"bi_fields: {msg}", file=sys.stderr)
    sys.exit(2)


# --------------------------------------------------------------------------
# Semantic model readers
# --------------------------------------------------------------------------

def unquote_tmdl(token):
    token = token.strip()
    if token.startswith("'"):
        out, i = [], 1
        while i < len(token):
            if token[i] == "'":
                if i + 1 < len(token) and token[i + 1] == "'":
                    out.append("'")
                    i += 2
                    continue
                break
            out.append(token[i])
            i += 1
        return "".join(out), token[i + 1:]
    m = re.match(r"[^\s=:]+", token)
    return (m.group(0), token[m.end():]) if m else ("", token)


def read_tmdl(folder):
    """{table: {field: kind}} from a TMDL definition folder."""
    fields = {}
    files = sorted(pathlib.Path(folder).rglob("*.tmdl"))
    for f in files:
        child_indent = None
        table = None
        for raw in f.read_text(encoding="utf-8-sig").splitlines():
            if not raw.strip() or raw.lstrip().startswith(("///", "//")):
                continue
            indent = len(raw) - len(raw.lstrip(" \t"))
            line = raw.strip()
            if indent == 0:
                m = re.match(r"table\s+(.+)", line)
                if m:
                    table, _ = unquote_tmdl(m.group(1))
                    fields.setdefault(table, {})
                    child_indent = None
                else:
                    table = None
                continue
            if table is None:
                continue
            if child_indent is None:
                child_indent = indent
            if indent != child_indent:
                continue
            m = re.match(r"(column|measure|hierarchy)\s+(.+)", line)
            if m:
                name, _ = unquote_tmdl(m.group(2))
                if name:
                    fields[table][name] = m.group(1)
    return fields, len(files)


def read_bim(path):
    model = json.loads(pathlib.Path(path).read_text(encoding="utf-8-sig"))
    model = model.get("model", model)
    fields = {}
    for t in model.get("tables", []):
        d = fields.setdefault(t["name"], {})
        for c in t.get("columns", []):
            d[c["name"]] = "column"
        for m in t.get("measures", []):
            d[m["name"]] = "measure"
        for h in t.get("hierarchies", []):
            d[h["name"]] = "hierarchy"
    return fields


def read_against(path):
    fields = {}
    for line in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        table, _, name = line.rpartition(".")
        fields.setdefault(table, {})[name] = "listed"
    return fields


def find_model(report_dir, explicit):
    """Return (model_fields or None, description)."""
    if explicit:
        return load_model_folder(pathlib.Path(explicit), "--model")
    pbir = report_dir / "definition.pbir"
    if pbir.is_file():
        try:
            ref = json.loads(pbir.read_text(encoding="utf-8-sig")).get("datasetReference", {})
        except json.JSONDecodeError:
            return None, "definition.pbir is not valid JSON"
        by_path = (ref.get("byPath") or {}).get("path")
        if by_path:
            return load_model_folder((report_dir / by_path).resolve(), f"definition.pbir byPath {by_path}")
        if ref.get("byConnection"):
            return None, "definition.pbir uses byConnection (a published model): pass --model or --against"
    return None, "no semantic model found: pass --model or --against"


def load_model_folder(folder, how):
    if not folder.is_dir():
        return None, f"model folder not found ({how}: {folder})"
    tmdl = folder / "definition"
    if tmdl.is_dir() and list(tmdl.rglob("*.tmdl")):
        fields, n = read_tmdl(tmdl)
        return fields, f"TMDL, {n} files, {len(fields)} tables ({how})"
    for cand in (folder / "model.bim", folder / "definition" / "model.bim"):
        if cand.is_file():
            fields = read_bim(cand)
            return fields, f"model.bim, {len(fields)} tables ({how})"
    return None, f"no TMDL or model.bim in {folder} ({how})"


# --------------------------------------------------------------------------
# PBIR walker
# --------------------------------------------------------------------------

class Collector:
    def __init__(self):
        self.refs = []      # (where, kind, entity, property)
        self.literals = []  # (where, value)

    def walk(self, node, where, aliases=None, path=(), in_where=False):
        aliases = aliases or {}
        if isinstance(node, dict):
            if isinstance(node.get("From"), list):
                aliases = dict(aliases)
                for src in node["From"]:
                    if isinstance(src, dict) and "Name" in src and "Entity" in src:
                        aliases[src["Name"]] = src["Entity"]
            for kind in ("Column", "Measure"):
                body = node.get(kind)
                if isinstance(body, dict) and "Property" in body and isinstance(body.get("Expression"), dict):
                    self._ref(kind, body["Expression"], body["Property"], where, aliases)
            body = node.get("Hierarchy")
            if isinstance(body, dict) and "Hierarchy" in body and isinstance(body.get("Expression"), dict):
                self._ref("Hierarchy", body["Expression"], body["Hierarchy"], where, aliases)
            lit = node.get("Literal")
            if isinstance(lit, dict) and isinstance(lit.get("Value"), str):
                value = lit["Value"]
                if value.startswith("'") and (in_where or any(p.lower() in ("title", "subtitle") for p in path)):
                    self.literals.append((where, value.strip("'")))
            for key, value in node.items():
                self.walk(value, where, aliases, path + (key,), in_where or key == "Where")
        elif isinstance(node, list):
            for item in node:
                self.walk(item, where, aliases, path, in_where)

    def _ref(self, kind, expr, prop, where, aliases):
        ref = expr.get("SourceRef")
        if not isinstance(ref, dict):
            return
        entity = ref.get("Entity") or aliases.get(ref.get("Source"))
        self.refs.append((where, kind, entity or f"<unresolved alias {ref.get('Source')}>", prop))


def load_json(path, problems):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        problems.append(f"invalid JSON: {path}: {e}")
        return None


def pbir_report(args):
    report_dir = pathlib.Path(args.path).resolve()
    definition = report_dir / "definition"
    if not report_dir.is_dir():
        fail(f"not a folder: {report_dir}")
    if not definition.is_dir():
        fail(f"{report_dir} has no 'definition' folder. This script reads PBIR. "
             "A PBIR-Legacy report keeps everything in report.json, which Microsoft documents as not editable externally; "
             "save the report as PBIR in Power BI Desktop first.")

    problems, notes = [], []
    col = Collector()
    pages_meta = load_json(definition / "pages" / "pages.json", problems) if (definition / "pages" / "pages.json").is_file() else None
    page_dirs = sorted(p for p in (definition / "pages").iterdir() if p.is_dir()) if (definition / "pages").is_dir() else []

    # structure
    folder_names = [p.name for p in page_dirs]
    if pages_meta is None:
        notes.append("pages/pages.json is absent (optional); page order and active page are not declared")
    else:
        order = pages_meta.get("pageOrder", [])
        for name in order:
            if name not in folder_names:
                problems.append(f"pages.json pageOrder lists '{name}' but there is no such page folder")
        for name in folder_names:
            if name not in order:
                problems.append(f"page folder '{name}' is not listed in pages.json pageOrder")
        for key in ("activePageName", "landingPageName"):
            value = pages_meta.get(key)
            if value and value not in folder_names:
                problems.append(f"pages.json {key} = '{value}' but no such page exists (Microsoft documents an invalid activePageName as a non-blocking error that Desktop repairs on open)")

    filter_names, binding_names, page_rows, visual_rows = {}, {}, [], []
    report_json = definition / "report.json"
    if report_json.is_file():
        data = load_json(report_json, problems)
        if data is not None:
            col.walk(data, "report.json")
            for flt in (data.get("filterConfig") or {}).get("filters", []):
                filter_names.setdefault(flt.get("name"), []).append("report.json")

    bookmarks = definition / "bookmarks"
    if bookmarks.is_dir():
        for bm in sorted(bookmarks.glob("*.bookmark.json")):
            data = load_json(bm, problems)
            if data is not None:
                col.walk(data, f"bookmarks/{bm.name}")

    ext_path = definition / "reportExtensions.json"
    extension_fields = {}
    if ext_path.is_file():
        data = load_json(ext_path, problems)
        for ent in (data or {}).get("entities", []):
            for m in ent.get("measures", []):
                extension_fields.setdefault(ent["name"], {})[m["name"]] = "measure"

    for pdir in page_dirs:
        if not NAME_RE.match(pdir.name):
            problems.append(f"page folder name '{pdir.name}' breaks the naming convention (letters, digits, underscore, hyphen); Desktop ignores it")
        pjson = pdir / "page.json"
        page = load_json(pjson, problems) if pjson.is_file() else None
        if page is None:
            if not pjson.is_file():
                problems.append(f"page folder '{pdir.name}' has no page.json")
            continue
        if page.get("name") != pdir.name:
            problems.append(f"page '{pdir.name}': page.json name is '{page.get('name')}'")
        hidden_page = page.get("visibility") == "HiddenInViewMode"
        rel = f"pages/{pdir.name}/page.json"
        col.walk(page, rel)
        for flt in (page.get("filterConfig") or {}).get("filters", []):
            filter_names.setdefault(flt.get("name"), []).append(rel)
        binding = (page.get("pageBinding") or {}).get("name")
        if binding:
            binding_names.setdefault(binding, []).append(pdir.name)
        vdirs = sorted(v for v in (pdir / "visuals").iterdir() if v.is_dir()) if (pdir / "visuals").is_dir() else []
        page_rows.append((pdir.name, page.get("displayName", ""), "hidden" if hidden_page else "visible", len(vdirs)))
        for vdir in vdirs:
            vjson = vdir / "visual.json"
            if not NAME_RE.match(vdir.name):
                problems.append(f"visual folder name '{pdir.name}/{vdir.name}' breaks the naming convention; Desktop ignores it")
            visual = load_json(vjson, problems) if vjson.is_file() else None
            if visual is None:
                if not vjson.is_file():
                    problems.append(f"visual folder '{pdir.name}/{vdir.name}' has no visual.json")
                continue
            vrel = f"pages/{pdir.name}/visuals/{vdir.name}/visual.json"
            before = len(col.refs)
            col.walk(visual, vrel)
            for flt in (visual.get("filterConfig") or {}).get("filters", []):
                filter_names.setdefault(flt.get("name"), []).append(vrel)
            vtype = (visual.get("visual") or {}).get("visualType", "group" if visual.get("visualGroup") else "?")
            visual_rows.append((pdir.name, vdir.name, vtype,
                                "HIDDEN" if visual.get("isHidden") else "", "hidden page" if hidden_page else "",
                                len({(k, e, p) for w, k, e, p in col.refs[before:]})))

    for name, places in filter_names.items():
        if name and len(places) > 1:
            notes.append(f"filter name '{name}' appears {len(places)} times ({', '.join(places)}); often a filter cloned with its visual. Check by hand that it is unique before publishing")
    for name, pages in binding_names.items():
        if len(pages) > 1:
            problems.append(f"pageBinding name '{name}' is used by pages {', '.join(pages)}; it must be unique (a copied page keeps the source page's binding)")

    # model
    if args.against:
        model, how = read_against(args.against), f"list file {args.against}"
    else:
        model, how = find_model(report_dir, args.model)
        if isinstance(model, dict):
            for ent, d in extension_fields.items():
                model.setdefault(ent, {}).update(d)

    # usage table
    usage = {}
    for where, kind, entity, prop in col.refs:
        usage.setdefault((entity, prop, kind), set()).add(where)
    hidden_places = {f"pages/{p}/visuals/{v}/visual.json" for p, v, _, h, _, _ in visual_rows if h} | \
                    {f"pages/{p}/visuals/{v}/visual.json" for p, v, _, _, hp, _ in visual_rows if hp}
    missing = []
    for (entity, prop, kind), places in sorted(usage.items()):
        if model is None:
            continue
        if entity not in model or prop not in model[entity]:
            missing.append((entity, prop, kind, sorted(places)))

    # binding
    binding_lines = []
    pbir = report_dir / "definition.pbir"
    if pbir.is_file():
        ref = (load_json(pbir, problems) or {}).get("datasetReference", {})
        if "byPath" in ref:
            target = (report_dir / ref["byPath"].get("path", "")).resolve()
            binding_lines.append(f"semantic model: byPath `{ref['byPath'].get('path')}` ({'found' if target.is_dir() else 'NOT FOUND'})")
            if not target.is_dir():
                problems.append(f"definition.pbir byPath target does not exist: {target}")
        elif "byConnection" in ref:
            binding_lines.append("semantic model: byConnection (published model; connection string not printed)")
    else:
        problems.append("definition.pbir is missing")
    ls = report_dir / ".pbi" / "localSettings.json"
    if ls.is_file():
        data = load_json(ls, problems) or {}
        ids = [a.get("reportId") for a in (data.get("remoteArtifacts") or []) if isinstance(a, dict)]
        binding_lines.append("published report binding (.pbi/localSettings.json remoteArtifacts[].reportId): "
                             + (", ".join(f"`{i}`" for i in ids) if ids else "none"))
    else:
        binding_lines.append("published report binding: no .pbi/localSettings.json (not published from this folder, or the file is excluded)")

    # report
    out = [f"# BI field inventory: {report_dir.name}", "",
           f"Read-only inventory of a PBIR report. Model: {how}.", ""]
    out += ["## Structure", ""]
    out += [f"- {p}" for p in problems] or ["- no structural problems found"]
    out += [f"- note: {n}" for n in notes]
    out += ["", "## Pages", "", "| Page folder | Display name | Visibility | Visuals |", "|---|---|---|---|"]
    out += [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in page_rows]
    out += ["", "## Visuals", "", "| Page | Visual | Type | Hidden | Page hidden | Distinct fields |", "|---|---|---|---|---|---|"]
    out += [f"| {a} | {b} | {c} | {d} | {e} | {f} |" for a, b, c, d, e, f in visual_rows]
    out += ["", "## Fields referenced", "", "| Table | Field | Kind | Used in | In model |", "|---|---|---|---|---|"]
    miss_keys = {(e, p, k) for e, p, k, _ in missing}
    for (entity, prop, kind), places in sorted(usage.items()):
        status = "unchecked" if model is None else ("MISSING" if (entity, prop, kind) in miss_keys else "yes")
        shown = sorted(places)
        n_hidden = sum(1 for p in shown if p in hidden_places)
        flag = f", {n_hidden} in hidden visuals or pages" if n_hidden else ""
        out.append(f"| {entity} | {prop} | {kind} | {len(shown)} place(s){flag} | {status} |")
    out += ["", "## Missing from the model", ""]
    if model is None:
        out.append(f"Not checked: {how}.")
    elif not missing:
        out.append("None: every referenced field exists in the model.")
    else:
        for entity, prop, kind, places in missing:
            out.append(f"- **{entity}[{prop}]** ({kind}) is used in:")
            out += [f"  - `{p}`{' (hidden)' if p in hidden_places else ''}" for p in places]
    out += ["", "## Literal values stored in the report", "",
            "Values saved in filters, slicer selections and titles travel with a copied report. Check each against the target.", ""]
    if col.literals:
        out += ["| Value | Where |", "|---|---|"]
        out += [f"| {v} | `{w}` |" for w, v in sorted(set(col.literals), key=lambda x: (x[1], x[0]))]
    else:
        out.append("None found.")
    out += ["", "## Bindings", ""] + [f"- {b}" for b in binding_lines]
    print("\n".join(out))
    sys.exit(1 if (problems or missing) else 0)


# --------------------------------------------------------------------------
# Semantic model: Power Query steps, relationships, measures
# --------------------------------------------------------------------------

ROW_FUNCS = {
    "removes rows": ["Table.SelectRows", "Table.RemoveRows", "Table.RemoveFirstN", "Table.RemoveLastN",
                     "Table.RemoveRowsWithErrors", "Table.SelectRowsWithErrors", "Table.Skip", "Table.FirstN",
                     "Table.LastN", "Table.Range", "Table.Distinct", "Table.AlternateRows",
                     "Table.RemoveMatchingRows", "Table.SelectColumnsWithErrors"],
    "changes row count": ["Table.Group", "Table.NestedJoin", "Table.Join", "Table.FuzzyJoin", "Table.FuzzyNestedJoin",
                          "Table.ExpandTableColumn", "Table.ExpandListColumn", "Table.Combine", "Table.Pivot",
                          "Table.Unpivot", "Table.UnpivotOtherColumns", "Table.Transpose", "Table.Repeat",
                          "Table.InsertRows"],
    "changes values": ["Table.ReplaceValue", "Table.FillDown", "Table.FillUp", "Table.TransformColumns",
                       "Table.TransformColumnTypes", "Table.ReplaceErrorValues"],
    "source": ["Value.NativeQuery", "Sql.Database", "Sql.Databases", "GoogleBigQuery.Database", "Databricks.Catalogs",
               "Databricks.Contents", "Snowflake.Databases", "Odbc.Query", "Odbc.DataSource", "PostgreSQL.Database",
               "OData.Feed", "Excel.Workbook", "Csv.Document", "Web.Contents", "AzureStorage.DataLake",
               "AzureStorage.Blobs", "SharePoint.Files", "Folder.Files"],
}
FUNC_KIND = {f: kind for kind, fs in ROW_FUNCS.items() for f in fs}
RELATIVE_DATE = re.compile(r"DateTime\.(Fixed)?LocalNow|DateTime\.FixedUtcNow|DateTimeZone\.(Fixed)?(Utc|Local)Now|Date\.From\(DateTime")
INCREMENTAL = re.compile(r"\bRange(Start|End)\b")
FILTER_DAX = ("ALLEXCEPT", "ALLSELECTED", "ALLNOBLANKROW", "REMOVEFILTERS", "ALL", "USERELATIONSHIP", "CROSSFILTER",
              "TREATAS", "KEEPFILTERS", "CALCULATE", "CALCULATETABLE", "FILTER", "SELECTEDVALUE", "LOOKUPVALUE")
STEP_RE = re.compile(r'^\s*(#"[^"]+"|[A-Za-z_][\w.]*)\s*=\s*(.*)$')
CALL_RE = re.compile(r"\b([A-Z][A-Za-z0-9]*(?:\.[A-Za-z][A-Za-z0-9]*)+)\s*\(")


def m_steps(expression):
    """[(step name, first function, full text)] from a Power Query let ... in expression."""
    lines = expression.splitlines()
    steps, current = [], None
    for line in lines:
        stripped = line.strip()
        if stripped.lower() == "let" or not stripped:
            continue
        if stripped.lower().startswith("in") and (len(stripped) == 2 or stripped[2] in " \t"):
            break
        m = STEP_RE.match(line)
        if m and (current is None or len(line) - len(line.lstrip()) <= current[3]):
            if current:
                steps.append(current[:3])
            current = [m.group(1), None, m.group(2), len(line) - len(line.lstrip())]
        elif current:
            current[2] += " " + stripped
    if current:
        steps.append(current[:3])
    out = []
    for name, _, text in steps:
        text = text.rstrip(",")
        call = CALL_RE.search(text)
        out.append((name, call.group(1) if call else "", text))
    return out


def call_args(text, func):
    """Top-level arguments of the first call to func(...) in text, respecting parentheses, braces and quoted strings."""
    start = text.find(func + "(")
    if start < 0:
        return []
    i, depth, args, cur, quote = start + len(func) + 1, 1, [], [], False
    while i < len(text):
        ch = text[i]
        if quote:
            cur.append(ch)
            if ch == '"':
                if i + 1 < len(text) and text[i + 1] == '"':
                    cur.append('"')
                    i += 1
                else:
                    quote = False
        elif ch == '"':
            quote = True
            cur.append(ch)
        elif ch in "({[":
            depth += 1
            cur.append(ch)
        elif ch in ")}]":
            depth -= 1
            if depth == 0:
                args.append("".join(cur).strip())
                return args
            cur.append(ch)
        elif ch == "," and depth == 1:
            args.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
        i += 1
    return args


def describe_step(name, func, text):
    notes = []
    kind = FUNC_KIND.get(func)
    if kind and kind != "source":
        notes.append(f"{kind}")
    for jk in re.findall(r"JoinKind\.(\w+)", text):
        notes.append(f"join kind {jk}" + (" (drops unmatched rows)" if jk in ("Inner", "RightAnti", "LeftAnti") else ""))
    if RELATIVE_DATE.search(text):
        notes.append("depends on today's date")
    if INCREMENTAL.search(text):
        notes.append("incremental-refresh range filter")
    if func in ("Table.TransformColumnTypes", "Table.TransformColumns"):
        notes.append("conversion errors become errors or nulls")
    return kind, notes


def tmdl_blocks(path):
    """Yield (keyword, header text, [body lines]) for top-level and nested blocks of a TMDL file."""
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    return lines


def read_tmdl_model(folder):
    tables, relationships = {}, []
    for f in sorted((folder / "definition").rglob("*.tmdl")):
        lines = f.read_text(encoding="utf-8-sig").splitlines()
        i = 0
        table = None
        while i < len(lines):
            raw = lines[i]
            stripped = raw.strip()
            indent = len(raw) - len(raw.lstrip(" \t"))
            if indent == 0 and stripped.startswith("table "):
                name, _ = unquote_tmdl(stripped[6:])
                table = tables.setdefault(name, {"partitions": [], "measures": []})
            elif indent == 0 and stripped.startswith("relationship"):
                rel = {}
                i += 1
                while i < len(lines) and (not lines[i].strip() or lines[i][0] in " \t"):
                    kv = re.match(r"\s*(\w+):\s*(.*)$", lines[i])
                    if kv:
                        rel[kv.group(1)] = kv.group(2).strip()
                    i += 1
                relationships.append(rel)
                continue
            elif table is not None and indent > 0:
                m = re.match(r"(partition|measure)\s+(.+)", stripped)
                if m and indent == len(raw) - len(raw.lstrip(" \t")):
                    kind = m.group(1)
                    base = indent
                    name, rest = unquote_tmdl(m.group(2))
                    rest = rest.strip()
                    body = []
                    j = i + 1
                    while j < len(lines) and (not lines[j].strip() or len(lines[j]) - len(lines[j].lstrip(" \t")) > base):
                        body.append(lines[j])
                        j += 1
                    if kind == "partition":
                        ptype = rest.lstrip("= ").split()[0] if rest.lstrip("= ") else ""
                        expr, k = [], 0
                        while k < len(body):
                            if re.match(r"\s*source\s*=", body[k]):
                                first = body[k].split("=", 1)[1].strip()
                                src_indent = len(body[k]) - len(body[k].lstrip(" \t"))
                                if first:
                                    expr.append(first)
                                k += 1
                                while k < len(body) and (not body[k].strip() or len(body[k]) - len(body[k].lstrip(" \t")) > src_indent):
                                    expr.append(body[k])
                                    k += 1
                                break
                            k += 1
                        table["partitions"].append((name, ptype, "\n".join(expr)))
                    else:
                        expr = [rest[1:].strip()] if rest.startswith("=") and rest[1:].strip() else []
                        for b in body:
                            if re.match(r"\s*(formatString|lineageTag|displayFolder|description|isHidden|dataType|annotation|changedProperty|extendedProperty|dataCategory)\b", b):
                                continue
                            if b.strip() and b.strip() != "```":
                                expr.append(b.strip())
                        table["measures"].append((name, " ".join(expr)))
                    i = j
                    continue
            i += 1
    return tables, relationships


def read_bim_model(path):
    model = json.loads(path.read_text(encoding="utf-8-sig"))
    model = model.get("model", model)
    tables = {}
    for t in model.get("tables", []):
        parts = []
        for part in t.get("partitions", []):
            src = part.get("source", {})
            expr = src.get("expression", "")
            parts.append((part.get("name", ""), src.get("type", ""), "\n".join(expr) if isinstance(expr, list) else expr))
        meas = []
        for m in t.get("measures", []):
            e = m.get("expression", "")
            meas.append((m["name"], " ".join(e) if isinstance(e, list) else e))
        tables[t["name"]] = {"partitions": parts, "measures": meas}
    rels = [{"fromColumn": f"{r.get('fromTable')}.{r.get('fromColumn')}", "toColumn": f"{r.get('toTable')}.{r.get('toColumn')}",
             "crossFilteringBehavior": r.get("crossFilteringBehavior", ""), "isActive": str(r.get("isActive", True)).lower()}
            for r in model.get("relationships", [])]
    return tables, rels


def model_report(args):
    folder = pathlib.Path(args.path).resolve()
    if not folder.is_dir():
        fail(f"not a folder: {folder}")
    if (folder / "definition").is_dir() and list((folder / "definition").rglob("*.tmdl")):
        tables, rels = read_tmdl_model(folder)
        kind = "TMDL"
    elif (folder / "model.bim").is_file():
        tables, rels = read_bim_model(folder / "model.bim")
        kind = "model.bim"
    elif (folder / "definition" / "model.bim").is_file():
        tables, rels = read_bim_model(folder / "definition" / "model.bim")
        kind = "model.bim"
    else:
        fail(f"no TMDL files or model.bim in {folder}")

    out = [f"# Semantic model inventory: {folder.name} ({kind})", "",
           "Read-only. Lists what can change the data between the source and the visuals. A flag marks a step worth "
           "checking, not a defect.", ""]
    step_rows, native, flagged = [], [], 0
    out += ["## Tables and partitions", "", "| Table | Partition | Type | Source function |", "|---|---|---|---|"]
    for tname, t in sorted(tables.items()):
        if not t["partitions"]:
            out.append(f"| {tname} | (none) | | |")
        for pname, ptype, expr in t["partitions"]:
            steps = m_steps(expr) if expr.strip() else []
            src = next((f for _, f, _ in steps if FUNC_KIND.get(f) == "source"), "")
            out.append(f"| {tname} | {pname} | {ptype} | {src} |")
            for n, (sname, func, text) in enumerate(steps, 1):
                kind_, notes = describe_step(sname, func, text)
                step_rows.append((tname, n, sname.replace("#", "").strip('"'), func, "; ".join(notes)))
                if notes:
                    flagged += 1
                if func == "Value.NativeQuery":
                    args = call_args(text, "Value.NativeQuery")
                    if len(args) >= 2 and args[1].startswith('"'):
                        native.append((tname, args[1][1:-1].replace('""', '"')))
                    elif len(args) >= 2:
                        native.append((tname, f"(built from an expression, not a literal) {args[1][:200]}"))
    out += ["", "## Power Query steps", "",
            "Steps that remove rows, change the row count or change values are flagged. Compare the row count before "
            "and after any flagged step when a figure is missing.", ""]
    if step_rows:
        out += ["| Table | # | Step | Function | Flags |", "|---|---|---|---|---|"]
        out += [f"| {t} | {n} | {s} | {f} | {fl} |" for t, n, s, f, fl in step_rows]
    else:
        out.append("No Power Query steps found (DirectQuery, calculated tables or non-M partitions).")
    out += ["", "## Native queries sent to the source", ""]
    if native:
        for t, q in native:
            out += [f"**{t}**", "", "```sql", q[:1200] + (" ..." if len(q) > 1200 else ""), "```", ""]
    else:
        out.append("None found.")
    out += ["## Relationships", "", "| From | To | Active | Cross-filter | Notes |", "|---|---|---|---|---|"]
    for r in rels:
        active = r.get("isActive", "true").lower() != "false"
        both = "both" in r.get("crossFilteringBehavior", "").lower()
        notes = []
        if not active:
            notes.append("inactive: used only by USERELATIONSHIP")
        if both:
            notes.append("bidirectional filtering")
        out.append(f"| {r.get('fromColumn', '')} | {r.get('toColumn', '')} | {'yes' if active else 'NO'} | "
                   f"{r.get('crossFilteringBehavior') or 'single'} | {'; '.join(notes)} |")
    if not rels:
        out.append("| (none found) | | | | |")
    out += ["", "## Measures that change filter context", "", "| Table | Measure | Functions | Expression |", "|---|---|---|---|"]
    shown = 0
    for tname, t in sorted(tables.items()):
        for mname, expr in t["measures"]:
            funcs = sorted({f for f in FILTER_DAX if re.search(rf"\b{f}\s*\(", expr, re.I) and f not in ("CALCULATE", "FILTER")})
            if funcs:
                shown += 1
                out.append(f"| {tname} | {mname} | {', '.join(funcs)} | `{expr[:160]}` |")
    if not shown:
        out.append("| (none) | | | |")
    out += ["", f"Summary: {len(tables)} table(s), {len(step_rows)} Power Query step(s) ({flagged} flagged), "
                f"{len(rels)} relationship(s), {len(native)} native query(ies)."]
    print("\n".join(out))


# --------------------------------------------------------------------------
# Tableau
# --------------------------------------------------------------------------

def read_twb_xml(path):
    p = pathlib.Path(path)
    if not p.is_file():
        fail(f"not a file: {p}")
    if p.suffix.lower() == ".twbx":
        with zipfile.ZipFile(p) as z:
            names = [n for n in z.namelist() if n.lower().endswith(".twb")]
            if not names:
                fail(f"{p} contains no .twb")
            info = z.getinfo(names[0])
            if info.file_size > 200 * 1024 * 1024:
                fail("the .twb inside is larger than 200 MB; refusing to parse")
            data = z.read(names[0])
    else:
        data = p.read_bytes()
    if b"<!ENTITY" in data:
        fail("the workbook declares XML entities; refusing to parse it")
    return ET.fromstring(data)


def strip_br(name):
    return name[1:-1] if name and name.startswith("[") and name.endswith("]") else (name or "")


def twb_report(args):
    root = read_twb_xml(args.path)
    problems = []
    declared = {}
    captions = {}
    for ds in root.iter("datasource"):
        name = ds.get("name")
        if not name or ds.find("connection") is None and ds.find("column") is None and name != "Parameters":
            continue
        cols = declared.setdefault(name, set())
        captions[name] = ds.get("caption") or name
        for c in ds.findall("column"):
            cols.add(strip_br(c.get("name")))
        for rec in ds.iter("metadata-record"):
            if rec.get("class") == "column":
                ln = rec.findtext("local-name")
                if ln:
                    cols.add(strip_br(ln))
    against = None
    if args.against:
        against = {f for tbl in read_against(args.against).values() for f in tbl}

    hidden_sheets = {w.get("name") for w in root.iter("window") if w.get("hidden") == "true"}
    dash_sheets = {}
    for dash in root.iter("dashboard"):
        dash_sheets[dash.get("name")] = {z.get("name") for z in dash.iter("zone") if z.get("name")}
    used_in_dash = set().union(*dash_sheets.values()) if dash_sheets else set()

    rows, literals, missing = [], [], []
    sheets = [w for w in root.iter("worksheet")]
    for ws in sheets:
        wname = ws.get("name")
        used = {}
        for dep in ws.iter("datasource-dependencies"):
            dsn = dep.get("datasource")
            for c in dep.findall("column"):
                used.setdefault((dsn, strip_br(c.get("name"))), c.get("caption"))
            for ci in dep.findall("column-instance"):
                used.setdefault((dsn, strip_br(ci.get("column"))), None)
        for flt in ws.iter("filter"):
            for gf in flt.iter("groupfilter"):
                member = gf.get("member")
                if member:
                    literals.append((wname, flt.get("column", ""), member.strip('"')))
        for (dsn, field), _ in sorted(used.items()):
            known = against if against is not None else declared.get(dsn)
            if known is not None and field not in known:
                missing.append((wname, captions.get(dsn, dsn), field))
        rows.append((wname, "HIDDEN" if wname in hidden_sheets else "",
                     "yes" if wname in used_in_dash else "no", len(used)))
        if wname in hidden_sheets and used:
            pass

    out = [f"# BI field inventory: {pathlib.Path(args.path).name}", "",
           "Read-only inventory of a Tableau workbook.", "",
           "## Worksheets", "", "| Worksheet | Hidden | Used by a dashboard | Distinct fields |", "|---|---|---|---|"]
    out += [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in rows]
    out += ["", "## Dashboards", ""]
    out += [f"- {d}: {', '.join(sorted(s)) or 'no worksheets'}" for d, s in sorted(dash_sheets.items())] or ["- none"]
    out += ["", "## Fields used but not declared in the data source" + (" (checked against --against)" if against is not None else ""), ""]
    if missing:
        out += ["| Worksheet | Data source | Field |", "|---|---|---|"]
        out += [f"| {w} | {d} | {f} |" for w, d, f in missing]
    else:
        out.append("None.")
    out += ["", "## Filter values stored in the workbook", ""]
    if literals:
        out += ["| Worksheet | Filter column | Value |", "|---|---|---|"]
        out += [f"| {w} | {c} | {v} |" for w, c, v in literals]
    else:
        out.append("None found.")
    print("\n".join(out))
    sys.exit(1 if missing else 0)


def main():
    for stream in (sys.stdout, sys.stderr):  # Windows consoles default to a legacy code page
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pbir", help="Power BI report in PBIR format")
    p.add_argument("path", help="the <name>.Report folder")
    p.add_argument("--model", help="the <name>.SemanticModel folder (default: from definition.pbir byPath)")
    p.add_argument("--against", help="file with one Table.Field per line, instead of reading the model")
    mo = sub.add_parser("model", help="Power BI semantic model: Power Query steps, relationships, measures")
    mo.add_argument("path", help="the <name>.SemanticModel folder")
    t = sub.add_parser("twb", help="Tableau workbook")
    t.add_argument("path", help=".twb or .twbx file")
    t.add_argument("--against", help="file with one field name per line")
    args = ap.parse_args()
    {"pbir": pbir_report, "twb": twb_report, "model": model_report}[args.cmd](args)


if __name__ == "__main__":
    main()
