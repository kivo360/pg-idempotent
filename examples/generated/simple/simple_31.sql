-- Generated Test Case: simple_31
-- Complexity: simple
-- Valid: True
-- Non-Idempotent: False
-- Features: constraints

-- Example 6: Add a unique constraint to a column
ALTER TABLE orders ADD CONSTRAINT unq_orders_user_id UNIQUE (user_id);