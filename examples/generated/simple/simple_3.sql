-- Generated Test Case: simple_3
-- Complexity: simple
-- Valid: True
-- Non-Idempotent: False
-- Features: check constraint

**Example 2: Add Index on Column**
```sql
CREATE INDEX idx_users_name ON users (name);
```
This migration adds an index on the `name` column of the `users` table.