-- Generated Test Case: medium_30
-- Complexity: medium
-- Valid: Unknown
-- Non-Idempotent: Unknown

-- Example 5: Create a materialized view
CREATE MATERIALIZED VIEW customer_summary AS
SELECT name, COUNT(*) AS order_count
FROM customers
GROUP BY name;