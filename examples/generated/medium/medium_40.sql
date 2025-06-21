-- Generated Test Case: medium_40
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: view, rule, insert rule

-- Example 7: Create a view and a rule to insert into it
CREATE VIEW customer_info AS
SELECT c.name, c.address, o.total
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id;

CREATE RULE customer_info_insert AS ON INSERT TO customer_info
DO INSTEAD (
    INSERT INTO customers (name, address) VALUES (NEW.name, NEW.address);
    INSERT INTO orders (customer_id, total) VALUES ((SELECT id FROM customers WHERE name = NEW.name), NEW.total);
);