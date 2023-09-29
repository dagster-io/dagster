import json
import os
from pathlib import Path
from typing import List

import pytest
from dagster import AssetCheckResult, AssetExecutionContext, AssetKey, materialize
from dagster._core.definitions.asset_check_spec import AssetCheckSeverity
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.asset_defs import load_assets_from_dbt_manifest
from dagster_dbt.core.resources_v2 import DbtCliResource

pytest.importorskip("dbt.version", minversion="1.4")


test_asset_checks_dbt_project_dir = (
    Path(__file__).joinpath("..", "dbt_projects", "test_dagster_asset_checks").resolve()
)
no_asset_checks_manifest_path = test_asset_checks_dbt_project_dir.joinpath(
    "manifest_no_asset_checks.json"
).resolve()
asset_checks_manifest_path = test_asset_checks_dbt_project_dir.joinpath(
    "manifest_with_asset_checks.json"
).resolve()
manifest_no_asset_checks_json = json.loads(no_asset_checks_manifest_path.read_bytes())
manifest_asset_checks_json = json.loads(asset_checks_manifest_path.read_bytes())


def test_with_asset_checks() -> None:
    @dbt_assets(manifest=manifest_no_asset_checks_json)
    def my_dbt_assets_no_checks(): ...

    [load_my_dbt_assets_no_checks] = load_assets_from_dbt_manifest(
        manifest=manifest_no_asset_checks_json
    )

    # dbt tests are present, but are not modeled as Dagster asset checks
    for asset_def in [my_dbt_assets_no_checks, load_my_dbt_assets_no_checks]:
        assert any(
            unique_id.startswith("test")
            for unique_id in manifest_no_asset_checks_json["nodes"].keys()
        )
        assert not asset_def.check_specs_by_output_name

    @dbt_assets(manifest=manifest_asset_checks_json)
    def my_dbt_assets_with_checks(): ...

    [load_my_dbt_assets_with_checks] = load_assets_from_dbt_manifest(
        manifest=manifest_asset_checks_json
    )

    # dbt tests are present, and are modeled as Dagster asset checks
    for asset_def in [my_dbt_assets_with_checks, load_my_dbt_assets_with_checks]:
        assert any(
            unique_id.startswith("test") for unique_id in manifest_asset_checks_json["nodes"].keys()
        )
        assert asset_def.check_specs_by_output_name

        # dbt singular tests are not modeled as Dagster asset checks
        for check_spec in asset_def.check_specs_by_output_name.values():
            assert "assert_singular_test_is_not_asset_check" != check_spec.name


@pytest.mark.parametrize(
    "dbt_commands",
    [
        [
            ["build"],
        ],
        [
            ["seed"],
            ["run"],
            ["test"],
        ],
    ],
)
def test_asset_check_execution(dbt_commands: List[List[str]]) -> None:
    dbt = DbtCliResource(project_dir=os.fspath(test_asset_checks_dbt_project_dir))

    @dbt_assets(manifest=manifest_asset_checks_json)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        for dbt_command in dbt_commands:
            yield from dbt.cli(dbt_command, context=context).stream()

    result = materialize(
        [my_dbt_assets],
        resources={
            "dbt": dbt,
        },
    )

    assert result.success

    events = []
    invocation_id = ""
    for dbt_command in dbt_commands:
        dbt_cli_invocation = dbt.cli(dbt_command, manifest=manifest_asset_checks_json)

        events += list(dbt_cli_invocation.stream())
        invocation_id = dbt_cli_invocation.get_artifact("run_results.json")["metadata"][
            "invocation_id"
        ]

    assert (
        AssetCheckResult(
            passed=True,
            asset_key=AssetKey(["customers"]),
            check_name="unique_customers_customer_id",
            metadata={
                "unique_id": (
                    "test.test_dagster_asset_checks.unique_customers_customer_id.c5af1ff4b1"
                ),
                "invocation_id": invocation_id,
                "status": "pass",
            },
            severity=AssetCheckSeverity.WARN,
        )
        in events
    )
    assert (
        AssetCheckResult(
            passed=True,
            asset_key=AssetKey(["customers"]),
            check_name="not_null_customers_customer_id",
            metadata={
                "unique_id": (
                    "test.test_dagster_asset_checks.not_null_customers_customer_id.5c9bf9911d"
                ),
                "invocation_id": invocation_id,
                "status": "pass",
            },
            severity=AssetCheckSeverity.ERROR,
        )
        in events
    )
