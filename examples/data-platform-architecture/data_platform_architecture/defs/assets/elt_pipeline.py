from datetime import datetime
from typing import Any

import pandas as pd
from dagster import AssetExecutionContext, asset

from ..resources import RESTAPIResource, SnowflakeResource


@asset(group_name="elt_pipeline")
def extract_raw_clickstream(
    context: AssetExecutionContext,
    api: RESTAPIResource,
) -> pd.DataFrame:
    response = api.get("/clickstream", params={"limit": 500})
    events = response.get("data", [])
    df = pd.DataFrame(events)

    context.log.info(f"Extracted {len(df)} raw clickstream events")
    context.add_output_metadata(
        {
            "record_count": len(df),
            "extraction_timestamp": datetime.now().isoformat(),
            "data_format": "raw",
        }
    )

    return df


@asset(deps=[extract_raw_clickstream], group_name="elt_pipeline")
def load_raw_to_warehouse(
    context: AssetExecutionContext,
    extract_raw_clickstream: pd.DataFrame,
    snowflake: SnowflakeResource,
) -> dict[str, Any]:
    if extract_raw_clickstream.empty:
        context.log.warning("No data to load")
        return {"loaded": 0}

    snowflake.write_table("bronze_clickstream", extract_raw_clickstream, if_exists="append")

    context.log.info(f"Loading {len(extract_raw_clickstream)} raw records to warehouse")

    context.add_output_metadata(
        {
            "loaded_count": len(extract_raw_clickstream),
            "load_timestamp": datetime.now().isoformat(),
            "table_name": "bronze_clickstream",
            "layer": "bronze",
        }
    )

    return {
        "loaded": len(extract_raw_clickstream),
        "timestamp": datetime.now().isoformat(),
        "layer": "bronze",
    }


@asset(deps=[load_raw_to_warehouse], group_name="elt_pipeline")
def transform_in_warehouse(
    context: AssetExecutionContext,
    load_raw_to_warehouse: dict[str, Any],
    snowflake: SnowflakeResource,
) -> dict[str, Any]:
    context.log.info("Transforming data in warehouse via SQL")

    transform_sql = """
        CREATE OR REPLACE TABLE silver_clickstream AS
        SELECT
            user_id,
            event_type,
            COUNT(event_id) as event_count
        FROM bronze_clickstream
        GROUP BY user_id, event_type
    """

    snowflake.execute(transform_sql)
    context.log.info("Created silver layer with aggregated records")

    return {
        "transformed": True,
        "timestamp": datetime.now().isoformat(),
        "layer": "silver",
    }
