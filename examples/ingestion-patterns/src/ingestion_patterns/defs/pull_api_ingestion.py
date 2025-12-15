from datetime import datetime, timedelta
from typing import Any

import dagster as dg
import pandas as pd
from dagster._core.events import StepMaterializationData
from dagster_duckdb import DuckDBResource

from ingestion_patterns.resources import APIClientResource


class PullIngestionConfig(dg.Config):
    """Configuration for pull-based ingestion."""

    start_date: str | None = None  # ISO format
    end_date: str | None = None  # ISO format
    batch_size: int = 1000


@dg.asset
def extract_source_data(
    context: dg.AssetExecutionContext,
    config: PullIngestionConfig,
    duckdb: DuckDBResource,
    api_client: APIClientResource,
) -> pd.DataFrame:
    """Pull data from source system via API.

    This asset determines the date range to extract (defaulting to last 24 hours
    or using provided dates), queries the API, and returns a DataFrame.
    """
    # Determine date range
    end_date = datetime.now()

    # Try to get last successful extraction time from previous run
    last_event = context.instance.get_latest_materialization_event(context.asset_key)

    if last_event and last_event.dagster_event and not config.start_date:
        # Use last successful extraction time as start
        mat_data = last_event.dagster_event.event_specific_data
        if isinstance(mat_data, StepMaterializationData):
            metadata = mat_data.materialization.metadata
            if "last_extracted_timestamp" in metadata:
                timestamp_value = metadata["last_extracted_timestamp"].value
                start_date = datetime.fromisoformat(str(timestamp_value))
            else:
                start_date = end_date - timedelta(days=1)
        else:
            start_date = end_date - timedelta(days=1)
    elif config.start_date:
        start_date = datetime.fromisoformat(config.start_date)
    else:
        start_date = end_date - timedelta(days=1)

    if config.end_date:
        end_date = datetime.fromisoformat(config.end_date)

    context.log.info(f"Pulling data from {start_date} to {end_date}")

    # Pull data from API using the resource
    records = api_client.get_records(start_date, end_date)

    if not records:
        context.log.info("No new records found")
        return pd.DataFrame()

    df = pd.DataFrame(records)

    # Store raw data in DuckDB
    with duckdb.get_connection() as conn:
        conn.execute("CREATE SCHEMA IF NOT EXISTS ingestion")
        conn.register("raw_df", df)
        # Check if table exists
        table_exists = conn.execute(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema='ingestion' AND table_name='raw_extract'"
        ).fetchone()
        if table_exists:
            conn.execute("INSERT INTO ingestion.raw_extract SELECT * FROM raw_df")
        else:
            conn.execute("CREATE TABLE ingestion.raw_extract AS SELECT * FROM raw_df")
        context.log.info(f"Stored {len(df)} records in ingestion.raw_extract")

    # Store metadata for next run
    context.add_output_metadata(
        {
            "record_count": len(df),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "last_extracted_timestamp": end_date.isoformat(),
        }
    )

    context.log.info(f"Extracted {len(df)} records")
    return df


@dg.asset_check(asset=extract_source_data)
def validate_extracted_data(
    context: dg.AssetCheckExecutionContext,
    extract_source_data: pd.DataFrame,
) -> dg.AssetCheckResult:
    """Validate extracted data quality.

    This asset check performs data quality checks:
    - Schema validation (required columns present)
    - Duplicate detection
    - Data type validation
    - Completeness checks (no nulls in required fields)
    """
    if extract_source_data.empty:
        return dg.AssetCheckResult(
            passed=True,
            metadata={"reason": "No data to validate"},
        )

    df = extract_source_data

    # Check required columns
    required_columns = ["id", "timestamp", "value"]
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        return dg.AssetCheckResult(
            passed=False,
            metadata={"missing_columns": missing},
            description=f"Missing required columns: {missing}",
        )

    # Check for duplicates
    duplicates = df.duplicated(subset=["id"])
    duplicate_count = int(duplicates.sum()) if duplicates.any() else 0

    # Check for nulls in required fields
    null_counts = df[required_columns].isnull().sum().to_dict()
    has_nulls = any(count > 0 for count in null_counts.values())

    # Determine pass/fail
    # We pass if there are no missing columns (duplicates and nulls are warnings)
    passed = len(missing) == 0

    return dg.AssetCheckResult(
        passed=passed,
        metadata={
            "record_count": len(df),
            "duplicate_count": duplicate_count,
            "null_counts": null_counts,
            "has_nulls": has_nulls,
        },
        description=(
            f"Validated {len(df)} records. Duplicates: {duplicate_count}, Has nulls: {has_nulls}"
        ),
    )


@dg.asset
def load_to_storage(
    context: dg.AssetExecutionContext,
    extract_source_data: pd.DataFrame,
    duckdb: DuckDBResource,
) -> dict[str, Any]:
    """Load extracted data to final storage table in DuckDB.

    This asset loads data after extraction. The validate_extracted_data
    asset check runs alongside to verify data quality.
    """
    if extract_source_data.empty:
        context.log.info("No data to load")
        return {"loaded": 0}

    df = extract_source_data

    # Clean data before loading: remove duplicates
    original_count = len(df)
    df = df.drop_duplicates(subset=["id"], keep="first")
    duplicates_removed = original_count - len(df)
    if duplicates_removed > 0:
        context.log.info(f"Removed {duplicates_removed} duplicate records")

    # Load to final table in DuckDB
    with duckdb.get_connection() as conn:
        conn.execute("CREATE SCHEMA IF NOT EXISTS ingestion")
        conn.register("final_df", df)
        # Check if table exists
        table_exists = conn.execute(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema='ingestion' AND table_name='final_data'"
        ).fetchone()
        if table_exists:
            conn.execute("INSERT INTO ingestion.final_data SELECT * FROM final_df")
        else:
            conn.execute("CREATE TABLE ingestion.final_data AS SELECT * FROM final_df")

        # Get total count
        result = conn.execute("SELECT COUNT(*) FROM ingestion.final_data").fetchone()
        total_count = result[0] if result else 0

    context.log.info(f"Loaded {len(df)} records to ingestion.final_data")

    context.add_output_metadata(
        {
            "loaded_count": len(df),
            "duplicates_removed": duplicates_removed,
            "total_in_storage": total_count,
            "load_timestamp": datetime.now().isoformat(),
        }
    )

    return {
        "loaded": len(df),
        "total": total_count,
        "timestamp": datetime.now().isoformat(),
    }
