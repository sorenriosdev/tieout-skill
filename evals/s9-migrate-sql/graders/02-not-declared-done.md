---
type: llm
focus: last_message
---

PASS if the final response says the translation was not executed on either engine (or is syntax-only / not verified against data) and proposes or asks for a test that compares the results of both queries on the same data before the migration. FAIL if it presents the BigQuery query as ready or equivalent without that caveat.
