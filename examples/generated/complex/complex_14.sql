-- Generated Test Case: complex_14
-- Complexity: complex
-- Valid: True
-- Non-Idempotent: False
-- Features: window functions, RANK, LAG, LEAD

**Example 5: Window Functions**
```sql
CREATE TABLE "window_example" (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    salary DECIMAL(10, 2) NOT NULL
);

INSERT INTO "window_example" (name, salary) VALUES ('John Doe', 50000.00);
INSERT INTO "window_example" (name, salary) VALUES ('Jane Doe', 60000.00);
INSERT INTO "window_example" (name, salary) VALUES ('Bob Smith', 70000.00);

SELECT name, salary,
       RANK() OVER (ORDER BY salary DESC) AS rank,
       LAG(salary) OVER (ORDER BY salary DESC) AS prev_salary,
       LEAD(salary) OVER (ORDER BY salary DESC) AS next_salary
FROM "window_example";
```