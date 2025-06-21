-- Generated Test Case: extreme_10
-- Complexity: extreme
-- Valid: True
-- Non-Idempotent: False
-- Features: jsonb, dynamic SQL queries

-- Example 1: Creating a table with a polymorphic function and a circular dependency

```sql
CREATE OR REPLACE FUNCTION public.get_user_name(p_user_id integer)
  RETURNS text AS
$BODY$
BEGIN
  RETURN (SELECT name FROM users WHERE id = p_user_id);
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;

CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  name text NOT NULL,
  manager_id integer,
  FOREIGN KEY (manager_id) REFERENCES users(id)
);

INSERT INTO users (name, manager_id) VALUES ('John Doe', NULL);

CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  user_id integer NOT NULL,
  order_date date NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

INSERT INTO orders (user_id, order_date) VALUES (1, '2022-01-01');
```