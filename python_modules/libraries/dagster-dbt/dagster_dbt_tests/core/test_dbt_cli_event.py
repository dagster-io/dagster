import pytest
from dagster import AssetMaterialization
from dagster_dbt.core.dbt_cli_event import DbtCoreCliEventMessage
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator

MANIFEST = {
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
            "description": "",
        }
    },
}


def build_log_model_result(node_status: str) -> DbtCoreCliEventMessage:
    return DbtCoreCliEventMessage(
        raw_event={
            "data": {
                "description": "sql incremental model public.orders",
                "execution_time": 0.1,
                "index": 1,
                "node_info": {
                    "materialized": "incremental",
                    "node_finished_at": "2025-03-10T12:53:48.818126",
                    "node_name": "public__orders",
                    "node_path": "mart/public__orders.sql",
                    "node_started_at": "2025-03-10T12:53:36.820592",
                    "node_status": node_status,
                    "resource_type": "model",
                    "unique_id": "model.pytest_dwh.public__orders",
                },
                "status": node_status.upper(),
                "total": 1,
            },
            "info": {
                "invocation_id": "c630c6bf-633e-4612-8e46-2f170224066c",
                "level": "info",
                "msg": "1 of 1 OK",
                "name": "LogModelResult",
            },
        },
        event_history_metadata={},
    )


@pytest.mark.parametrize("node_status", ["success", "no-op", "reused"])
def test_non_error_node_statuses_materialize(node_status: str) -> None:
    """`no-op` (dbt 1.10+) and `reused` (dbt 1.12+) are terminal, non-error statuses meaning dbt
    did not rebuild the node. They must materialize the asset rather than be treated as failures,
    otherwise the missing materialization cascades to downstream assets.
    """
    events = list(
        build_log_model_result(node_status).to_default_asset_events(
            MANIFEST, DagsterDbtTranslator()
        )
    )

    assert len(events) == 1
    materialization = events[0]
    assert isinstance(materialization, AssetMaterialization)
    assert materialization.asset_key.path == ["public", "public__orders"]
    # The status is surfaced as metadata so that it is visible that nothing was built.
    assert materialization.metadata["status"].value == node_status


@pytest.mark.parametrize("node_status", ["error", "fail", "skipped", "runtime error"])
def test_error_node_statuses_do_not_materialize(node_status: str) -> None:
    events = list(
        build_log_model_result(node_status).to_default_asset_events(
            MANIFEST, DagsterDbtTranslator()
        )
    )

    assert events == []
