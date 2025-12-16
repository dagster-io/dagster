from datetime import datetime
from typing import Any

import pandas as pd
from dagster import AssetExecutionContext, asset

from ..resources import PostgresResource, SnowflakeResource


@asset(group_name="etl_pipeline")
def extract_sales_data(
    context: AssetExecutionContext,
    database: PostgresResource,
) -> pd.DataFrame:
    query = """
        SELECT
            sale_id,
            customer_id,
            product_id,
            amount,
            sale_date,
            region
        FROM sales
        WHERE sale_date >= CURRENT_DATE - INTERVAL '1 day'
    """

    df = database.query(query)

    context.log.info(f"Extracted {len(df)} sales records")
    context.add_output_metadata(
        {
            "record_count": len(df),
            "extraction_timestamp": datetime.now().isoformat(),
        }
    )

    return df


@asset(deps=[extract_sales_data], group_name="etl_pipeline")
def transform_sales_data(
    context: AssetExecutionContext,
    extract_sales_data: pd.DataFrame,
) -> pd.DataFrame:
    if extract_sales_data.empty:
        context.log.warning("No data to transform")
        return pd.DataFrame()

    df_transformed = (
        extract_sales_data.groupby("region")
        .agg(
            {
                "amount": "sum",
                "sale_id": "count",
            }
        )
        .reset_index()
    )

    df_transformed.columns = ["region", "total_revenue", "sale_count"]

    df_transformed["avg_transaction_value"] = (
        df_transformed["total_revenue"] / df_transformed["sale_count"]
    )

    context.log.info(f"Transformed to {len(df_transformed)} regional summaries")
    context.add_output_metadata(
        {
            "region_count": len(df_transformed),
            "total_revenue": float(df_transformed["total_revenue"].sum()),
        }
    )

    return df_transformed


@asset(deps=[transform_sales_data], group_name="etl_pipeline")
def load_to_warehouse(
    context: AssetExecutionContext,
    transform_sales_data: pd.DataFrame,
    snowflake: SnowflakeResource,
) -> dict[str, Any]:
    if transform_sales_data.empty:
        context.log.warning("No data to load")
        return {"loaded": 0}

    snowflake.write_table("regional_sales_summary", transform_sales_data, if_exists="replace")

    context.log.info(f"Loaded {len(transform_sales_data)} records to warehouse")

    context.add_output_metadata(
        {
            "loaded_count": len(transform_sales_data),
            "load_timestamp": datetime.now().isoformat(),
            "table_name": "regional_sales_summary",
        }
    )

    return {
        "loaded": len(transform_sales_data),
        "timestamp": datetime.now().isoformat(),
    }
