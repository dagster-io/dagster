"""Raw data assets with randomly generated data containing quality issues.

These assets serve as the data sources for the pipeline,
generating data with intentional quality problems to demonstrate
validation capabilities.
"""

import dagster as dg
import pandas as pd
from dagster_duckdb import DuckDBResource

from data_quality_patterns.defs.assets.freshness import daily_freshness_policy
from data_quality_patterns.defs.resources.data_generator import (
    generate_customers,
    generate_orders,
    generate_products,
)


@dg.asset(
    group_name="raw_data",
    compute_kind="python",
    freshness_policy=daily_freshness_policy,
)
def raw_customers(
    context: dg.AssetExecutionContext,
    duckdb: DuckDBResource,
) -> pd.DataFrame:
    """Generate raw customer data with intentional quality issues.

    This asset generates customer data that contains:
    - Duplicate customer_ids (uniqueness issues)
    - Missing emails (completeness issues)
    - Invalid email formats (validity issues)
    - Incorrect name patterns (accuracy issues)
    - Inconsistent region codes (consistency issues)
    - Old created_at dates (timeliness issues)

    The failure rate is set high enough to ensure some checks fail.
    """
    # Use a seed based on a fixed value to ensure reproducible failures
    # but still have random distribution of issues
    df = generate_customers(n=100, failure_rate=0.15, seed=42)

    context.log.info(f"Generated {len(df)} customer records")
    context.log.info(f"Unique customer_ids: {df['customer_id'].nunique()}")
    context.log.info(f"Null emails: {df['email'].isna().sum()}")

    # Store in DuckDB for dbt to access
    with duckdb.get_connection() as conn:
        conn.execute("CREATE SCHEMA IF NOT EXISTS raw")
        conn.execute("DROP TABLE IF EXISTS raw.customers")
        conn.execute("CREATE TABLE raw.customers AS SELECT * FROM df")

    context.add_output_metadata(
        {
            "record_count": len(df),
            "unique_ids": int(df["customer_id"].nunique()),
            "null_emails": int(df["email"].isna().sum()),
            "regions": df["region"].value_counts().to_dict(),
        }
    )

    return df


@dg.asset(
    group_name="raw_data",
    compute_kind="python",
    deps=[raw_customers],
    freshness_policy=daily_freshness_policy,
)
def raw_orders(
    context: dg.AssetExecutionContext,
    duckdb: DuckDBResource,
    raw_customers: pd.DataFrame,
) -> pd.DataFrame:
    """Generate raw order data with intentional quality issues.

    This asset generates order data that contains:
    - Invalid customer_id references (integrity issues)
    - Duplicate order_ids (uniqueness issues)
    - Missing amounts (completeness issues)
    - Negative amounts (validity issues)
    """
    # Get valid customer IDs for referential integrity testing
    valid_customer_ids = raw_customers["customer_id"].unique().tolist()

    df = generate_orders(
        n=200,
        customer_ids=valid_customer_ids,
        failure_rate=0.15,
        seed=42,
    )

    context.log.info(f"Generated {len(df)} order records")

    # Check for integrity issues
    invalid_refs = ~df["customer_id"].isin(valid_customer_ids)
    context.log.info(f"Invalid customer references: {invalid_refs.sum()}")

    # Store in DuckDB for dbt to access
    with duckdb.get_connection() as conn:
        conn.execute("CREATE SCHEMA IF NOT EXISTS raw")
        conn.execute("DROP TABLE IF EXISTS raw.orders")
        conn.execute("CREATE TABLE raw.orders AS SELECT * FROM df")

    context.add_output_metadata(
        {
            "record_count": len(df),
            "unique_orders": int(df["order_id"].nunique()),
            "invalid_customer_refs": int(invalid_refs.sum()),
            "null_amounts": int(df["amount"].isna().sum()),
        }
    )

    return df


@dg.asset(
    group_name="raw_data",
    compute_kind="python",
    freshness_policy=daily_freshness_policy,
)
def raw_products(
    context: dg.AssetExecutionContext,
    duckdb: DuckDBResource,
) -> pd.DataFrame:
    """Generate raw product data with intentional quality issues.

    This asset generates product data for Great Expectations validation.
    """
    df = generate_products(n=50, failure_rate=0.10, seed=42)

    context.log.info(f"Generated {len(df)} product records")

    # Store in DuckDB
    with duckdb.get_connection() as conn:
        conn.execute("CREATE SCHEMA IF NOT EXISTS raw")
        conn.execute("DROP TABLE IF EXISTS raw.products")
        conn.execute("CREATE TABLE raw.products AS SELECT * FROM df")

    context.add_output_metadata(
        {
            "record_count": len(df),
            "unique_skus": int(df["sku"].nunique()),
            "null_prices": int(df["price"].isna().sum()),
        }
    )

    return df
