from dagster import AssetCheckEvaluation, AssetMaterialization, IntMetadataValue, TextMetadataValue
from dagster_dbt.core.dbt_cli_event import DbtCoreCliEventMessage, DbtFusionCliEventMessage
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator

MANIFEST = {
    "metadata": {"adapter_type": "duckdb", "project_name": "my_project"},
    "nodes": {
        "model.my_project.my_model": {
            "unique_id": "model.my_project.my_model",
            "name": "my_model",
            "resource_type": "model",
            "depends_on": {"nodes": []},
            "config": {"materialized": "table"},
            "meta": {},
            "description": "",
            "package_name": "my_project",
            "path": "models/my_model.sql",
            "original_file_path": "models/my_model.sql",
        },
        "test.my_project.my_test": {
            "unique_id": "test.my_project.my_test",
            "name": "my_test",
            "resource_type": "test",
            "depends_on": {"nodes": ["model.my_project.my_model"]},
            "attached_node": "model.my_project.my_model",
            "config": {},
            "meta": {},
            "description": "",
            "package_name": "my_project",
            "path": "tests/my_test.sql",
            "original_file_path": "tests/my_test.sql",
        },
    },
}


def _build_core_test_event(node_status: str, status: str | None = None) -> dict[str, object]:
    return {
        "info": {"name": "LogTestResult", "msg": "Core test event", "invocation_id": "core-1"},
        "data": {
            "node_info": {"unique_id": "test.my_project.my_test", "node_status": node_status},
            "status": status or node_status,
            "num_failures": 0 if node_status == "pass" else 1,
        },
    }


def _build_fusion_event(unique_id: str, node_status: str, status: str | None = None) -> dict[str, object]:
    return {
        "info": {"name": "NodeFinished", "msg": "Fusion event", "invocation_id": "fusion-1"},
        "data": {
            "node_info": {"unique_id": unique_id, "node_status": node_status},
            "status": status or node_status,
            "num_failures": 0 if node_status in {"pass", "success"} else 1,
        },
    }


def _assert_check_evaluation(
    event: object, *, passed: bool, check_name: str, asset_key_path: list[str], status: str, failed_row_count: int
) -> None:
    assert isinstance(event, AssetCheckEvaluation)
    assert event.passed is passed
    assert event.check_name == check_name
    assert event.asset_key.path == asset_key_path
    assert event.metadata["status"] == TextMetadataValue(text=status)
    assert event.metadata["dagster_dbt/failed_row_count"] == IntMetadataValue(
        value=failed_row_count
    )


def test_dbt_core_cli_event_to_default_asset_events_emits_expected_check_evaluation():
    passing_test_event = _build_core_test_event("pass")
    failing_test_event = _build_core_test_event("fail")

    passing_events = list(
        DbtCoreCliEventMessage(
            raw_event=passing_test_event, event_history_metadata={}
        ).to_default_asset_events(MANIFEST, DagsterDbtTranslator())
    )
    assert len(passing_events) == 1
    _assert_check_evaluation(
        passing_events[0],
        passed=True,
        check_name="my_test",
        asset_key_path=["my_model"],
        status="pass",
        failed_row_count=0,
    )

    failing_events = list(
        DbtCoreCliEventMessage(
            raw_event=failing_test_event, event_history_metadata={}
        ).to_default_asset_events(MANIFEST, DagsterDbtTranslator())
    )
    assert len(failing_events) == 1
    _assert_check_evaluation(
        failing_events[0],
        passed=False,
        check_name="my_test",
        asset_key_path=["my_model"],
        status="fail",
        failed_row_count=1,
    )


def test_dbt_fusion_cli_event_to_default_asset_events_emits_expected_events():
    success_test_event = _build_fusion_event("test.my_project.my_test", "pass")
    failed_test_event = _build_fusion_event("test.my_project.my_test", "fail")
    success_model_event = _build_fusion_event("model.my_project.my_model", "success")

    passing_events = list(
        DbtFusionCliEventMessage(
            raw_event=success_test_event, event_history_metadata={}
        ).to_default_asset_events(MANIFEST, DagsterDbtTranslator())
    )
    assert len(passing_events) == 1
    _assert_check_evaluation(
        passing_events[0],
        passed=True,
        check_name="my_test",
        asset_key_path=["my_model"],
        status="pass",
        failed_row_count=0,
    )

    failing_events = list(
        DbtFusionCliEventMessage(
            raw_event=failed_test_event, event_history_metadata={}
        ).to_default_asset_events(MANIFEST, DagsterDbtTranslator())
    )
    assert len(failing_events) == 1
    _assert_check_evaluation(
        failing_events[0],
        passed=False,
        check_name="my_test",
        asset_key_path=["my_model"],
        status="fail",
        failed_row_count=1,
    )

    successful_model_events = list(
        DbtFusionCliEventMessage(
            raw_event=success_model_event, event_history_metadata={}
        ).to_default_asset_events(MANIFEST, DagsterDbtTranslator())
    )
    assert len(successful_model_events) == 1
    model_event = successful_model_events[0]
    assert isinstance(model_event, AssetMaterialization)
    assert model_event.asset_key.path == ["my_model"]
