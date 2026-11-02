"""Build the synthetic Power BI project used by the clone-bi example, tests and scenario.

Layout it writes next to this script:
  Alpha.SemanticModel/   source model (Sales has Channel and a Variance measure)
  Beta.SemanticModel/   target model (no Channel column, no Variance measure)
  Alpha.Report/          source report
  Beta.Report/          a fresh copy of Alpha.Report, as after "Save as" or a
                         folder copy, with the problems cloning leaves behind:
                         fields missing in the target model (one in a hidden
                         visual, one in a hidden page), a title and a slicer
                         selection from the source, a stale active page, the
                         source's published-report binding, and a copied
                         filter name used twice.

Everything is invented and was written by hand from the public PBIR schemas
(microsoft/json-schemas) and Microsoft Learn documentation. It has not been
opened in Power BI Desktop.

Usage: python examples/clone-bi-synthetic/make_fixture.py
"""
import json
import pathlib
import shutil

HERE = pathlib.Path(__file__).resolve().parent
SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def col(entity, prop):
    return {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}


def measure(entity, prop):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}


def projection(field, name):
    return {"field": field, "queryRef": name, "active": True}


def in_filter(entity, prop, values):
    """A saved selection: FilterDefinition with a From alias, as Desktop writes it."""
    return {
        "Version": 2,
        "From": [{"Name": "t", "Entity": entity, "Type": 0}],
        "Where": [{"Condition": {"In": {
            "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "t"}}, "Property": prop}}],
            "Values": [[{"Literal": {"Value": f"'{v}'"}}] for v in values]}}}],
    }


def visual(name, vtype, x, y, projections, hidden=False, title=None, filters=None, objects=None):
    body = {
        "$schema": f"{SCHEMA}/visualContainer/2.13.0/schema.json",
        "name": name,
        "position": {"x": x, "y": y, "z": 0, "height": 200, "width": 300},
        "visual": {"visualType": vtype,
                   "query": {"queryState": {role: {"projections": projs} for role, projs in projections.items()}}},
    }
    if title:
        body["visual"]["visualContainerObjects"] = {"title": [{"properties": {
            "text": {"expr": {"Literal": {"Value": f"'{title}'"}}}}}]}
    if objects:
        body["visual"]["objects"] = objects
    if hidden:
        body["isHidden"] = True
    if filters:
        body["filterConfig"] = {"filters": filters}
    return body


SALES_M = """\t\t\t\tlet
\t\t\t\t    Source = Value.NativeQuery(Sql.Database("synthetic-server", "synthetic-db"), "select order_id, store_id, period, amount, channel from dbo.sales", null, [EnableFolding = true]),
\t\t\t\t    #"Filtered Rows" = Table.SelectRows(Source, each [period] >= "2026-01" and [amount] <> null),
\t\t\t\t    #"Removed Duplicates" = Table.Distinct(#"Filtered Rows", {"order_id"}),
\t\t\t\t    #"Merged Stores" = Table.NestedJoin(#"Removed Duplicates", {"store_id"}, Stores, {"store_id"}, "Stores", JoinKind.Inner),
\t\t\t\t    #"Changed Type" = Table.TransformColumnTypes(#"Merged Stores", {{"amount", type number}})
\t\t\t\tin
\t\t\t\t    #"Changed Type"
"""


def tmdl_model(sales_columns, sales_measures):
    cols = "".join(f"\tcolumn {c}\n\t\tdataType: string\n\t\tsourceColumn: {c}\n\n" for c in sales_columns)
    meas = "".join(f"\tmeasure '{n}' = {e}\n\t\tformatString: 0\n\n" for n, e in sales_measures)
    part = f"\tpartition Sales = m\n\t\tmode: import\n\t\tsource =\n{SALES_M}\n"
    sales = f"table Sales\n\tlineageTag: 00000000-0000-0000-0000-000000000001\n\n{meas}{cols}{part}"
    store = ("table Store\n\tlineageTag: 00000000-0000-0000-0000-000000000002\n\n"
             "\tcolumn StoreId\n\t\tdataType: string\n\t\tsourceColumn: StoreId\n\n"
             "\tcolumn StoreName\n\t\tdataType: string\n\t\tsourceColumn: StoreName\n\n"
             "\tcolumn SegmentCode\n\t\tdataType: string\n\t\tsourceColumn: SegmentCode\n\n")
    return sales, store


def build_model(folder, sales_columns, sales_measures):
    write_json(folder / "definition.pbism", {"version": "4.0", "settings": {}})
    write_text(folder / "definition" / "model.tmdl", "model Model\n\tculture: en-US\n\nref table Sales\nref table Store\n")
    sales, store = tmdl_model(sales_columns, sales_measures)
    write_text(folder / "definition" / "tables" / "Sales.tmdl", sales)
    write_text(folder / "definition" / "tables" / "Store.tmdl", store)
    write_text(folder / "definition" / "relationships.tmdl",
               "relationship 00000000-0000-0000-0000-0000000000a1\n\tfromColumn: Sales.StoreId\n\ttoColumn: Store.StoreId\n\n"
               "relationship 00000000-0000-0000-0000-0000000000a2\n\tcrossFilteringBehavior: bothDirections\n"
               "\tisActive: false\n\tfromColumn: Sales.OrderId\n\ttoColumn: Store.StoreId\n")


