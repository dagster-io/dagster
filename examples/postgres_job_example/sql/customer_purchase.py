CUSTOMER_PURCHASE_INSERT_QUERY = """
TRUNCATE customer_purchases;
INSERT INTO customer_purchases 
    (customer, item, sale_date, sale_amount, sales_region)
SELECT 
    customer_name, 
    product_name, 
    purchase_date, 
    amount, 
    region 
FROM example_data
"""
