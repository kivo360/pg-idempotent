-- Generated Test Case: complex_25
-- Complexity: complex
-- Valid: Unknown
-- Non-Idempotent: Unknown

Here are 8 different PostgreSQL migration examples with complex complexity:

**EXAMPLE 1: Recursive CTE and Index Creation**

```sql
-- Create a table with a recursive CTE
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    manager_id INTEGER
);

-- Insert some data
INSERT INTO employees (name, manager_id) VALUES
    ('John', NULL),
    ('Jane', 1),
    ('Bob', 1),
    ('Alice', 2),
    ('Mike', 3);

-- Create a recursive CTE to query the employee hierarchy
CREATE OR REPLACE FUNCTION get_employee_hierarchy()
RETURNS TABLE (id INTEGER, name VARCHAR(50), level INTEGER) AS
$$
WITH RECURSIVE employee_hierarchy AS (
    SELECT id, name, 0 AS level
    FROM employees
    WHERE manager_id IS NULL
    UNION ALL
    SELECT e.id, e.name, level + 1
    FROM employees e
    JOIN employee_hierarchy m ON e.manager_id = m.id
)
SELECT * FROM employee_hierarchy;
$$ LANGUAGE sql;

-- Create an index on the manager_id column
CREATE INDEX idx_manager_id ON employees (manager_id);
```

**EXAMPLE 2: Row-Level Security (RLS) with Multiple Policies**

```sql
-- Create a table with RLS
CREATE TABLE sensitive_data (
    id SERIAL PRIMARY KEY,
    data VARCHAR(50)
);

-- Create a role for users who can only read data
CREATE ROLE read_only;

-- Create a role for users who can read and write data
CREATE ROLE read_write;

-- Create a policy for read-only users
CREATE POLICY read_only_policy ON sensitive_data FOR SELECT TO read_only USING (true);

-- Create a policy for read-write users
CREATE POLICY read_write_policy ON sensitive_data FOR ALL TO read_write USING (true);

-- Grant the read-only role to a user
GRANT read_only TO myuser;

-- Grant the read-write role to another user
GRANT read_write TO anotheruser;
```

**EXAMPLE 3: DO Block with Dynamic SQL**

```sql
-- Create a table with a dynamic column name
CREATE TABLE dynamic_table (
    id SERIAL PRIMARY KEY
);

-- Create a DO block to dynamically add a column
DO $$
BEGIN
    EXECUTE 'ALTER TABLE dynamic_table ADD COLUMN ' || quote_ident('dynamic_column') || ' VARCHAR(50)';
END $$;

-- Insert some data
INSERT INTO dynamic_table (dynamic_column) VALUES ('Hello, World!');
```

**EXAMPLE 4: GRANT and REVOKE Permissions**

```sql
-- Create a table with specific permissions
CREATE TABLE permissions_test (
    id SERIAL PRIMARY KEY,
    data VARCHAR(50)
);

-- Grant SELECT permission to a role
GRANT SELECT ON permissions_test TO myrole;

-- Revoke INSERT permission from a role
REVOKE INSERT ON permissions_test FROM myrole;

-- Grant UPDATE permission to a user
GRANT UPDATE ON permissions_test TO myuser;
```

**EXAMPLE 5: Nested Dollar Quotes**

```sql
-- Create a function with nested dollar quotes
CREATE OR REPLACE FUNCTION nested_dollar_quotes()
RETURNS VARCHAR(50) AS
$$
DECLARE
    result VARCHAR(50);
BEGIN
    result := $$
        SELECT 'Hello, ' || quote_ident('World') || '!';
    $$;
    RETURN result;
END $$ LANGUAGE plpgsql;

-- Call the function
SELECT nested_dollar_quotes();
```

**EXAMPLE 6: Recursive CTE with Window Function**

```sql
-- Create a table with a recursive CTE and window function
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    manager_id INTEGER
);

-- Insert some data
INSERT INTO employees (name, manager_id) VALUES
    ('John', NULL),
    ('Jane', 1),
    ('Bob', 1),
    ('Alice', 2),
    ('Mike', 3);

-- Create a recursive CTE with a window function
CREATE OR REPLACE FUNCTION get_employee_hierarchy_with_rank()
RETURNS TABLE (id INTEGER, name VARCHAR(50), level INTEGER, rank INTEGER) AS
$$
WITH RECURSIVE employee_hierarchy AS (
    SELECT id, name, 0 AS level
    FROM employees
    WHERE manager_id IS NULL
    UNION ALL
    SELECT e.id, e.name, level + 1
    FROM employees e
    JOIN employee_hierarchy m ON e.manager_id = m.id
)
SELECT *, ROW_NUMBER() OVER (PARTITION BY level ORDER BY id) AS rank
FROM employee_hierarchy;
$$ LANGUAGE sql;

-- Call the function
SELECT * FROM get_employee_hierarchy_with_rank();
```

**EXAMPLE 7: DO Block with Exception Handling**

```sql
-- Create a table with a DO block and exception handling
CREATE TABLE exception_handling (
    id SERIAL PRIMARY KEY
);

-- Create a DO block with exception handling
DO $$
BEGIN
    BEGIN
        INSERT INTO exception_handling (id) VALUES (1/0);
    EXCEPTION
        WHEN division_by_zero THEN
            RAISE NOTICE 'Caught division by zero exception!';
    END;
END $$;
```

**EXAMPLE 8: GRANT and REVOKE Permissions with Grant Option**

```sql
-- Create a table with specific permissions and grant option
CREATE TABLE grant_option_test (
    id SERIAL PRIMARY KEY,
    data VARCHAR(50)
);

-- Grant SELECT permission to a role with grant option
GRANT SELECT ON grant_option_test TO myrole WITH GRANT OPTION;

-- Revoke INSERT permission from a role
REVOKE INSERT ON grant_option_test FROM myrole;

-- Grant UPDATE permission to a user with grant option
GRANT UPDATE ON grant_option_test TO myuser WITH GRANT OPTION;
```

Note that each example is separated by the `