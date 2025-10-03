# start_asset
import pandas as pd
from dagster_pandas.data_frame import create_table_schema_metadata_from_dataframe

import dagster as dg


@dg.asset
def shipments(context: dg.AssetExecutionContext) -> pd.DataFrame:
    """Example shipments asset with column schema metadata."""
    df = pd.DataFrame(
        {
            "shipment_id": [1, 2, 3],
            "customer_name": pd.Series(
                [
                    "Alice",
                    "Bob",
                    "Charlie",
                ],
                dtype="string",
            ),
            "amount": [100.50, 200.75, 150.25],
            "ship_date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
        }
    )

    context.add_output_metadata(
        {"dagster/column_schema": create_table_schema_metadata_from_dataframe(df)}
    )
    return df


# end_asset


# start_asset_check
import pandas as pd
import yaml

import dagster as dg


@dg.asset_check(
    asset=shipments, description="Validate shipments schema against data contract"
)
def validate_shipments_data_contract(
    context: dg.AssetCheckExecutionContext, shipments: pd.DataFrame
) -> dg.AssetCheckResult:
    """Check that the shipments asset matches the data contract schema."""
    # Read the data contract YAML file
    try:
        with open(dg.file_relative_path(__file__, "shipments_contract.yaml")) as file:
            contract = yaml.safe_load(file)
    except FileNotFoundError:
        return dg.AssetCheckResult(
            passed=False, metadata={"error": "Data contract YAML file not found"}
        )

    # Get the current asset's column schema from metadata
    latest_materialization = context.instance.get_latest_materialization_event(
        asset_key=dg.AssetKey(["shipments"])
    )

    if (
        not latest_materialization
        or not latest_materialization.dagster_event.event_specific_data.materialization.metadata
    ):
        return dg.AssetCheckResult(
            passed=False, metadata={"error": "No schema metadata found for asset"}
        )

    # Extract the TableSchema from metadata
    schema_metadata = latest_materialization.dagster_event.event_specific_data.materialization.metadata.get(
        "dagster/column_schema"
    )

    if not schema_metadata:
        return dg.AssetCheckResult(
            passed=False, metadata={"error": "No column schema metadata found"}
        )

    # Convert TableSchema to dict for comparison
    actual_schema = {col.name: col.type for col in schema_metadata.value.columns}

    # Extract expected schema from contract
    expected_schema = {}
    if "schema" in contract and "columns" in contract["schema"]:
        for col_name, col_info in contract["schema"]["columns"].items():
            expected_schema[col_name] = col_info.get("type", "unknown")

    # Compare schemas
    mismatches = []
    missing_columns = []
    extra_columns = []

    # Check for missing columns in actual schema
    for col_name in expected_schema:
        if col_name not in actual_schema:
            missing_columns.append(col_name)

    # Check for extra columns in actual schema
    for col_name in actual_schema:
        if col_name not in expected_schema:
            extra_columns.append(col_name)

    # Check for type mismatches
    for col_name in expected_schema:
        if col_name in actual_schema:
            if actual_schema[col_name] != expected_schema[col_name]:
                mismatches.append(
                    {
                        "column": col_name,
                        "expected": expected_schema[col_name],
                        "actual": actual_schema[col_name],
                    }
                )

    # Determine if check passed
    passed = (
        len(mismatches) == 0 and len(missing_columns) == 0 and len(extra_columns) == 0
    )

    # Prepare metadata for the result
    result_metadata = {
        "expected_schema": expected_schema,
        "actual_schema": actual_schema,
        "mismatches": mismatches,
        "missing_columns": missing_columns,
        "extra_columns": extra_columns,
    }

    return dg.AssetCheckResult(
        passed=passed,
        metadata=result_metadata,
        severity=dg.AssetCheckSeverity.ERROR
        if not passed
        else dg.AssetCheckSeverity.WARN,
    )


# end_asset_check
