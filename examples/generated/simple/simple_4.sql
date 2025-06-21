-- Generated Test Case: simple_4
-- Complexity: simple
-- Valid: True
-- Non-Idempotent: False
-- Features: foreign key, referential integrity

**Example 3: Add Check Constraint**
```sql
ALTER TABLE users
ADD CONSTRAINT chk_users_email CHECK (email LIKE '%@%.%');
```
This migration adds a check constraint to the `users` table to ensure that the `email` column contains a valid email address.