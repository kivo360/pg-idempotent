-- Generated Test Case: extreme_12
-- Complexity: extreme
-- Valid: True
-- Non-Idempotent: False
-- Features: jsonb, dynamic SQL queries

-- Example 3: Creating a table with a polymorphic function and a circular dependency

```sql
CREATE OR REPLACE FUNCTION public.get_product_name(p_product_id integer)
  RETURNS text AS
$BODY$
BEGIN
  RETURN (SELECT name FROM products WHERE id = p_product_id);
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;

CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  name text NOT NULL,
  category_id integer,
  FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE TABLE categories (
  id SERIAL PRIMARY KEY,
  name text NOT NULL,
  parent_id integer,
  FOREIGN KEY (parent_id) REFERENCES categories(id)
);

INSERT INTO categories (name, parent_id) VALUES ('Electronics', NULL);

INSERT INTO products (name, category_id) VALUES ('Laptop', 1);

CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  product_id integer NOT NULL,
  order_date date NOT NULL,
  FOREIGN KEY (product_id) REFERENCES products(id)
);

INSERT INTO orders (product_id, order_date) VALUES (1, '2022-01-01');
```