-- Example 3: Create a table with a complex RLS and test DO block
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER,
    total DECIMAL(10, 2)
);

INSERT INTO
    orders (customer_id, total)
VALUES (1, 100.00),
    (2, 200.00);

CREATE POLICY order_select_policy ON orders FOR
SELECT USING (
        (
            customer_id = current_setting('app.current_customer_id')::INTEGER
        )
    );

CREATE POLICY order_insert_policy ON orders FOR INSERT
WITH
    CHECK (
        (
            customer_id = current_setting('app.current_customer_id')::INTEGER
        )
    );

DO $$
BEGIN
    PERFORM set_config('app.current_customer_id', '1', true);
    INSERT INTO orders (customer_id, total) VALUES (1, 300.00);
    PERFORM set_config('app.current_customer_id', '2', true);
    INSERT INTO orders (customer_id, total) VALUES (2, 400.00);
END;
$$ LANGUAGE plpgsql;