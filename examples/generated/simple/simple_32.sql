-- Generated Test Case: simple_32
-- Complexity: simple
-- Valid: True
-- Non-Idempotent: False
-- Features: views

-- Example 7: Create a view
CREATE VIEW user_orders AS
SELECT u.name, o.order_date
FROM users u
JOIN orders o ON u.id = o.user_id;