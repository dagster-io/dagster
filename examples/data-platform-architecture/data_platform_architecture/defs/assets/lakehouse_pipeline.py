from datetime import datetime

import dagster._check as check
import pandas as pd
from dagster import AssetExecutionContext, asset

from ..resources import RESTAPIResource, S3Resource


@asset(group_name="lakehouse_pipeline")
def extract_sensor_data(
    context: AssetExecutionContext,
    api: RESTAPIResource,
) -> pd.DataFrame:
    response = api.get("/sensors", params={"limit": 1000})
    data = response.get("data", [])
    df = pd.DataFrame(data)

    context.log.info(f"Extracted {len(df)} sensor readings")
    context.add_output_metadata(
        {
            "record_count": len(df),
            "extraction_timestamp": datetime.now().isoformat(),
        }
    )

    return df


@asset(deps=[extract_sensor_data], group_name="lakehouse_pipeline")
def load_bronze_layer(
    context: AssetExecutionContext,
    extract_sensor_data: pd.DataFrame,
    storage: S3Resource,
) -> str:
    if extract_sensor_data.empty:
        raise ValueError("No data to load to bronze layer")

    run_id = context.run.run_id
    bronze_key = f"bronze/sensor_data/{run_id}.parquet"

    storage.write_parquet(bronze_key, extract_sensor_data)

    context.log.info(f"Loaded to bronze layer: s3://{storage.bucket}/{bronze_key}")
    context.add_output_metadata(
        {
            "bronze_path": f"s3://{storage.bucket}/{bronze_key}",
            "record_count": len(extract_sensor_data),
            "layer": "bronze",
        }
    )

    return bronze_key


@asset(deps=[load_bronze_layer], group_name="lakehouse_pipeline")
def process_silver_layer(
    context: AssetExecutionContext,
    load_bronze_layer: str,
    storage: S3Resource,
) -> str:
    df = storage.read_parquet(load_bronze_layer)

    if df.empty:
        raise ValueError("No data in bronze layer to process")

    df_clean = df[df["temperature"].notna()].copy()
    df_clean = df_clean.drop_duplicates(subset=["sensor_id", "timestamp"])  # type: ignore[call-overload]
    df_clean = df_clean[(df_clean["temperature"] >= -50) & (df_clean["temperature"] <= 100)]
    df_clean = df_clean[(df_clean["humidity"] >= 0) & (df_clean["humidity"] <= 100)]
    df_clean["timestamp"] = pd.to_datetime(df_clean["timestamp"])  # type: ignore[index]

    run_id = context.run.run_id
    silver_key = f"silver/sensor_data/{run_id}.parquet"

    df_clean = check.inst(df_clean, pd.DataFrame)
    storage.write_parquet(silver_key, df_clean)

    context.log.info(
        f"Processed to silver layer: s3://{storage.bucket}/{silver_key} "
        f"({len(df_clean)} records, {len(df) - len(df_clean)} removed)"
    )

    context.add_output_metadata(
        {
            "silver_path": f"s3://{storage.bucket}/{silver_key}",
            "record_count": len(df_clean),
            "records_removed": len(df) - len(df_clean),
            "layer": "silver",
        }
    )

    return silver_key


@asset(deps=[process_silver_layer], group_name="lakehouse_pipeline")
def aggregate_gold_layer(
    context: AssetExecutionContext,
    process_silver_layer: str,
    storage: S3Resource,
) -> str:
    df = storage.read_parquet(process_silver_layer)

    if df.empty:
        raise ValueError("No data in silver layer to aggregate")

    df["hour"] = df["timestamp"].dt.floor("h")

    df_agg = (
        df.groupby(["region", "hour"])
        .agg(
            {
                "temperature": "mean",
                "humidity": "mean",
                "sensor_id": "count",
            }
        )
        .reset_index()
    )

    df_agg.columns = ["region", "hour", "avg_temperature", "avg_humidity", "sensor_count"]

    run_id = context.run.run_id
    gold_key = f"gold/sensor_summary/{run_id}.parquet"

    storage.write_parquet(gold_key, df_agg)

    context.log.info(
        f"Aggregated to gold layer: s3://{storage.bucket}/{gold_key} ({len(df_agg)} summaries)"
    )

    context.add_output_metadata(
        {
            "gold_path": f"s3://{storage.bucket}/{gold_key}",
            "summary_count": len(df_agg),
            "layer": "gold",
        }
    )

    return gold_key
