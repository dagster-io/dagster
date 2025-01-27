import os
import shutil
from dataclasses import replace
from pathlib import Path
from typing import Any, Optional, Union, cast

import pydantic
import pytest
from dagster import In, Nothing, Out, job, materialize, op
from dagster._core.definitions.metadata.metadata_value import FloatMetadataValue, TextMetadataValue
from dagster._core.errors import DagsterExecutionInterruptedError
from dagster._core.execution.context.compute import AssetExecutionContext, OpExecutionContext
from dagster_dbt import dbt_assets
from dagster_dbt.asset_utils import build_dbt_asset_selection
from dagster_dbt.core.dbt_cli_invocation import PARTIAL_PARSE_FILE_NAME
from dagster_dbt.core.resource import DbtCliResource
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator, DagsterDbtTranslatorSettings
from dagster_dbt.dbt_project import DbtProject
from dagster_dbt.errors import DagsterDbtCliRuntimeError
from dbt.version import __version__ as dbt_version
from packaging import version
from pydantic import ValidationError
from pytest_mock import MockerFixture

from dagster_dbt_tests.dbt_projects import (
    test_dbt_source_freshness_path,
    test_exceptions_path,
    test_jaffle_shop_path,
    test_jaffle_with_profile_vars_path,
)


@pytest.fixture(name="dbt", scope="module")
def dbt_fixture() -> DbtCliResource:
    return DbtCliResource(project_dir=os.fspath(test_jaffle_shop_path))


@pytest.fixture(name="dbt_with_profile_vars", scope="module")
def dbt_with_profile_vars_fixture() -> DbtCliResource:
    return DbtCliResource(project_dir=os.fspath(test_jaffle_with_profile_vars_path))


@pytest.mark.parametrize("global_config_flags", [[], ["--quiet"]])
def test_dbt_cli(global_config_flags: list[str]) -> None:
    dbt = DbtCliResource(
        project_dir=os.fspath(test_jaffle_shop_path), global_config_flags=global_config_flags
    )
    dbt_cli_invocation = dbt.cli(["parse"])

    assert dbt_cli_invocation.process.args == ["dbt", *global_config_flags, "parse"]
    assert dbt_cli_invocation.is_successful()
    assert dbt_cli_invocation.process.returncode == 0
    assert dbt_cli_invocation.target_path.joinpath("dbt.log").exists()


def test_dbt_cli_executable() -> None:
    dbt_executable = cast(str, shutil.which("dbt"))
    invocation = DbtCliResource(
        project_dir=os.fspath(test_jaffle_shop_path), dbt_executable=dbt_executable
    ).cli(["parse"])
    assert invocation.is_successful()
    assert not invocation.get_error()

    assert (
        DbtCliResource(
            project_dir=os.fspath(test_jaffle_shop_path),
            dbt_executable=Path(dbt_executable),
        )
        .cli(["parse"])
        .is_successful()
    )

    # dbt executable must exist
    with pytest.raises(ValidationError, match="does not exist"):
        DbtCliResource(project_dir=os.fspath(test_jaffle_shop_path), dbt_executable="nonexistent")


def test_dbt_cli_project_dir_path() -> None:
    dbt = DbtCliResource(project_dir=test_jaffle_shop_path)

    assert Path(dbt.project_dir).is_absolute()
    assert dbt.cli(["parse"]).is_successful()

    # project directory must exist
    with pytest.raises(ValidationError, match="does not exist"):
        DbtCliResource(project_dir="nonexistent")

    # project directory must be a valid dbt project
    with pytest.raises(ValidationError, match="specify a valid path to a dbt project"):
        DbtCliResource(project_dir=f"{os.fspath(test_jaffle_shop_path)}/models")


def test_dbt_cli_failure() -> None:
    dbt = DbtCliResource(project_dir=os.fspath(test_exceptions_path))
    dbt_cli_invocation = dbt.cli(["run", "--selector", "nonexistent"])

    with pytest.raises(
        DagsterDbtCliRuntimeError, match="Could not find selector named nonexistent"
    ):
        dbt_cli_invocation.wait()

    assert not dbt_cli_invocation.is_successful()
    assert dbt_cli_invocation.get_error()
    assert dbt_cli_invocation.process.returncode == 2
    assert dbt_cli_invocation.target_path.joinpath("dbt.log").exists()

    # If the exit code is 0, but error logs were emitted, the invocation is not successful.
    dbt_cli_invocation.process.returncode = 0
    assert not dbt_cli_invocation.is_successful()
    assert dbt_cli_invocation.get_error()

    dbt = DbtCliResource(project_dir=os.fspath(test_exceptions_path), target="error_dev")

    with pytest.raises(Exception, match="Env var required but not provided: 'DBT_DUCKDB_THREADS'"):
        dbt.cli(["parse"]).wait()

    project = DbtProject(project_dir=os.fspath(test_exceptions_path), target="error_dev")
    dbt = DbtCliResource(project_dir=project)
    with pytest.raises(Exception, match="Env var required but not provided: 'DBT_DUCKDB_THREADS'"):
        dbt.cli(["parse"]).wait()


