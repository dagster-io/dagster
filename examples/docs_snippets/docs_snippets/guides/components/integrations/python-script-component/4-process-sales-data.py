import pandas as pd

# Sample sales data (in a real scenario, this might come from a database or file)
sales_data = {
    "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
    "product": ["A", "B", "A"],
    "quantity": [10, 5, 8],
    "price": [100.0, 200.0, 100.0],
}

df = pd.DataFrame(sales_data)
df["revenue"] = df["quantity"] * df["price"]

# Calculate total revenue
total_revenue = df["revenue"].sum()

print(f"Generated revenue report with total revenue: ${total_revenue}")  # noqa: T201
print(f"Number of transactions: {len(df)}")  # noqa: T201
print(f"Average transaction: ${df['revenue'].mean():.2f}")  # noqa: T201
