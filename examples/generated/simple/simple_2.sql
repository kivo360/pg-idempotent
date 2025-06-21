-- Generated Test Case: simple_2
-- Complexity: simple
-- Valid: Unknown
-- Non-Idempotent: Unknown

-- Migration 1: Create a table with a primary key and check constraint
-- This will fail if run twice because the table already exists
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    age INTEGER CHECK (age >= 18),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add an index on the email column for faster lookups
CREATE INDEX idx_customers_email ON customers(email);