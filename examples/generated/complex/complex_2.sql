-- Generated Test Case: complex_2
-- Complexity: complex
-- Valid: Unknown
-- Non-Idempotent: Unknown

-- EXAMPLE 2: Recursive CTE for hierarchical data with dollar-quoted triggers and grants
DO $$
BEGIN
    -- Create hierarchical employee table
    CREATE TABLE employees (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        manager_id INT REFERENCES employees(id),
        salary NUMERIC(10,2),
        department TEXT
    );
    
    -- Insert recursive test data
    WITH RECURSIVE emp_data AS (
        SELECT 1 AS id, 'CEO' AS name, NULL::int AS manager_id, 100000 AS salary, 'Executive' AS department
        UNION ALL
        SELECT id+1, 
               'Employee ' || (id+1), 
               CASE WHEN id < 5 THEN 1 ELSE id-4 END, 
               50000 + (random()*20000)::numeric(10,2),
               CASE 
                   WHEN id < 5 THEN 'Management' 
                   ELSE 'Operations' 
               END
        FROM emp_data WHERE id < 10
    )
    INSERT INTO employees SELECT * FROM emp_data;
    
    -- Create complex dollar-quoted trigger function
    CREATE OR REPLACE FUNCTION check_salary_hierarchy()
    RETURNS TRIGGER LANGUAGE plpgsql AS $trigger$
    DECLARE
        manager_salary NUMERIC(10,2);
    BEGIN
        IF NEW.manager_id IS NOT NULL THEN
            SELECT salary INTO manager_salary FROM employees WHERE id = NEW.manager_id;
            IF NEW.salary > manager_salary THEN
                RAISE EXCEPTION $exception$
                    Employee (ID:%) cannot have higher salary (%) than manager (ID:%) with salary (%)
                $exception$ USING 
                    NEW.id, NEW.salary, NEW.manager_id, manager_salary;
            END IF;
        END IF;
        RETURN NEW;
    END;
    $trigger$;
    
    -- Add trigger
    CREATE TRIGGER salary_hierarchy_trigger
    BEFORE INSERT OR UPDATE ON employees
    FOR EACH ROW EXECUTE FUNCTION check_salary_hierarchy();
    
    -- Create reporting role with limited access
    CREATE ROLE reporting_role;
    
    -- Grant access with column-level permissions
    GRANT SELECT (id, name, department) ON employees TO reporting_role;
    
    -- Create a recursive view with dollar quotes
    CREATE OR REPLACE VIEW employee_hierarchy AS
    WITH RECURSIVE org_chart AS (
        SELECT id, name, manager_id, department, 0 AS level, ARRAY[id] AS path
        FROM employees WHERE manager_id IS NULL
        UNION ALL
        SELECT e.id, e.name, e.manager_id, e.department, o.level + 1, o.path || e.id
        FROM employees e
        JOIN org_chart o ON e.manager_id = o.id
    )
    SELECT 
        id,
        repeat('->', level) || ' ' || name AS hierarchy,
        department,
        level
    FROM org_chart
    ORDER BY path;
    
    -- Grant view access
    GRANT SELECT ON employee_hierarchy TO reporting_role;
    
    -- Test data validation
    BEGIN
        -- This should fail due to trigger
        UPDATE employees SET salary = 200000 WHERE id = 2;
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Trigger test passed: %', SQLERRM;
    END;
END $$;