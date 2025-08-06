import pandas as pd

# Sample transaction data (in a real scenario, this might come from a database or API)
transaction_data = {
    "transaction_id": ["T001", "T002", "T003", "T004"],
    "customer_id": ["C123", "C456", "C789", "C123"],
    "product": ["Widget A", "Widget B", "Widget A", "Widget C"],
    "quantity": [2, 1, 3, 1],
    "price": [19.99, 39.99, 19.99, 29.99],
}

df = pd.DataFrame(transaction_data)
df["total_amount"] = df["quantity"] * df["price"]

# Calculate metrics
total_revenue = df["total_amount"].sum()
unique_customers = df["customer_id"].nunique()
avg_order_value = df["total_amount"].mean()

print("Data processing completed successfully")  # noqa: T201
print(f"Total revenue: ${total_revenue}")  # noqa: T201
print(f"Unique customers: {unique_customers}")  # noqa: T201
print(f"Average order value: ${avg_order_value:.2f}")  # noqa: T201
