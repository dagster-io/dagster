import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast

import pytest
from dagster import (
    AssetMaterialization,
    FloatMetadataValue,
    IntMetadataValue,
    TextMetadataValue,
    job,
    materialize,
    op,
)
from dagster._core.errors import DagsterExecutionInterruptedError
from dagster._core.execution.context.compute import AssetExecutionContext, OpExecutionContext
from dagster_dbt import dbt_assets
from dagster_dbt.asset_utils import build_dbt_asset_selection
from dagster_dbt.core.resources_v2 import (
    PARTIAL_PARSE_FILE_NAME,
    DbtCliEventMessage,
    DbtCliResource,
)
from dagster_dbt.errors import DagsterDbtCliRuntimeError
from pydantic import ValidationError
from pytest_mock import MockerFixture

from ..dbt_projects import test_exceptions_path, test_jaffle_shop_path


@pytest.fixture(name="dbt", scope="module")
def dbt_fixture() -> DbtCliResource:
    return DbtCliResource(project_dir=os.fspath(test_jaffle_shop_path))


@pytest.mark.parametrize("global_config_flags", [[], ["--quiet"]])
def test_dbt_cli(global_config_flags: List[str]) -> None:
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
    assert (
        DbtCliResource(project_dir=os.fspath(test_jaffle_shop_path), dbt_executable=dbt_executable)
        .cli(["parse"])
        .is_successful()
    )

    assert (
        DbtCliResource(
            project_dir=os.fspath(test_jaffle_shop_path),
            dbt_executable=Path(dbt_executable),  # type: ignore
        )
        .cli(["parse"])
        .is_successful()
    )

    # dbt executable must exist
    with pytest.raises(ValidationError, match="does not exist"):
        DbtCliResource(project_dir=os.fspath(test_jaffle_shop_path), dbt_executable="nonexistent")


def test_dbt_cli_project_dir_path() -> None:
    dbt = DbtCliResource(project_dir=test_jaffle_shop_path)  # type: ignore

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
    assert dbt_cli_invocation.process.returncode == 2
    assert dbt_cli_invocation.target_path.joinpath("dbt.log").exists()

    dbt = DbtCliResource(project_dir=os.fspath(test_exceptions_path), target="error_dev")

    with pytest.raises(
        DagsterDbtCliRuntimeError, match="Env var required but not provided: 'DBT_DUCKDB_THREADS'"
    ):
        dbt.cli(["parse"]).wait()


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
            profiles_dir=profiles_dir,  # type: ignore
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
    test_jaffle_shop_manifest: Dict[str, Any], dbt: DbtCliResource
) -> None:
    @dbt_assets(manifest=test_jaffle_shop_manifest)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["--debug", "build"], context=context).stream()

    result = materialize([my_dbt_assets], resources={"dbt": dbt})
    assert result.success


def test_dbt_cli_adapter_metadata(
    test_jaffle_shop_manifest: Dict[str, Any], dbt: DbtCliResource
) -> None:
    @dbt_assets(manifest=test_jaffle_shop_manifest)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        # For `dbt-duckdb`, the `rows_affected` metadata is only emitted for seed files.
        for event in dbt.cli(["seed"], context=context).stream():
            assert event.metadata.get("rows_affected")

            yield event

    result = materialize([my_dbt_assets], resources={"dbt": dbt})
    assert result.success


def test_dbt_cli_asset_selection(
    test_jaffle_shop_manifest: Dict[str, Any], dbt: DbtCliResource
) -> None:
    dbt_select = " ".join(
        [
            "fqn:jaffle_shop.raw_customers",
            "fqn:jaffle_shop.staging.stg_customers",
        ]
    )

    @dbt_assets(manifest=test_jaffle_shop_manifest, select=dbt_select)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        dbt_cli_invocation = dbt.cli(["build"], context=context)

        assert dbt_cli_invocation.process.args == ["dbt", "build", "--select", dbt_select]

        yield from dbt_cli_invocation.stream()

    result = materialize([my_dbt_assets], resources={"dbt": dbt})
    assert result.success


