-- Generated Test Case: medium_24
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: partitioned tables, range partitioning

**

**Example 7: Creating a partitioned table**
```sql
-- Create a partitioned table
CREATE TABLE orders_partitioned (
  id SERIAL PRIMARY KEY,
  customer_id INTEGER NOT NULL,
  order_date TIMESTAMP NOT NULL DEFAULT NOW(),
  total DECIMAL(10, 2) NOT NULL
) PARTITION BY RANGE (EXTRACT(YEAR FROM order_date));

-- Create partitions for each year
CREATE TABLE orders_partitioned_2022 PARTITION OF orders_partitioned
FOR VALUES FROM (2022) TO (2023);

CREATE TABLE orders_partitioned_2023 PARTITION OF orders_partitioned
FOR VALUES FROM (2023) TO (2024);
```

**