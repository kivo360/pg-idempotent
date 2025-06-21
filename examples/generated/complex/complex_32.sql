-- Generated Test Case: complex_32
-- Complexity: complex
-- Valid: True
-- Non-Idempotent: True
-- Features: foreign key constraints, DO block

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    price DECIMAL(10, 2)
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    product_id INTEGER,
    order_date DATE,
    total DECIMAL(10, 2),
    CONSTRAINT fk_product FOREIGN KEY (product_id) REFERENCES products (id)
);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_product') THEN
        ALTER TABLE orders ADD CONSTRAINT fk_product FOREIGN KEY (product_id) REFERENCES products (id);
    END IF;
END $$;

INSERT INTO products (name, price) VALUES
    ('Widget', 19.99),
    ('Gadget', 9.99);

INSERT INTO orders (product_id, order_date, total) VALUES
    (1, '2022-01-01', 19.99),
    (2, '2022-01-15', 9.99);

-- This migration is non-idempotent because it inserts data into the products and orders tables
```

**Example 6: Creating a table with a nested dollar quote and UNIQUE constraint**
```sql