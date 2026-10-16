import pytest
from dagster import AssetCheckEvaluation, AssetCheckSeverity
from dagster_dbt.compat import DBT_PYTHON_VERSION, NodeStatus, TestStatus
from dagster_dbt.core.dbt_cli_event import DbtFusionCliEventMessage
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator

# `compat` defines these itself when dbt-core is not installed, so the values have to hold
# either way — a divergence makes every status comparison in the library silently wrong.
NODE_STATUS_VALUES = {
    "Success": "success",
    "Error": "error",
    "Fail": "fail",
    "Warn": "warn",
    "Skipped": "skipped",
    "PartialSuccess": "partial success",
    "Pass": "pass",
    "RuntimeErr": "runtime error",
}
TEST_STATUS_VALUES = {
    "Pass": "pass",
    "Error": "error",
    "Fail": "fail",
    "Warn": "warn",
    "Skipped": "skipped",
}

MANIFEST = {
    "metadata": {"invocation_id": "1ed5a1f0-2ec0-4b4f-9e0f-0a31e2a1a0d1"},
    "nodes": {
        "model.jaffle_shop.customers": {
            "unique_id": "model.jaffle_shop.customers",
            "name": "customers",
            "resource_type": "model",
            "config": {"materialized": "table"},
            "database": "db",
            "schema": "public",
            "alias": "customers",
            "path": "customers.sql",
            "description": "",
        },
        "test.jaffle_shop.unique_customers_customer_id": {
            "unique_id": "test.jaffle_shop.unique_customers_customer_id",
            "name": "unique_customers_customer_id",
            "resource_type": "test",
            "attached_node": "model.jaffle_shop.customers",
            "depends_on": {"nodes": ["model.jaffle_shop.customers"]},
            "config": {},
            "description": "",
        },
    },
}


def _fusion_test_event(status: str) -> DbtFusionCliEventMessage:
    return DbtFusionCliEventMessage(
        raw_event={
            "data": {
                "node_info": {
                    "unique_id": "test.jaffle_shop.unique_customers_customer_id",
                    "node_status": status,
                    "resource_type": "test",
                    "node_started_at": "",
                    "node_finished_at": "",
                },
                "status": status,
            },
            "info": {
                "name": "NodeFinished",
                "invocation_id": "1ed5a1f0-2ec0-4b4f-9e0f-0a31e2a1a0d1",
                "msg": "",
            },
        },
        event_history_metadata={},
    )


def test_status_enums_match_dbt_core() -> None:
    """The statuses `compat` falls back to must match the ones dbt-core defines.

    `DbtFusionCliEventMessage._get_check_passed` compares a raw status string against these,
    so a wrong value reports every passing dbt test as a failed asset check.
    """
    expected_by_enum = ((NodeStatus, NODE_STATUS_VALUES), (TestStatus, TEST_STATUS_VALUES))

    # dbt-core gains statuses over time — 1.7 has no `PartialSuccess` — so only check the ones
    # the installed version defines.
    for enum_cls, expected in expected_by_enum:
        for name, value in expected.items():
            if name in enum_cls.__members__:
                assert enum_cls[name].value == value

    if DBT_PYTHON_VERSION is not None:
        return

    # With no dbt-core these come from `compat` itself, so it must define all of them and
    # stringify them to their values the way dbt's own StrEnum does.
    for enum_cls, expected in expected_by_enum:
        assert set(expected) <= set(enum_cls.__members__)
        for name, value in expected.items():
            assert str(enum_cls[name]) == value


@pytest.mark.parametrize(
    "status,passed,severity",
    [
        ("pass", True, AssetCheckSeverity.ERROR),
        ("success", True, AssetCheckSeverity.ERROR),
        ("fail", False, AssetCheckSeverity.ERROR),
        ("error", False, AssetCheckSeverity.ERROR),
        ("warn", False, AssetCheckSeverity.WARN),
    ],
)
def test_fusion_test_result_to_check_evaluation(
    status: str, passed: bool, severity: AssetCheckSeverity
) -> None:
    """A dbt Fusion test result maps to an asset check evaluation with the right verdict."""
    [evaluation] = list(
        _fusion_test_event(status).to_default_asset_events(MANIFEST, DagsterDbtTranslator())
    )

    assert isinstance(evaluation, AssetCheckEvaluation)
    assert evaluation.passed is passed
    assert evaluation.severity is severity
