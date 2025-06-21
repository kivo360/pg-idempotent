-- Generated Test Case: complex_41
-- Complexity: complex
-- Valid: True
-- Non-Idempotent: True
-- Features: GRANT, REVOKE, system catalogs

**Example 7: Grant/Revoke with System Catalogs**

```sql
GRANT SELECT ON pg_catalog.pg_tables TO PUBLIC;
REVOKE SELECT ON pg_catalog.pg_tables FROM PUBLIC;

CREATE ROLE db_admin;
GRANT SELECT ON pg_catalog.pg_tables TO db_admin;

CREATE ROLE db_reader;
GRANT SELECT ON pg_catalog.pg_tables TO db_reader;

REVOKE SELECT ON pg_catalog.pg_tables FROM db_admin;
GRANT SELECT ON pg_catalog.pg_tables TO db_admin WITH GRANT OPTION;
```