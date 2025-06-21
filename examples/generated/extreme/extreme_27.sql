-- Generated Test Case: extreme_27
-- Complexity: extreme
-- Valid: True
-- Non-Idempotent: False
-- Features: circular dependencies, foreign keys

CREATE TABLE table_a (
  id SERIAL PRIMARY KEY,
  table_b_id INTEGER NOT NULL
);

CREATE TABLE table_b (
  id SERIAL PRIMARY KEY,
  table_a_id INTEGER NOT NULL
);

ALTER TABLE table_a
ADD CONSTRAINT fk_table_a_table_b FOREIGN KEY (table_b_id) REFERENCES table_b (id);

ALTER TABLE table_b
ADD CONSTRAINT fk_table_b_table_a FOREIGN KEY (table_a_id) REFERENCES table_a (id);
```

**EXAMPLE 3: Creating a table with a deeply nested structure**

```sql