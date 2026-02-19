import json
import logging
from typing import Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)


# start_simple_existing_lambda
def simple_existing_lambda(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Existing Lambda that expects a simple config dictionary."""
    logger.info("Simple existing Lambda handler")

    source_bucket = event.get("source_bucket")
    destination_bucket = event.get("destination_bucket")
    file_pattern = event.get("file_pattern")

    logger.info(f"Source: {source_bucket}")
    logger.info(f"Destination: {destination_bucket}")
    logger.info(f"Pattern: {file_pattern}")

    result = process_files(source_bucket, destination_bucket, file_pattern)

    return {"statusCode": 200, "body": json.dumps(result)}


# end_simple_existing_lambda


# start_ops_aware_lambda
def ops_aware_lambda(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Existing Lambda that understands Dagster ops config structure."""
    logger.info("Ops-aware Lambda handler")

    ops_config = event
    logger.info(f"Received ops config: {json.dumps(ops_config, indent=2)}")

    results = {}
    for op_name, op_data in ops_config.items():
        logger.info(f"Processing op: {op_name}")
        config = op_data.get("config", {})
        result = process_op_config(op_name, config)
        results[op_name] = result

    return {"statusCode": 200, "body": json.dumps(results)}


# end_ops_aware_lambda


# start_run_config_lambda
def run_config_lambda(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Existing Lambda that works with Dagster's full run_config."""
    logger.info("Run config Lambda handler")

    ops_config = event.get("ops", {})
    resources_config = event.get("resources", {})

    logger.info(f"Processing {len(ops_config)} ops")

    results = {}
    for op_name, op_data in ops_config.items():
        config = op_data.get("config", {})
        result = process_with_resources(op_name, config, resources_config)
        results[op_name] = result

    return {"statusCode": 200, "body": json.dumps({"status": "completed", "results": results})}


# end_run_config_lambda


# start_real_world_etl_lambda
def real_world_etl_lambda(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Existing ETL Lambda - receives flat config, no changes needed."""
    logger.info("ETL Lambda handler (existing, unchanged)")

    input_table = event.get("input_table")
    output_table = event.get("output_table")
    date_range = event.get("date_range", {})
    filters = event.get("filters", [])

    logger.info(f"ETL: {input_table} -> {output_table}")
    logger.info(f"Date range: {date_range}")
    logger.info(f"Filters: {filters}")

    records_processed = run_etl_pipeline(input_table, output_table, date_range, filters)

    return {
        "statusCode": 200,
        "body": json.dumps({"status": "success", "records_processed": records_processed}),
    }


# end_real_world_etl_lambda


def process_files(source: str, destination: str, pattern: str) -> dict[str, Any]:
    """Your existing file processing logic."""
    logger.info(f"Processing files: {source} -> {destination} ({pattern})")
    files_processed = 42
    return {"files_processed": files_processed, "source": source, "destination": destination}


def process_op_config(op_name: str, config: dict[str, Any]) -> dict[str, Any]:
    """Process a single op's configuration."""
    logger.info(f"Processing op '{op_name}' with config: {config}")
    return {"op": op_name, "status": "processed", "config_keys": list(config.keys())}


def process_with_resources(
    op_name: str, config: dict[str, Any], resources: dict[str, Any]
) -> dict[str, Any]:
    """Process with resource configuration."""
    logger.info(f"Processing op '{op_name}' with resources")
    return {
        "op": op_name,
        "status": "processed_with_resources",
        "resources_used": list(resources.keys()),
    }


def run_etl_pipeline(input_table, output_table, date_range, filters):
    """Your existing ETL pipeline logic."""
    return 1000
