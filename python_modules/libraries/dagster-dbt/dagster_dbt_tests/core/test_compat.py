import importlib.metadata
from unittest import mock

import pytest
from dagster import AssetCheckEvaluation, AssetCheckSeverity
from dagster_dbt.compat import (
    DBT_PYTHON_VERSION,
    NodeStatus,
    TestStatus,
    _check_dbt_v2_and_dbt_core_not_both_installed,
)
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
    # Unit tests live here, not under `nodes`, in both dbt Core and dbt Fusion manifests.
    "unit_tests": {
        "unit_test.jaffle_shop.customers.test_customers": {
            "unique_id": "unit_test.jaffle_shop.customers.test_customers",
            "name": "test_customers",
            "resource_type": "unit_test",
            "depends_on": {"nodes": ["model.jaffle_shop.customers"]},
        },
    },
}


def _fusion_test_event(
    status: str,
    unique_id: str = "test.jaffle_shop.unique_customers_customer_id",
    resource_type: str = "test",
) -> DbtFusionCliEventMessage:
    return DbtFusionCliEventMessage(
        raw_event={
            "data": {
                "node_info": {
                    "unique_id": unique_id,
                    "node_status": status,
                    "resource_type": resource_type,
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


def test_dbt_v2_and_dbt_core_conflict() -> None:
    def installed(versions: dict[str, str]):
        def _version(name: str) -> str:
            if name not in versions:
                raise importlib.metadata.PackageNotFoundError(name)
            return versions[name]

        return mock.patch("dagster_dbt.compat.importlib.metadata.version", side_effect=_version)

    with installed({"dbt": "2.0.9", "dbt-core": "1.12.6"}):
        with pytest.raises(ImportError, match="uninstall `dbt-core`"):
            _check_dbt_v2_and_dbt_core_not_both_installed()

    # Either one alone, or the legacy `dbt` 1.x meta-package alongside dbt-core, is fine.
    for versions in (
        {"dbt": "2.0.9"},
        {"dbt-core": "1.12.6"},
        {"dbt": "1.0.0.40", "dbt-core": "1.12.6"},
        {},
    ):
        with installed(versions):
            _check_dbt_v2_and_dbt_core_not_both_installed()


@pytest.mark.parametrize("status", ["pass", "success", "fail", "error"])
def test_fusion_unit_test_result_is_not_a_result_event(status: str) -> None:
    """A dbt Fusion unit test result yields no asset events, as on dbt Core.

    Its unique id is under `unit_tests` rather than `nodes`, so treating it as a result
    event raised a `KeyError` and failed any `dbt build` that ran a unit test.
    """
    event = _fusion_test_event(
        status,
        unique_id="unit_test.jaffle_shop.customers.test_customers",
        resource_type="unit_test",
    )

    assert not event.is_result_event
    assert list(event.to_default_asset_events(MANIFEST, DagsterDbtTranslator())) == []


@pytest.mark.parametrize("status,num_failures", [("pass", 0), ("fail", 1), ("warn", 4)])
def test_fusion_test_result_failed_row_count(status: str, num_failures: int) -> None:
    """A dbt v2 test result sets the failing row count from `data.run_result`.

    The `NodeFinished` event for a dbt v2 test has only `node_info` and `run_result` under
    `data`, so reading `data.num_failures` dropped `dagster_dbt/failed_row_count`.
    """
    event = DbtFusionCliEventMessage(
        raw_event={
            "data": {
                "node_info": {
                    "unique_id": "test.jaffle_shop.unique_customers_customer_id",
                    "node_status": status,
                    "resource_type": "test",
                    "node_started_at": "2026-11-24T17:14:05.849806Z",
                    "node_finished_at": "2026-11-24T17:14:05.858671Z",
                },
                "run_result": {
                    "execution_time": 0.0088,
                    "num_failures": num_failures,
                    "status": status,
                },
            },
            "info": {
                "name": "NodeFinished",
                "invocation_id": "1ed5a1f0-2ec0-4b4f-9e0f-0a31e2a1a0d1",
                "msg": "",
            },
        },
        event_history_metadata={},
    )

    [evaluation] = list(event.to_default_asset_events(MANIFEST, DagsterDbtTranslator()))

    assert isinstance(evaluation, AssetCheckEvaluation)
    assert evaluation.metadata["dagster_dbt/failed_row_count"].value == num_failures