def test_dbt_cli_failure_no_raise() -> None:
    dbt = DbtCliResource(project_dir=os.fspath(test_exceptions_path))
    dbt_cli_invocation = dbt.cli(["run", "--selector", "nonexistent"], raise_on_error=False)
    dbt_cli_invocation.wait()
    assert "Could not find selector named nonexistent" in dbt_cli_invocation.get_error().description  # type: ignore


def test_dbt_cli_subprocess_cleanup(
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
    dbt: DbtCliResource,
) -> None:
    dbt_cli_invocation_1 = dbt.cli(["run"])

    assert dbt_cli_invocation_1.process.returncode is None

    with pytest.raises(DagsterExecutionInterruptedError):
        mock_stdout = mocker.patch.object(dbt_cli_invocation_1.process, "stdout")
        mock_stdout.__enter__.side_effect = DagsterExecutionInterruptedError()
        mock_stdout.closed = False

        dbt_cli_invocation_1.wait()

    assert "Forwarding interrupt signal to dbt command" in caplog.text
    assert (
        f"dbt process terminated with exit code `{dbt_cli_invocation_1.process.returncode}`."
        in caplog.text
    )

    assert dbt_cli_invocation_1.process.returncode < 0


def test_dbt_cli_get_artifact(dbt: DbtCliResource) -> None:
    dbt_cli_invocation_1 = dbt.cli(["seed"]).wait()
    dbt_cli_invocation_2 = dbt.cli(["compile"]).wait()

    # `dbt seed` produces a manifest.json and run_results.json
    manifest_json_1 = dbt_cli_invocation_1.get_artifact("manifest.json")
    assert manifest_json_1
    assert dbt_cli_invocation_1.get_artifact("run_results.json")

    # `dbt compile` produces a manifest.json and run_results.json
    manifest_json_2 = dbt_cli_invocation_2.get_artifact("manifest.json")
    assert manifest_json_2
    assert dbt_cli_invocation_2.get_artifact("run_results.json")

    # `dbt compile` does not produce a sources.json
    with pytest.raises(Exception):
        dbt_cli_invocation_2.get_artifact("sources.json")

    # Artifacts are stored in separate paths by manipulating DBT_TARGET_PATH.
    # By default, they are stored in the `target` directory of the DBT project.
    assert dbt_cli_invocation_1.target_path.parent == test_jaffle_shop_path.joinpath("target")

    # As a result, their contents should be different, and newer artifacts
    # should not overwrite older ones.
    assert manifest_json_1 != manifest_json_2


def test_dbt_cli_target_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, dbt: DbtCliResource
) -> None:
    monkeypatch.setenv("DBT_TARGET_PATH", os.fspath(tmp_path))

    dbt_cli_invocation_1 = dbt.cli(["compile"]).wait()
    manifest_st_mtime_1 = dbt_cli_invocation_1.target_path.joinpath("manifest.json").stat().st_mtime

    dbt_cli_invocation_2 = dbt.cli(["compile"], target_path=dbt_cli_invocation_1.target_path).wait()
    manifest_st_mtime_2 = dbt_cli_invocation_2.target_path.joinpath("manifest.json").stat().st_mtime

    # The target path should be the same for both invocations
    assert dbt_cli_invocation_1.target_path == dbt_cli_invocation_2.target_path

    # Which results in the manifest.json being overwritten
    assert manifest_st_mtime_1 != manifest_st_mtime_2


@pytest.mark.parametrize("target_path", [Path("tmp"), Path("/tmp")])
def test_dbt_cli_target_path_env_var(
    monkeypatch: pytest.MonkeyPatch, dbt: DbtCliResource, target_path: Path
) -> None:
    expected_target_path = (
        target_path if target_path.is_absolute() else test_jaffle_shop_path.joinpath(target_path)
    )

    monkeypatch.setenv("DBT_TARGET_PATH", os.fspath(target_path))

    dbt_cli_invocation = dbt.cli(["compile"]).wait()

    assert dbt_cli_invocation.target_path.parent == expected_target_path
    assert dbt_cli_invocation.get_artifact("manifest.json")


