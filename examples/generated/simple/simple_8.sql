-- Generated Test Case: simple_8
-- Complexity: simple
-- Valid: True
-- Non-Idempotent: False
-- Features: table creation, primary key

**Example 7: Add Default Value**
```sql
ALTER TABLE users
ALTER COLUMN name SET DEFAULT 'John Doe';
```
This migration sets a default value of `'John Doe'` for the `name` column of the `users` table.