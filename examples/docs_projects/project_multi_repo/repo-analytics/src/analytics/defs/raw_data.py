import dagster as dg
import pandas as pd


# start_customer_data_asset
@dg.asset(group_name="raw_data")
def customer_data() -> pd.DataFrame:
    """Raw customer data from CRM system."""
    # Simulated customer data
    data = {
        "customer_id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "email": [
            "alice@example.com",
            "bob@example.com",
            "charlie@example.com",
            "diana@example.com",
            "eve@example.com",
        ],
        "signup_date": ["2023-01-15", "2023-02-20", "2023-03-10", "2023-04-05", "2023-05-12"],
        "tier": ["premium", "basic", "premium", "basic", "premium"],
    }
    df = pd.DataFrame(data)
    df["signup_date"] = pd.to_datetime(df["signup_date"])

    return df


# end_customer_data_asset


@dg.asset(group_name="raw_data")
def order_data() -> pd.DataFrame:
    """Raw order data from e-commerce platform."""
    # Simulated order data
    data = {
        "order_id": [101, 102, 103, 104, 105, 106, 107, 108],
        "customer_id": [1, 2, 1, 3, 4, 2, 5, 3],
        "product": [
            "Widget A",
            "Widget B",
            "Widget C",
            "Widget A",
            "Widget B",
            "Widget A",
            "Widget C",
            "Widget B",
        ],
        "quantity": [2, 1, 3, 1, 2, 1, 4, 2],
        "price": [29.99, 49.99, 19.99, 29.99, 49.99, 29.99, 19.99, 49.99],
        "order_date": [
            "2023-01-20",
            "2023-02-25",
            "2023-03-15",
            "2023-04-10",
            "2023-05-15",
            "2023-06-01",
            "2023-06-10",
            "2023-07-05",
        ],
    }
    df = pd.DataFrame(data)
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["total_amount"] = df["quantity"] * df["price"]

    return df


@dg.asset(group_name="raw_data")
def product_catalog() -> pd.DataFrame:
    """Product catalog data."""
    # Simulated product catalog
    data = {
        "product": ["Widget A", "Widget B", "Widget C"],
        "category": ["Electronics", "Electronics", "Home"],
        "cost": [15.00, 25.00, 10.00],
        "retail_price": [29.99, 49.99, 19.99],
        "supplier": ["Supplier X", "Supplier Y", "Supplier Z"],
    }
    df = pd.DataFrame(data)

    return df