def test_dbt_profile_configuration() -> None:
    dbt_cli_invocation = (
        DbtCliResource(
            project_dir=os.fspath(test_jaffle_shop_path), profile="jaffle_shop", target="dev"
        )
        .cli(["parse"])
        .wait()
    )

    assert dbt_cli_invocation.process.args == [
        "dbt",
        "parse",
        "--profile",
        "jaffle_shop",
        "--target",
        "dev",
    ]
    assert dbt_cli_invocation.is_successful()


@pytest.mark.parametrize(
    "profiles_dir", [None, test_jaffle_shop_path, os.fspath(test_jaffle_shop_path)]
)
def test_dbt_profiles_dir_configuration(profiles_dir: Union[str, Path]) -> None:
    assert (
        DbtCliResource(
            project_dir=os.fspath(test_jaffle_shop_path),
            profiles_dir=profiles_dir,
        )
        .cli(["parse"])
        .is_successful()
    )

    # profiles directory must exist
    with pytest.raises(ValidationError, match="does not exist"):
        DbtCliResource(project_dir=os.fspath(test_jaffle_shop_path), profiles_dir="nonexistent")

    # profiles directory must contain profile configuration
    with pytest.raises(ValidationError, match="specify a valid path to a dbt profile directory"):
        DbtCliResource(
            project_dir=os.fspath(test_jaffle_shop_path),
            profiles_dir=f"{os.fspath(test_jaffle_shop_path)}/models",
        )


def test_dbt_project_dir_conflicting_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DBT_PROJECT_DIR", "nonexistent")
    assert (
        DbtCliResource(
            project_dir=os.fspath(test_jaffle_shop_path),
        )
        .cli(["parse"])
        .is_successful()
    )


def test_dbt_partial_parse(dbt: DbtCliResource) -> None:
    test_jaffle_shop_path.joinpath("target", PARTIAL_PARSE_FILE_NAME).unlink(missing_ok=True)

    # Run `dbt compile` to generate the partial parse file
    dbt_cli_compile_invocation = dbt.cli(["compile"])

    # Assert that partial parsing was not used.
    assert dbt_cli_compile_invocation.is_successful()
    assert any(
        "Unable to do partial parsing" in event.raw_event["info"]["msg"]
        for event in dbt_cli_compile_invocation.stream_raw_events()
    )

    # Copy the partial parse file to the target directory
    partial_parse_file_path = test_jaffle_shop_path.joinpath(
        dbt_cli_compile_invocation.target_path,
        PARTIAL_PARSE_FILE_NAME,
    )
    original_target_path = test_jaffle_shop_path.joinpath("target", PARTIAL_PARSE_FILE_NAME)

    original_target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(partial_parse_file_path, original_target_path)

    # Assert that partial parsing was used.
    dbt_cli_compile_with_partial_parse_invocation = dbt.cli(["compile"])
    partial_parse_original_st_mtime = (
        dbt_cli_compile_with_partial_parse_invocation.target_path.joinpath(PARTIAL_PARSE_FILE_NAME)
        .stat()
        .st_mtime
    )

    assert dbt_cli_compile_with_partial_parse_invocation.is_successful()
    assert not any(
        "Unable to do partial parsing" in event.raw_event["info"]["msg"]
        for event in dbt_cli_compile_with_partial_parse_invocation.stream_raw_events()
    )

    # Assert that partial parsing is continues to happen when the target directory is reused.
    dbt_cli_compile_with_reused_partial_parse_invocation = dbt.cli(
        ["compile"], target_path=dbt_cli_compile_with_partial_parse_invocation.target_path
    )
    partial_parse_new_st_mtime = (
        dbt_cli_compile_with_reused_partial_parse_invocation.target_path.joinpath(
            PARTIAL_PARSE_FILE_NAME
        )
        .stat()
        .st_mtime
    )

    assert partial_parse_original_st_mtime == partial_parse_new_st_mtime
    assert dbt_cli_compile_with_reused_partial_parse_invocation.is_successful()
    assert not any(
        "Unable to do partial parsing" in event.raw_event["info"]["msg"]
        for event in dbt_cli_compile_with_reused_partial_parse_invocation.stream_raw_events()
    )


def test_dbt_cli_debug_execution(
    test_jaffle_shop_manifest: dict[str, Any], dbt: DbtCliResource
) -> None:
    @dbt_assets(manifest=test_jaffle_shop_manifest)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["--debug", "build"], context=context).stream()

    result = materialize([my_dbt_assets], resources={"dbt": dbt})
    assert result.success


