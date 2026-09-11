import pytest
from dagster import AssetCheckEvaluation, AssetCheckSeverity, AssetMaterialization
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


@pytest.mark.parametrize("node_status", ["success", "no-op", "reused", "warn"])
def test_non_error_node_statuses_materialize(node_status: str) -> None:
    """Statuses a refable node can end on without having failed must materialize the asset,
    rather than be silently dropped.

    `no-op` (dbt-core 1.10+) and `reused` (dbt-core 1.12+, and dbt Fusion's `Reused*` variants)
    mean dbt deliberately did not rebuild the node. `warn` is what dbt Fusion serializes
    `SucceededWithWarning` to -- the node did build, it just emitted a warning.
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


WARNED_TEST_MANIFEST = {
    "metadata": MANIFEST["metadata"],
    "nodes": {
        **MANIFEST["nodes"],
        "test.pytest_dwh.unique_orders": {
            "unique_id": "test.pytest_dwh.unique_orders",
            "name": "unique_orders",
            "resource_type": "test",
            "materialized": "test",
            "database": "dev",
            "schema": "public",
            "alias": "unique_orders",
            "path": "unique_orders.sql",
            "config": {"schema": "public"},
            "description": "",
            "depends_on": {"nodes": ["model.pytest_dwh.public__orders"]},
            "attached_node": "model.pytest_dwh.public__orders",
        },
    },
}


def test_warn_on_a_test_is_still_a_warn_severity_check() -> None:
    """`warn` means opposite things either side of the resource-type gate: a success for a
    refable node, but a warn-severity check failure for a test. dbt serializes both to the same
    string, so accepting `warn` for models must not leak into the test path.
    """
    event = DbtCoreCliEventMessage(
        raw_event={
            "data": {
                "node_info": {
                    "node_status": "warn",
                    "node_name": "unique_orders",
                    "resource_type": "test",
                    "unique_id": "test.pytest_dwh.unique_orders",
                    "node_started_at": "2025-03-10T12:53:36.820592",
                    "node_finished_at": "2025-03-10T12:53:48.818126",
                },
                "status": "WARN",
                "num_failures": 3,
            },
            "info": {
                "invocation_id": "c630c6bf-633e-4612-8e46-2f170224066c",
                "level": "warn",
                "msg": "1 of 1 WARN 3",
                "name": "LogTestResult",
            },
        },
        event_history_metadata={},
    )

    events = list(event.to_default_asset_events(WARNED_TEST_MANIFEST, DagsterDbtTranslator()))

    # No materialization: a test is not a refable node.
    assert [e for e in events if isinstance(e, AssetMaterialization)] == []

    evaluations = [e for e in events if isinstance(e, AssetCheckEvaluation)]
    assert len(evaluations) == 1
    assert evaluations[0].passed is False
    assert evaluations[0].severity == AssetCheckSeverity.WARN
