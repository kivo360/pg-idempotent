-- Generated Test Case: extreme_14
-- Complexity: extreme
-- Valid: True
-- Non-Idempotent: False
-- Features: jsonb, dynamic SQL queries

-- Example 5: Creating a table with a polymorphic function and a circular dependency

```sql
CREATE OR REPLACE FUNCTION public.get_supplier_name(p_supplier_id integer)
  RETURNS text AS
$BODY$
BEGIN
  RETURN (SELECT name FROM suppliers WHERE id = p_supplier_id);
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;

CREATE TABLE suppliers (
  id SERIAL PRIMARY KEY,
  name text NOT NULL,
  contact_id integer,
  FOREIGN KEY (contact_id) REFERENCES contacts(id)
);

CREATE TABLE contacts (
  id SERIAL PRIMARY KEY,
  name text NOT NULL,
  supplier_id integer,
  FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
);

INSERT INTO contacts (name, supplier_id) VALUES ('Jane Doe', NULL);

INSERT INTO suppliers (name, contact_id) VALUES ('ABC Inc.', 1);

CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  supplier_id integer NOT NULL,
  order_date date NOT NULL,
  FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
);

INSERT INTO orders (supplier_id, order_date) VALUES (1, '2022-01-01');
```