def test_dbt_cli_subsetted_execution(
    test_jaffle_shop_manifest: Dict[str, Any], dbt: DbtCliResource
) -> None:
    dbt_select = [
        "fqn:jaffle_shop.raw_customers",
        "fqn:jaffle_shop.staging.stg_customers",
    ]

    @dbt_assets(manifest=test_jaffle_shop_manifest)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        dbt_cli_invocation = dbt.cli(["build"], context=context)

        dbt_cli_args: List[str] = list(dbt_cli_invocation.process.args)  # type: ignore
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
    test_jaffle_shop_manifest: Dict[str, Any], dbt: DbtCliResource, exclude: Optional[str]
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


def test_dbt_cli_op_execution(
    test_jaffle_shop_manifest: Dict[str, Any], dbt: DbtCliResource
) -> None:
    @op(out={})
    def my_dbt_op_yield_events(context: OpExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], manifest=test_jaffle_shop_manifest, context=context).stream()

    @job
    def my_dbt_job_yield_events():
        my_dbt_op_yield_events()

    result = my_dbt_job_yield_events.execute_in_process(resources={"dbt": dbt})
    assert result.success


@pytest.mark.parametrize(
    "data",
    [
        {},
        {
            "node_info": {
                "materialized": "table",
                "unique_id": "a.b.c",
                "resource_type": "model",
                "node_status": "failure",
                "node_finished_at": "2024-01-01T00:00:00Z",
                "meta": {},
            },
        },
        {
            "node_info": {
                "materialized": "table",
                "unique_id": "a.b.c",
                "resource_type": "macro",
                "node_status": "success",
                "node_finished_at": "2024-01-01T00:00:00Z",
                "meta": {},
            },
        },
        {
            "node_info": {
                "materialized": "table",
                "unique_id": "a.b.c",
                "resource_type": "model",
                "node_status": "failure",
                "meta": {},
            },
        },
        {
            "node_info": {
                "materialized": "test",
                "unique_id": "a.b.c",
                "resource_type": "test",
                "node_status": "success",
                "meta": {},
            },
        },
    ],
    ids=[
        "node info missing",
        "node status failure",
        "not refable",
        "not successful execution",
        "not finished test execution",
    ],
)
def test_no_default_asset_events_emitted(data: dict) -> None:
    asset_events = DbtCliEventMessage(
        raw_event={
            "info": {
                "name": "NodeFinished",
                "level": "info",
                "invocation_id": "1-2-3",
            },
            "data": data,
        },
        event_history_metadata={},
    ).to_default_asset_events(manifest={"nodes": {"a.b.c": {}}})

    assert list(asset_events) == []


def test_to_default_asset_output_events() -> None:
    raw_event = {
        "info": {
            "name": "NodeFinished",
            "level": "info",
            "invocation_id": "1-2-3",
        },
        "data": {
            "node_info": {
                "materialized": "table",
                "unique_id": "a.b.c",
                "resource_type": "model",
                "node_name": "node_name",
                "node_status": "success",
                "node_started_at": "2024-01-01T00:00:00Z",
                "node_finished_at": "2024-01-01T00:01:00Z",
                "meta": {},
            },
            "run_result": {
                "adapter_response": {
                    "rows_affected": 100,
                }
            },
        },
    }
    manifest = {
        "nodes": {
            "a.b.c": {
                "meta": {
                    "dagster": {
                        "asset_key": ["a", "b", "c"],
                    },
                },
            },
        },
    }

    asset_events = list(
        DbtCliEventMessage(raw_event=raw_event, event_history_metadata={}).to_default_asset_events(
            manifest=manifest
        )
    )

    assert len(asset_events) == 1
    assert all(isinstance(e, AssetMaterialization) for e in asset_events)
    assert asset_events[0].metadata == {
        "unique_id": TextMetadataValue("a.b.c"),
        "invocation_id": TextMetadataValue("1-2-3"),
        "Execution Duration": FloatMetadataValue(60.0),
        "rows_affected": IntMetadataValue(100),
    }
