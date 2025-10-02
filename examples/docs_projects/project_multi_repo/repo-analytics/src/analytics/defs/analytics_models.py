import dagster as dg
import pandas as pd


# start_customer_order_summary
@dg.asset(deps=["customer_data", "order_data"], group_name="analytics")
def customer_order_summary(customer_data: pd.DataFrame, order_data: pd.DataFrame) -> pd.DataFrame:
    """Summary of customer orders for analytics."""
    # Join customer and order data
    summary = (
        order_data.groupby("customer_id")
        .agg({"order_id": "count", "total_amount": ["sum", "mean"], "order_date": ["min", "max"]})
        .round(2)
    )

    # Flatten column names
    summary.columns = [
        "total_orders",
        "total_spent",
        "avg_order_value",
        "first_order",
        "last_order",
    ]
    summary = summary.reset_index()

    # Add customer information
    summary = summary.merge(
        customer_data[["customer_id", "name", "tier"]], on="customer_id", how="left"
    )

    return summary


# end_customer_order_summary


# start_product_performance
@dg.asset(deps=["order_data", "product_catalog"], group_name="analytics")
def product_performance(order_data: pd.DataFrame, product_catalog: pd.DataFrame) -> pd.DataFrame:
    """Product performance metrics for analytics dashboard."""
    # Calculate product metrics
    product_stats = (
        order_data.groupby("product")
        .agg({"order_id": "count", "quantity": "sum", "total_amount": "sum"})
        .reset_index()
    )

    product_stats.columns = ["product", "orders", "units_sold", "revenue"]

    # Add product catalog information
    performance = product_stats.merge(product_catalog, on="product", how="left")

    # Calculate profit
    performance["total_cost"] = performance["units_sold"] * performance["cost"]
    performance["profit"] = performance["revenue"] - performance["total_cost"]
    performance["profit_margin"] = (performance["profit"] / performance["revenue"] * 100).round(2)

    return performance


# end_product_performance


@dg.asset(deps=["customer_order_summary"], group_name="analytics")
def customer_segments(customer_order_summary: pd.DataFrame) -> pd.DataFrame:
    """Customer segmentation based on purchase behavior."""
    df = customer_order_summary.copy()

    # Create segments based on total spent and order frequency
    def segment_customer(row):
        if row["total_spent"] >= 100 and row["total_orders"] >= 3:
            return "High Value"
        elif row["total_spent"] >= 50 and row["total_orders"] >= 2:
            return "Medium Value"
        else:
            return "Low Value"

    df["segment"] = df.apply(segment_customer, axis=1)

    return df
