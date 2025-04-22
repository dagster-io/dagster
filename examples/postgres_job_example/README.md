# Example of Postgres job

This only educatable project, which purpose is show 'how to'. Same code structure can be implemented for another tasks.

## Features
- Job creation
- Fill PostgreSQL database with dagster

## Requirements
- Python
- Poetry
- PostgreSQL

## Installation
- Install poetry
```bash
pip install poetry
```
- Set up the PostgreSQL database:
   - Create a new databases:
     ```sql
     CREATE TABLE customer_purchases (
        id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        customer VARCHAR(100) NOT NULL,
        item VARCHAR(100) NOT NULL,
        sale_date DATE NOT NULL,
        sale_amount DECIMAL(10,2) NOT NULL,
        sales_region VARCHAR(50) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
     ```
     ```sql
     CREATE TABLE example_data (
        id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        customer_name VARCHAR(100) NOT NULL,
        product_name VARCHAR(100) NOT NULL,
        purchase_date DATE NOT NULL,
        amount DECIMAL(10,2) NOT NULL,
        region VARCHAR(50) NOT NULL,
        record_loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
     ```     
   - Insert some data in example_data
     ```sql
     INSERT INTO example_data 
        (customer_name, product_name, purchase_date, amount, region)
     VALUES
        ('John Smith', 'Wireless Headphones', '2023-05-15', 129.99, 'Northwest'),
        ('Emily Johnson', 'Smartphone Case', '2023-05-16', 24.95, 'Southwest'),
        ('Michael Brown', 'Bluetooth Speaker', '2023-05-17', 89.99, 'Northeast'),
        ('Sarah Davis', 'Fitness Tracker', '2023-05-18', 79.50, 'Midwest'),
        ('David Wilson', 'Laptop Backpack', '2023-05-19', 49.99, 'Southeast'),
        ('Jessica Lee', 'Wireless Charger', '2023-05-20', 19.99, 'Northwest'),
        ('Robert Taylor', 'Noise-Canceling Earbuds', '2023-05-21', 199.99, 'Southwest'),
        ('Jennifer Martinez', 'Tablet Stand', '2023-05-22', 14.95, 'Northeast'),
        ('Thomas Anderson', 'Smart Watch', '2023-05-23', 249.99, 'Midwest'),
        ('Lisa Jackson', 'Portable SSD', '2023-05-24', 119.95, 'Southeast');
     ```
- Run from examples/postgres_job_example in console
```bash
poetry install
```
- Fill environment:
```bash
 POSTGRES_HOST=
 POSTGRES_PORT=
 POSTGRES_DATABASE=
 POSTGRES_USER=
 POSTGRES_PASSWORD=
```

- Open dagster UI and run job from it

