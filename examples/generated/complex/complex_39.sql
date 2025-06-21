-- Generated Test Case: complex_39
-- Complexity: complex
-- Valid: True
-- Non-Idempotent: False
-- Features: index creation, complex query

**Example 5: Complex Index Creation**

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    price DECIMAL(10, 2),
    category VARCHAR(50)
);

CREATE INDEX idx_products_name_price ON products (name, price DESC);
CREATE INDEX idx_products_category ON products (category);
CREATE INDEX idx_products_name_category ON products (name, category);

ANALYZE products;

EXPLAIN ANALYZE SELECT * FROM products WHERE name = 'Product A' AND price > 10.00;
```