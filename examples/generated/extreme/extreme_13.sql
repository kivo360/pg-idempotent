-- Generated Test Case: extreme_13
-- Complexity: extreme
-- Valid: False
-- Non-Idempotent: True
-- Features: polymorphic functions, circular dependencies

-- Example 4: Creating a table with a deeply nested structure and a dynamic SQL query

```sql
CREATE TABLE employees (
  id SERIAL PRIMARY KEY,
  name text NOT NULL,
  department jsonb NOT NULL
);

INSERT INTO employees (name, department) VALUES ('John Doe', '{"name": "Sales", "manager": {"name": "Jane Doe"}}'::jsonb);

CREATE OR REPLACE FUNCTION public.get_employee_department(p_employee_id integer)
  RETURNS jsonb AS
$BODY$
DECLARE
  v_department jsonb;
BEGIN
  SELECT department INTO v_department FROM employees WHERE id = p_employee_id;
  RETURN v_department;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;

CREATE OR REPLACE FUNCTION public.get_employee_manager(p_employee_id integer)
  RETURNS text AS
$BODY$
DECLARE
  v_manager text;
BEGIN
  SELECT department->'manager'->>'name' INTO v_manager FROM employees WHERE id = p_employee_id;
  RETURN v_manager;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;

CREATE TABLE projects (
  id SERIAL PRIMARY KEY,
  employee_id integer NOT NULL,
  project_date date NOT NULL,
  FOREIGN KEY (employee_id) REFERENCES employees(id)
);

INSERT INTO projects (employee_id, project_date) VALUES (1, '2022-01-01');
```