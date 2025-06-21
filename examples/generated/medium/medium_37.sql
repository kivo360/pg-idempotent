-- Generated Test Case: medium_37
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: materialized view, refresh

-- Example 4: Create a table with Row-Level Security (RLS) and a policy
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id integer NOT NULL,
    total decimal(10, 2) NOT NULL
);

CREATE POLICY orders_policy ON orders
TO PUBLIC
USING (customer_id = current_user_id());