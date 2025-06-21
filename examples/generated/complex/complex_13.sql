-- Generated Test Case: complex_13
-- Complexity: complex
-- Valid: True
-- Non-Idempotent: False
-- Features: GRANT, REVOKE

**Example 4: GRANT and REVOKE**
```sql
CREATE TABLE "grant_example" (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);

CREATE ROLE "admin";
CREATE ROLE "user";

GRANT SELECT, INSERT, UPDATE, DELETE ON "grant_example" TO "admin";
GRANT SELECT ON "grant_example" TO "user";

REVOKE INSERT, UPDATE, DELETE ON "grant_example" FROM "admin";
REVOKE SELECT ON "grant_example" FROM "user";

INSERT INTO "grant_example" (name) VALUES ('John Doe');
```