import json
import os
from pathlib import Path
from typing import List, Optional

import pytest
from dagster import (
    AssetCheckResult,
    AssetExecutionContext,
    AssetKey,
    AssetSelection,
    ExecuteInProcessResult,
    materialize,
)
from dagster._core.definitions.asset_check_spec import AssetCheckSeverity
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.asset_defs import load_assets_from_dbt_manifest
from dagster_dbt.core.resources_v2 import DbtCliResource
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator, DagsterDbtTranslatorSettings
from dbt.version import __version__ as dbt_version
from packaging import version
from pytest_mock import MockerFixture

pytest.importorskip("dbt.version", minversion="1.4")

is_dbt_1_4 = version.parse("1.4.0") <= version.parse(dbt_version) < version.parse("1.5.0")


test_asset_checks_dbt_project_dir = (
    Path(__file__).joinpath("..", "dbt_projects", "test_dagster_asset_checks").resolve()
)
manifest_path = test_asset_checks_dbt_project_dir.joinpath("manifest.json").resolve()
manifest = json.loads(manifest_path.read_bytes())

dagster_dbt_translator_with_checks = DagsterDbtTranslator(
    settings=DagsterDbtTranslatorSettings(enable_asset_checks=True)
)


@pytest.fixture(params=[[["build"]], [["seed"], ["run"], ["test"]]], ids=["build", "seed-run-test"])
def dbt_commands(request):
    return request.param


def test_with_asset_checks() -> None:
    @dbt_assets(manifest=manifest)
    def my_dbt_assets_no_checks():
        ...

    [load_my_dbt_assets_no_checks] = load_assets_from_dbt_manifest(manifest=manifest)

    # dbt tests are present, but are not modeled as Dagster asset checks
    for asset_def in [my_dbt_assets_no_checks, load_my_dbt_assets_no_checks]:
        assert any(unique_id.startswith("test") for unique_id in manifest["nodes"].keys())
        assert not asset_def.check_specs_by_output_name

    @dbt_assets(
        manifest=manifest,
        dagster_dbt_translator=dagster_dbt_translator_with_checks,
    )
    def my_dbt_assets_with_checks():
        ...

    [load_my_dbt_assets_with_checks] = load_assets_from_dbt_manifest(
        manifest=manifest_path,
        dagster_dbt_translator=dagster_dbt_translator_with_checks,
    )

    # dbt tests are present, and are modeled as Dagster asset checks
    for asset_def in [
        my_dbt_assets_with_checks,
        load_my_dbt_assets_with_checks,
    ]:
        assert any(unique_id.startswith("test") for unique_id in manifest["nodes"].keys())
        assert asset_def.check_specs_by_output_name

        # dbt singular tests are not modeled as Dagster asset checks
        for check_spec in asset_def.check_specs_by_output_name.values():
            assert "assert_singular_test_is_not_asset_check" != check_spec.name


def test_enable_asset_checks_with_custom_translator() -> None:
    class CustomDagsterDbtTranslatorWithInitNoSuper(DagsterDbtTranslator):
        def __init__(self, test_arg: str):
            self.test_arg = test_arg

    class CustomDagsterDbtTranslatorWithInitWithSuper(DagsterDbtTranslator):
        def __init__(self, test_arg: str):
            self.test_arg = test_arg

            super().__init__()

    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        ...

    class CustomDagsterDbtTranslatorWithPassThrough(DagsterDbtTranslator):
        def __init__(self, test_arg: str, *args, **kwargs):
            self.test_arg = test_arg

            super().__init__(*args, **kwargs)

    no_pass_through_no_super_translator = CustomDagsterDbtTranslatorWithInitNoSuper("test")
    assert not no_pass_through_no_super_translator.settings.enable_asset_checks

    no_pass_through_with_super_translator = CustomDagsterDbtTranslatorWithInitWithSuper("test")
    assert not no_pass_through_with_super_translator.settings.enable_asset_checks

    custom_translator = CustomDagsterDbtTranslator(
        settings=DagsterDbtTranslatorSettings(enable_asset_checks=True)
    )
    assert custom_translator.settings.enable_asset_checks

    pass_through_translator = CustomDagsterDbtTranslatorWithPassThrough(
        "test",
        settings=DagsterDbtTranslatorSettings(enable_asset_checks=True),
    )
    assert pass_through_translator.settings.enable_asset_checks


def _materialize_dbt_assets(
    dbt_commands: List[List[str]], selection: Optional[AssetSelection]
) -> ExecuteInProcessResult:
    dbt = DbtCliResource(project_dir=os.fspath(test_asset_checks_dbt_project_dir))

    @dbt_assets(manifest=manifest, dagster_dbt_translator=dagster_dbt_translator_with_checks)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        for dbt_command in dbt_commands:
            yield from dbt.cli(dbt_command, context=context).stream()

    result = materialize(
        [my_dbt_assets],
        resources={
            "dbt": dbt,
        },
        selection=selection,
    )

    assert result.success
    return result


def test_materialize_no_selection(dbt_commands: List[List[str]]) -> None:
    result = _materialize_dbt_assets(dbt_commands, selection=None)
    assert len(result.get_asset_materialization_events()) == 8
    assert len(result.get_asset_check_evaluations()) == 20


@pytest.mark.xfail(
    is_dbt_1_4,
    reason="DBT_INDIRECT_SELECTION=empty is not supported in dbt 1.4",
)
def test_materialize_asset_and_checks(dbt_commands: List[List[str]]) -> None:
    result = _materialize_dbt_assets(dbt_commands, AssetSelection.keys(AssetKey(["customers"])))
    assert len(result.get_asset_materialization_events()) == 1
    assert len(result.get_asset_check_evaluations()) == 2


@pytest.mark.xfail(
    is_dbt_1_4,
    reason="DBT_INDIRECT_SELECTION=empty is not supported in dbt 1.4",
)
def test_materialize_asset_no_checks(dbt_commands: List[List[str]]) -> None:
    result = _materialize_dbt_assets(
        dbt_commands, AssetSelection.keys(AssetKey(["customers"])).without_checks()
    )
    assert len(result.get_asset_materialization_events()) == 1
    assert len(result.get_asset_check_evaluations()) == 0


def test_materialize_checks_no_asset(dbt_commands: List[List[str]]) -> None:
    result = _materialize_dbt_assets(
        dbt_commands,
        AssetSelection.keys(AssetKey(["customers"]))
        - AssetSelection.keys(AssetKey(["customers"])).without_checks(),
    )
    assert len(result.get_asset_materialization_events()) == 0
    assert len(result.get_asset_check_evaluations()) == 2


def test_asset_checks_are_logged_from_resource(
    mocker: MockerFixture, dbt_commands: List[List[str]]
):
    mock_context = mocker.MagicMock()
    mock_context.assets_def = None
    mock_context.has_assets_def = True

    dbt = DbtCliResource(project_dir=os.fspath(test_asset_checks_dbt_project_dir))

    events = []
    invocation_id = ""
    for dbt_command in dbt_commands:
        dbt_cli_invocation = dbt.cli(
            dbt_command,
            manifest=manifest,
            dagster_dbt_translator=dagster_dbt_translator_with_checks,
            context=mock_context,
            target_path=Path("target"),
        )

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
