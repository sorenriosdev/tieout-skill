---
type: llm
focus: last_message
---

PASS if the final response asks the user to decide how to handle the missing fields (remove the visuals, replace the field with another, or add it to the model) instead of silently picking a replacement or removing visuals, and does not say that it published anything. FAIL otherwise.
