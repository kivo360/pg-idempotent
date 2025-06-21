-- Generated Test Case: extreme_3
-- Complexity: extreme
-- Valid: True
-- Non-Idempotent: False
-- Features: dynamic SQL, circular dependencies

-- Example 2: Creating a table with a circular dependency and a dynamic SQL query
CREATE OR REPLACE FUNCTION create_table()
  RETURNS void AS
$$
BEGIN
  EXECUTE 'CREATE TABLE IF NOT EXISTS table_a (id SERIAL PRIMARY KEY, table_b_id INTEGER)';
  EXECUTE 'CREATE TABLE IF NOT EXISTS table_b (id SERIAL PRIMARY KEY, table_a_id INTEGER)';
  EXECUTE 'ALTER TABLE table_a ADD CONSTRAINT fk_table_b FOREIGN KEY (table_b_id) REFERENCES table_b(id)';
  EXECUTE 'ALTER TABLE table_b ADD CONSTRAINT fk_table_a FOREIGN KEY (table_a_id) REFERENCES table_a(id)';
END;
$$ LANGUAGE plpgsql;

SELECT create_table();