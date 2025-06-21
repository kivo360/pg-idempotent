-- Generated Test Case: simple_36
-- Complexity: simple
-- Valid: True
-- Non-Idempotent: False
-- Features: constraints

**Example 3: Add Unique Constraint**

```sql
ALTER TABLE users ADD CONSTRAINT unique_email UNIQUE (email);
```