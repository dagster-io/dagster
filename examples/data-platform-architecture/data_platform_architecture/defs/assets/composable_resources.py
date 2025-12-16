import pandas as pd
from dagster import AssetExecutionContext, asset

from ..resources import PostgresResource, RESTAPIResource, S3Resource


@asset(group_name="composable_resources")
def extract_customer_data(
    context: AssetExecutionContext,
    database: PostgresResource,
) -> pd.DataFrame:
    query = "SELECT * FROM customers WHERE updated_at >= CURRENT_DATE - INTERVAL '1 day'"
    df = database.query(query)
    context.log.info(f"Extracted {len(df)} customer records")
    return df


@asset(group_name="composable_resources")
def extract_api_data(
    context: AssetExecutionContext,
    api: RESTAPIResource,
) -> pd.DataFrame:
    response = api.get("/data/events", params={"limit": 1000})
    data = response.get("data", [])
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    context.log.info(f"Extracted {len(df)} records from API")
    return df


@asset(deps=[extract_customer_data], group_name="composable_resources")
def load_to_storage(
    context: AssetExecutionContext,
    extract_customer_data: pd.DataFrame,
    storage: S3Resource,
) -> str:
    if context.run is None:
        raise ValueError("Run context is required")
    path = f"customers/{context.run.run_id}.parquet"
    storage.write(path, extract_customer_data)
    context.log.info(f"Loaded data to storage: {path}")
    return path