def build_report(folder, model_dir_name, report_id):
    d = folder / "definition"
    write_json(folder / "definition.pbir", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0", "datasetReference": {"byPath": {"path": f"../{model_dir_name}"}}})
    write_json(folder / ".pbi" / "localSettings.json", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/localSettings/1.0.0/schema.json",
        "remoteArtifacts": [{"reportId": report_id}]})
    write_json(d / "version.json", {"$schema": f"{SCHEMA}/versionMetadata/1.0.0/schema.json", "version": "2.0.0"})
    write_json(d / "report.json", {"$schema": f"{SCHEMA}/report/3.3.0/schema.json",
                                   "themeCollection": {"baseTheme": {"name": "CY24SU06", "reportVersionAtImport": "5.55", "type": "SharedResources"}}})
    write_json(d / "pages" / "pages.json", {"$schema": f"{SCHEMA}/pagesMetadata/1.1.0/schema.json",
                                            "pageOrder": ["overview", "detail"], "activePageName": "overview"})
    page = lambda name, title, extra=None: {"$schema": f"{SCHEMA}/page/2.1.0/schema.json", "name": name,
                                            "displayName": title, "displayOption": "FitToPage", "height": 720, "width": 1280, **(extra or {})}
    write_json(d / "pages" / "overview" / "page.json", page("overview", "Overview"))
    write_json(d / "pages" / "detail" / "page.json", page("detail", "Detail", {"visibility": "HiddenInViewMode"}))

    ov = d / "pages" / "overview" / "visuals"
    write_json(ov / "total_card" / "visual.json", visual(
        "total_card", "card", 0, 0, {"Values": [projection(measure("Sales", "Total Amount"), "Sales.Total Amount")]},
        title="Alpha Unit Revenue"))
    write_json(ov / "by_store" / "visual.json", visual(
        "by_store", "tableEx", 320, 0, {"Values": [projection(col("Store", "StoreName"), "Store.StoreName"),
                                                   projection(measure("Sales", "Total Amount"), "Sales.Total Amount")]}))
    write_json(ov / "by_channel" / "visual.json", visual(
        "by_channel", "clusteredColumnChart", 0, 220, {"Category": [projection(col("Sales", "Channel"), "Sales.Channel")],
                                                       "Y": [projection(measure("Sales", "Total Amount"), "Sales.Total Amount")]}))
    write_json(ov / "segment_slicer" / "visual.json", visual(
        "segment_slicer", "slicer", 320, 220, {"Values": [projection(col("Store", "SegmentCode"), "Store.SegmentCode")]},
        objects={"general": [{"properties": {"filter": {"filter": in_filter("Store", "SegmentCode", ["A1"])}}}]}))
    write_json(ov / "old_variance" / "visual.json", visual(
        "old_variance", "card", 0, 440, {"Values": [projection(measure("Sales", "Variance"), "Sales.Variance")]}, hidden=True))
    write_json(d / "pages" / "detail" / "visuals" / "detail_table" / "visual.json", visual(
        "detail_table", "tableEx", 0, 0, {"Values": [projection(col("Sales", "OrderId"), "Sales.OrderId"),
                                                     projection(col("Sales", "Channel"), "Sales.Channel")]},
        filters=[{"name": "saved_filter", "field": col("Store", "SegmentCode"), "type": "Categorical",
                  "filter": in_filter("Store", "SegmentCode", ["A1"])}]))


def main():
    for name in ("Alpha.SemanticModel", "Beta.SemanticModel", "Alpha.Report", "Beta.Report"):
        shutil.rmtree(HERE / name, ignore_errors=True)
    total = [("Total Amount", "SUM(Sales[Amount])"),
             ("Amount All Stores", "CALCULATE(SUM(Sales[Amount]), ALL(Store))")]
    build_model(HERE / "Alpha.SemanticModel", ["OrderId", "StoreId", "Period", "Amount", "Channel"],
                total + [("Variance", "[Total Amount] - 0")])
    build_model(HERE / "Beta.SemanticModel", ["OrderId", "StoreId", "Period", "Amount"], total)
    build_report(HERE / "Alpha.Report", "Alpha.SemanticModel", "11111111-1111-1111-1111-111111111111")

    # Beta.Report starts as a plain copy of Alpha.Report, then points at its own model.
    shutil.copytree(HERE / "Alpha.Report", HERE / "Beta.Report")
    pbir = HERE / "Beta.Report" / "definition.pbir"
    data = json.loads(pbir.read_text(encoding="utf-8"))
    data["datasetReference"]["byPath"]["path"] = "../Beta.SemanticModel"
    pbir.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    # A page was deleted from the copy but the active page still points at it.
    pages = HERE / "Beta.Report" / "definition" / "pages" / "pages.json"
    meta = json.loads(pages.read_text(encoding="utf-8"))
    meta["activePageName"] = "old_overview"
    pages.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    # The report-level copy of a filter reuses a name already used on the detail page.
    report = HERE / "Beta.Report" / "definition" / "report.json"
    rdata = json.loads(report.read_text(encoding="utf-8"))
    rdata["filterConfig"] = {"filters": [{"name": "saved_filter", "field": col("Store", "SegmentCode"),
                                          "type": "Categorical", "filter": in_filter("Store", "SegmentCode", ["A1"])}]}
    report.write_text(json.dumps(rdata, indent=2) + "\n", encoding="utf-8")
    print("wrote Alpha.* and Beta.* under", HERE)


if __name__ == "__main__":
    main()
