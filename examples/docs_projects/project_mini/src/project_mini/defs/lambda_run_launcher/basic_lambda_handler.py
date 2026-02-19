import json
import logging
from typing import Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Handle Dagster run invocation."""
    try:
        dagster_run = event.get("dagster_run", {})
        run_id = dagster_run.get("run_id", "unknown")
        job_name = dagster_run.get("job_name", "unknown")

        logger.info(f"Processing run {run_id} for job {job_name}")

        run_config = event.get("run_config", {})
        env_vars = event.get("environment_variables", {})

        # Your business logic here
        result = process_dagster_job(run_config, env_vars)

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "run_id": run_id,
                    "job_name": job_name,
                    "status": "success",
                    "result": result,
                }
            ),
        }

    except Exception as e:
        logger.error(f"Error processing Dagster run: {e!s}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "run_id": event.get("dagster_run", {}).get("run_id", "unknown"),
                    "status": "error",
                    "error": str(e),
                }
            ),
        }


def process_dagster_job(config: dict[str, Any], env_vars: dict[str, str]) -> dict[str, Any]:
    """Process the Dagster job configuration."""
    ops_config = config.get("ops", {})

    results = {}
    for op_name in ops_config:
        logger.info(f"Processing op: {op_name}")

        # Your business logic here
        results[op_name] = {"status": "completed"}

    return {"ops_processed": len(ops_config), "results": results}
