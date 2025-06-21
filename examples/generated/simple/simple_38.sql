-- Generated Test Case: simple_38
-- Complexity: simple
-- Valid: True
-- Non-Idempotent: False
-- Features: check constraints

**Example 5: Add Check Constraint**

```sql
ALTER TABLE users ADD CONSTRAINT check_age CHECK (age > 18);
```