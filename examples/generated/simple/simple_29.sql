-- Generated Test Case: simple_29
-- Complexity: simple
-- Valid: True
-- Non-Idempotent: False
-- Features: foreign key

-- Example 4: Add a check constraint to a column
ALTER TABLE users ADD CONSTRAINT chk_users_email CHECK (email LIKE '%@%.%');