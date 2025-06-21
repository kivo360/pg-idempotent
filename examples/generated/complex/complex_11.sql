-- Generated Test Case: complex_11
-- Complexity: complex
-- Valid: True
-- Non-Idempotent: False
-- Features: RLS, policies

**Example 2: Complex Row-Level Security (RLS)**
```sql
CREATE TABLE "rls_example" (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    department VARCHAR(50) NOT NULL
);

CREATE POLICY "rls_policy"
ON "rls_example"
FOR SELECT
TO PUBLIC
USING (department = 'Sales')
WITH CHECK (department = 'Sales');

CREATE ROLE "sales_team";
GRANT SELECT ON "rls_example" TO "sales_team";

CREATE ROLE "marketing_team";
GRANT SELECT ON "rls_example" TO "marketing_team";

INSERT INTO "rls_example" (name, department) VALUES ('John Doe', 'Sales');
INSERT INTO "rls_example" (name, department) VALUES ('Jane Doe', 'Marketing');
```