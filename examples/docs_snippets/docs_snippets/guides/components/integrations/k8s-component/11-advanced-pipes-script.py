import pandas as pd
from dagster_pipes import open_dagster_pipes

# Sample transaction data (in a real scenario, this might come from a database or API)
transaction_data = {
    "transaction_id": ["T001", "T002", "T003", "T004"],
    "customer_id": ["C123", "C456", "C789", "C123"],
    "product": ["Widget A", "Widget B", "Widget A", "Widget C"],
    "quantity": [2, 1, 3, 1],
    "price": [19.99, 39.99, 19.99, 29.99],
}

with open_dagster_pipes() as context:
    df = pd.DataFrame(transaction_data)
    df["total_amount"] = df["quantity"] * df["price"]

    # Calculate metrics
    total_revenue = df["total_amount"].sum()
    unique_customers = df["customer_id"].nunique()
    avg_order_value = df["total_amount"].mean()

    # Log the results to Dagster
    context.log.info("Data processing completed successfully")
    context.log.info(f"Processed {len(df)} transactions")

    # Report asset materialization with rich metadata
    context.report_asset_materialization(
        metadata={
            "total_revenue": total_revenue,
            "unique_customers": unique_customers,
            "avg_order_value": avg_order_value,
            "num_transactions": len(df),
            "top_product": df.groupby("product")["total_amount"].sum().idxmax(),
        }
    )
