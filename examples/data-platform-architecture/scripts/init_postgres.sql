-- Initialize demo database with sample tables

CREATE TABLE IF NOT EXISTS sales (
    sale_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    sale_date TIMESTAMP NOT NULL,
    region VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample sales data
INSERT INTO sales (sale_id, customer_id, product_id, amount, sale_date, region)
SELECT
    'sale-' || LPAD(i::text, 4, '0'),
    'cust-' || LPAD((i % 100)::text, 3, '0'),
    'prod-' || LPAD((i % 50)::text, 3, '0'),
    10.0 + (i % 100) * 5.0,
    CURRENT_TIMESTAMP - INTERVAL '1 day' * (i % 30),
    (ARRAY['North', 'South', 'East', 'West'])[1 + (i % 4)]
FROM generate_series(1, 1000) AS i
ON CONFLICT (sale_id) DO NOTHING;

-- Insert sample customer data
INSERT INTO customers (customer_id, name, email, updated_at)
SELECT
    'cust-' || LPAD(i::text, 3, '0'),
    'Customer ' || i,
    'customer' || i || '@example.com',
    CURRENT_TIMESTAMP - INTERVAL '1 hour' * (i % 24)
FROM generate_series(1, 100) AS i
ON CONFLICT (customer_id) DO NOTHING;
