-- Generated Test Case: simple_6
-- Complexity: simple
-- Valid: True
-- Non-Idempotent: False
-- Features: enum type, enum column

**Example 5: Add Unique Constraint**
```sql
ALTER TABLE users
ADD CONSTRAINT uniq_users_email UNIQUE (email);
```
This migration adds a unique constraint to the `email` column of the `users` table.