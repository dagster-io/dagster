import pandas as pd
from dagster_pipes import open_dagster_pipes

# Sample sales data (in a real scenario, this might come from a database or file)
sales_data = {
    "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
    "product": ["A", "B", "A"],
    "quantity": [10, 5, 8],
    "price": [100.0, 200.0, 100.0],
}

with open_dagster_pipes() as context:
    df = pd.DataFrame(sales_data)
    df["revenue"] = df["quantity"] * df["price"]

    # Calculate total revenue
    total_revenue = df["revenue"].sum()

    # Log the result to Dagster
    context.log.info(f"Generated revenue report with total revenue: ${total_revenue}")
    context.log.info(f"Processed {len(df)} transactions")

    # Report asset materialization with rich metadata
    context.report_asset_materialization(
        metadata={
            "total_revenue": total_revenue,
            "num_transactions": len(df),
            "average_transaction": df["revenue"].mean(),
            "top_product": df.loc[df["revenue"].idxmax(), "product"],
        }
    )
