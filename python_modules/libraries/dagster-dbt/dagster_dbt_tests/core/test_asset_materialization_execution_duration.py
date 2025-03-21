from datetime import datetime

from dagster import FloatMetadataValue
from dagster_dbt.core.dbt_cli_event import DbtCliEventMessage
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator


def test_microbatch_log_model_result_to_asset():
    """Microbatch models do not produce reliable data.node_info.node_started_at, data.node_info.node_finished_at and
    data.node_info.node_status, so we need to fall back to data.execution_time and data.status.

    Below is an example of LogModelResult produced by an actual dbt==1.9.1 executed against Snowflake.
    """
    microbatch_log_model_result = {
        "data": {
            "description": "sql microbatch model public.orders",
            "execution_time": 10.905523,
            "index": 1,
            "node_info": {
                "materialized": "incremental",
                "node_finished_at": "",
                "node_name": "public__orders",
                "node_path": "mart/public__orders.sql",
                "node_relation": {
                    "alias": "order_history",
                    "database": "dev",
                    "relation_name": "dev.public.order_history",
                    "schema": "public",
                },
                "node_started_at": "",
                "node_status": "None",
                "resource_type": "model",
                "unique_id": "model.pytest_dwh.public__orders",
            },
            "status": "SUCCESS",
            "total": 1,
        },
        "info": {
            "category": "",
            "code": "Q012",
            "extra": {},
            "invocation_id": "c630c6bf-633e-4612-8e46-2f170224066c",
            "level": "info",
            "msg": "1 of 1 OK created sql microbatch model public.orders  [\u001b[32mSUCCESS\u001b[0m in 10.91s]",
            "name": "LogModelResult",
            "pid": 14277,
            "thread": "MainThread",
            "ts": "2025-03-10T12:54:41.369662Z",
        },
    }

    microbatch_event_history_metadata = {
        "metadata": {
            "invocation_id": "c630c6bf-633e-4612-8e46-2f170224066c",
            "generated_at": "2025-03-10T12:54:41.369662Z",
            "env": {},
        },
        "logs": [],
    }

    event_message = DbtCliEventMessage(
        raw_event=microbatch_log_model_result,
        event_history_metadata=microbatch_event_history_metadata,
    )

    dagster_dbt_translator = DagsterDbtTranslator()

    manifest = {
        "metadata": {
            "invocation_id": "c630c6bf-633e-4612-8e46-2f170224066c",
            "generated_at": "2025-03-10T12:54:41.369662Z",
        },
        "nodes": {
            "model.pytest_dwh.public__orders": {
                "unique_id": "model.pytest_dwh.public__orders",
                "name": "public__orders",
                "resource_type": "model",
                "materialized": "incremental",
                "database": "dev",
                "schema": "public",
                "alias": "order_history",
                "path": "mart/public__orders.sql",
                "config": {"schema": "public"},
            }
        },
    }

    asset_materialization_event = next(
        event_message.to_default_asset_events(manifest, dagster_dbt_translator)
    )

    assert asset_materialization_event.metadata.get("Execution Duration") == FloatMetadataValue(
        value=10.905523
    )


def test_incremental_log_model_result_to_asset():
    """Incremental models produce logs with reliable data.node_info.node_started_at, data.node_info.node_finished_at and
    data.node_info.node_status, so there's no need for a patch -- we expect Execution Duration to be calculated as
    (node_finished_at - node_started_at) instead of sourcing it from data.execution_time.

    Below is an example of LogModelResult produced by an actual dbt==1.9.1 executed against Snowflake.
    """
    incremental_log_model_result = {
        "data": {
            "description": "sql incremental model public.orders",
            "execution_time": 11.995666,
            "index": 1,
            "node_info": {
                "materialized": "incremental",
                "node_finished_at": "2025-03-10T12:53:48.818126",
                "node_name": "public__orders",
                "node_path": "mart/public__orders.sql",
                "node_relation": {
                    "alias": "order_history",
                    "database": "dev",
                    "relation_name": "dev.public.order_history",
                    "schema": "public",
                },
                "node_started_at": "2025-03-10T12:53:36.820592",
                "node_status": "success",
                "resource_type": "model",
                "unique_id": "model.pytest_dwh.public__orders",
            },
            "status": "SUCCESS 0",
            "total": 1,
        },
        "info": {
            "category": "",
            "code": "Q012",
            "extra": {},
            "invocation_id": "3f0b2ff3-e708-4a86-a81d-eb348f7d2faa",
            "level": "info",
            "msg": "1 of 1 OK created sql incremental model public.orders .......... [\u001b[32mSUCCESS 0\u001b[0m in 12.00s]",
            "name": "LogModelResult",
            "pid": 14251,
            "thread": "Thread-1 (worker)",
            "ts": "2025-03-10T12:53:48.825332Z",
        },
    }

    incremental_event_history_metadata = {
        "metadata": {
            "invocation_id": "c630c6bf-633e-4612-8e46-2f170224066c",
            "generated_at": "2025-03-10T12:54:41.369662Z",
            "env": {},
        },
        "logs": [],
    }

    event_message = DbtCliEventMessage(
        raw_event=incremental_log_model_result,
        event_history_metadata=incremental_event_history_metadata,
    )

    dagster_dbt_translator = DagsterDbtTranslator()

    manifest = {
        "metadata": {
            "invocation_id": "c630c6bf-633e-4612-8e46-2f170224066c",
            "generated_at": "2025-03-10T12:54:41.369662Z",
        },
        "nodes": {
            "model.pytest_dwh.public__orders": {
                "unique_id": "model.pytest_dwh.public__orders",
                "name": "public__orders",
                "resource_type": "model",
                "materialized": "incremental",
                "database": "dev",
                "schema": "public",
                "alias": "order_history",
                "path": "mart/public__orders.sql",
                "config": {"schema": "public"},
            }
        },
    }

    asset_materialization_event = next(
        event_message.to_default_asset_events(manifest, dagster_dbt_translator)
    )

    node_started_at = incremental_log_model_result["data"]["node_info"]["node_started_at"]
    node_finished_at = incremental_log_model_result["data"]["node_info"]["node_finished_at"]
    timestamp_format = "%Y-%m-%dT%H:%M:%S.%f"
    started_at = datetime.strptime(node_started_at, timestamp_format)
    finished_at = datetime.strptime(node_finished_at, timestamp_format)
    execution_duration_seconds = (finished_at - started_at).total_seconds()

    # this test only makes sense if data.execution_time differs from (node_finished_at - node_started_at)
    assert incremental_log_model_result["data"]["execution_time"] != execution_duration_seconds

    # we expect AssetMaterialization to source Execution Duration from (node_finished_at - node_started_at) instead of
    # data.execution_time
    assert asset_materialization_event.metadata.get("Execution Duration") == FloatMetadataValue(
        value=execution_duration_seconds
    )
