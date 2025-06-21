-- Example 6: Create a table with a complex RLS and test GRANT/REVOKE
CREATE TABLE invoices (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER,
    total DECIMAL(10, 2)
);

INSERT INTO
    invoices (customer_id, total)
VALUES (1, 100.00),
    (2, 200.00);

CREATE POLICY invoice_select_policy ON invoices FOR
SELECT USING (
        (
            customer_id = current_setting('app.current_customer_id')::INTEGER
        )
    );

CREATE POLICY invoice_insert_policy ON invoices FOR INSERT
WITH
    CHECK (
        (
            customer_id = current_setting('app.current_customer_id')::INTEGER
        )
    );

GRANT INSERT ON invoices TO public;

REVOKE INSERT ON invoices FROM public;