@pytest.mark.skipif(
    version.parse(dbt_version) < version.parse("1.7.9"),
    reason="`dbt retry` with `--target-path` support is only available in `dbt-core>=1.7.9`",
)
def test_dbt_retry_execution(
    monkeypatch: pytest.MonkeyPatch,
    test_jaffle_shop_manifest: dict[str, Any],
    dbt: DbtCliResource,
    testrun_uid: str,
) -> None:
    monkeypatch.setenv(
        "DAGSTER_DBT_PYTEST_XDIST_DUCKDB_DBFILE_PATH", f"target/{testrun_uid}.duckdb"
    )

    @dbt_assets(manifest=test_jaffle_shop_manifest)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        dbt_invocation = dbt.cli(["run"], context=context, raise_on_error=False)

        assert not dbt_invocation.is_successful()
        assert not list(dbt_invocation.stream())

        yield from dbt.cli(["seed"], context=context).stream()
        yield from replace(
            dbt.cli(
                ["retry"],
                manifest=dbt_invocation.manifest,
                dagster_dbt_translator=dbt_invocation.dagster_dbt_translator,
                target_path=dbt_invocation.target_path,
            ),
            context=context,
        ).stream()

    result = materialize([my_dbt_assets], resources={"dbt": dbt})
    assert result.success
    assert len(result.filter_events(lambda event: event.is_successful_output)) == len(
        my_dbt_assets.keys_by_output_name.values()
    )


def test_dbt_source_freshness_execution(test_dbt_source_freshness_manifest: dict[str, Any]) -> None:
    @dbt_assets(manifest=test_dbt_source_freshness_manifest)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()
        yield from dbt.cli(["source", "freshness"], raise_on_error=False).stream()

    result = materialize(
        [my_dbt_assets],
        resources={"dbt": DbtCliResource(project_dir=os.fspath(test_dbt_source_freshness_path))},
    )
    assert result.success


def test_dbt_cli_asset_selection(
    test_jaffle_shop_manifest: dict[str, Any], dbt: DbtCliResource
) -> None:
    dbt_select = " ".join(
        [
            "jaffle_shop.raw_customers",
            "jaffle_shop.staging.stg_customers",
        ]
    )

    @dbt_assets(manifest=test_jaffle_shop_manifest, select=dbt_select)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        dbt_cli_invocation = dbt.cli(["build"], context=context)

        assert dbt_cli_invocation.process.args == ["dbt", "build", "--select", dbt_select]

        yield from dbt_cli_invocation.stream()

    result = materialize([my_dbt_assets], resources={"dbt": dbt})
    assert result.success


@pytest.mark.parametrize(
    "dagster_dbt_translator",
    [
        DagsterDbtTranslator(),
        DagsterDbtTranslator(
            settings=DagsterDbtTranslatorSettings(enable_dbt_selection_by_name=True)
        ),
    ],
)
def test_dbt_cli_subsetted_execution(
    test_jaffle_shop_manifest: dict[str, Any],
    dbt: DbtCliResource,
    dagster_dbt_translator: DagsterDbtTranslator,
) -> None:
    dbt_select = [
        "jaffle_shop.raw_customers",
        "jaffle_shop.staging.stg_customers",
    ]
    if dagster_dbt_translator.settings.enable_dbt_selection_by_name:
        dbt_select = [
            "raw_customers",
            "stg_customers",
        ]

    @dbt_assets(manifest=test_jaffle_shop_manifest, dagster_dbt_translator=dagster_dbt_translator)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        dbt_cli_invocation = dbt.cli(["build"], context=context)

        dbt_cli_args: list[str] = list(dbt_cli_invocation.process.args)  # type: ignore
        *dbt_args, dbt_select_args = dbt_cli_args

        assert dbt_args == ["dbt", "build", "--select"]
        assert set(dbt_select_args.split()) == set(dbt_select)

        yield from dbt_cli_invocation.stream()

    result = materialize(
        [my_dbt_assets],
        resources={"dbt": dbt},
        selection=build_dbt_asset_selection(
            [my_dbt_assets],
            dbt_select=" ".join(dbt_select),
        ),
    )
    assert result.success


@pytest.mark.parametrize("exclude", [None, "fqn:test_jaffle_shop.customers"])
def test_dbt_cli_default_selection(
    test_jaffle_shop_manifest: dict[str, Any], dbt: DbtCliResource, exclude: Optional[str]
) -> None:
    @dbt_assets(manifest=test_jaffle_shop_manifest, exclude=exclude)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        dbt_cli_invocation = dbt.cli(["build"], context=context)

        expected_args = ["dbt", "build", "--select", "fqn:*"]
        if exclude:
            expected_args += ["--exclude", exclude]

        assert dbt_cli_invocation.process.args == expected_args

        yield from dbt_cli_invocation.stream()

    result = materialize([my_dbt_assets], resources={"dbt": dbt})
    assert result.success


