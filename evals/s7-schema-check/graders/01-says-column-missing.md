---
type: llm
focus: last_message
---

data/dim_store.csv has the columns store_id, store_name, segment_code and is_active: there is no segment_name. PASS if the final response says that segment_name does not exist in dim_store (or in the export) and asks which column is meant, or offers segment_code as a candidate for the user to confirm. FAIL if it claims to have added segment_name without noticing it is missing.
