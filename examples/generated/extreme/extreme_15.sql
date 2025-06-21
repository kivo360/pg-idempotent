-- Generated Test Case: extreme_15
-- Complexity: extreme
-- Valid: False
-- Non-Idempotent: True
-- Features: polymorphic functions, circular dependencies

-- Example 6: Creating a table with a deeply nested structure and a dynamic SQL query

```sql
CREATE TABLE customers (
  id SERIAL PRIMARY KEY,
  name text NOT NULL,
  address jsonb NOT NULL
);

INSERT INTO customers (name, address) VALUES ('John Doe', '{"street": "123 Main St", "city": "Anytown", "state": "CA", "zip": "12345"}'::jsonb);

CREATE OR REPLACE FUNCTION public.get_customer_address(p_customer_id integer)
  RETURNS jsonb AS
$BODY$
DECLARE
  v_address jsonb;
BEGIN
  SELECT address INTO v_address FROM customers WHERE id = p_customer_id;
  RETURN v_address;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;

CREATE OR REPLACE FUNCTION public.get_customer_city(p_customer_id integer)
  RETURNS text AS
$BODY$
DECLARE
  v_city text;
BEGIN
  SELECT address->>'city' INTO v_city FROM customers WHERE id = p_customer_id;
  RETURN v_city;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;

CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  customer_id integer NOT NULL,
  order_date date NOT NULL,
  FOREIGN KEY (customer_id) REFERENCES customers(id)
);

INSERT INTO orders (customer_id, order_date) VALUES (1, '2022-01-01');
```