def test_dbt_cli_defer_args(monkeypatch: pytest.MonkeyPatch, testrun_uid: str) -> None:
    monkeypatch.setenv("DAGSTER_DBT_JAFFLE_SCHEMA", "prod")

    project = DbtProject(project_dir=test_jaffle_shop_path, state_path=Path("state", testrun_uid))
    dbt = DbtCliResource(project_dir=project)

    dbt.cli(["--quiet", "parse"], target_path=project.target_path).wait()

    @dbt_assets(manifest=project.manifest_path)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build", *dbt.get_defer_args()], context=context).stream()

    result = materialize([my_dbt_assets], resources={"dbt": dbt})
    assert result.success

    # Defer will not work since the manifest is not in the state directory.
    monkeypatch.setenv("DAGSTER_DBT_JAFFLE_SCHEMA", "staging")
    result = materialize(
        [my_dbt_assets], resources={"dbt": dbt}, selection="orders", raise_on_error=False
    )
    assert len(dbt.get_state_args()) == 0
    assert not result.success

    # Defer works after copying the manifest into the state directory.
    assert project.state_path
    project.state_path.mkdir(parents=True, exist_ok=True)
    shutil.copy(project.manifest_path, project.state_path.joinpath("manifest.json"))

    result = materialize([my_dbt_assets], resources={"dbt": dbt}, selection="orders")
    assert result.success

    assert len(dbt.get_state_args()) == 2


def test_dbt_cli_op_execution(
    test_jaffle_shop_manifest: dict[str, Any], dbt: DbtCliResource
) -> None:
    @op(out={})
    def my_dbt_op_yield_events(context: OpExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], manifest=test_jaffle_shop_manifest, context=context).stream()

    @op(out=Out(Nothing))
    def my_dbt_op_yield_events_with_downstream(context: OpExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], manifest=test_jaffle_shop_manifest, context=context).stream()

    @op(ins={"depends_on": In(dagster_type=Nothing)})
    def my_downstream_op(): ...

    @job
    def my_dbt_job_yield_events():
        my_dbt_op_yield_events()
        my_downstream_op(depends_on=my_dbt_op_yield_events_with_downstream())

    result = my_dbt_job_yield_events.execute_in_process(resources={"dbt": dbt})
    assert result.success


def test_dbt_adapter(dbt: DbtCliResource) -> None:
    assert dbt.cli(["compile"]).adapter
    assert dbt.cli(["build"]).adapter
    assert dbt.cli(["parse"]).adapter
    assert dbt.cli(["source", "freshness"]).adapter


def test_dbt_adapter_with_profile_vars(dbt_with_profile_vars: DbtCliResource) -> None:
    assert dbt_with_profile_vars.cli(
        ["build", '--vars={"duckdb_dbfile_path": "target/local.duckdb", "jaffle_schema": "dev"}']
    ).adapter


def test_custom_subclass():
    CustomDbtCliResource = pydantic.create_model(
        "CustomDbtCliResource",
        __base__=DbtCliResource,
        custom_field=(str, ...),
    )
    custom = CustomDbtCliResource(
        project_dir=os.fspath(test_jaffle_shop_path), custom_field="custom_value"
    )
    assert isinstance(custom, DbtCliResource)


def test_metadata(test_jaffle_shop_manifest: dict[str, Any], dbt: DbtCliResource) -> None:
    def assert_on_expected_metadata(metadata):
        assert isinstance(metadata["Execution Duration"], FloatMetadataValue)
        assert cast(float, metadata["Execution Duration"].value) > 0

        assert isinstance(metadata["unique_id"], TextMetadataValue)
        assert isinstance(metadata["invocation_id"], TextMetadataValue)

    @dbt_assets(manifest=test_jaffle_shop_manifest)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    result = materialize([my_dbt_assets], resources={"dbt": dbt})
    outputs = [event for event in result.all_events if event.is_successful_output]
    assert len(outputs) == 28

    # materialization outputs have metadata, asset check outputs don't
    outputs_with_metadata = [output for output in outputs if output.step_output_data.metadata]
    assert len(outputs_with_metadata) == 8

    for output in outputs_with_metadata:
        assert_on_expected_metadata(output.step_output_data.metadata)

    materializations = result.get_asset_materialization_events()
    assert len(materializations) == 8

    for materialization in materializations:
        assert_on_expected_metadata(
            materialization.step_materialization_data.materialization.metadata
        )
