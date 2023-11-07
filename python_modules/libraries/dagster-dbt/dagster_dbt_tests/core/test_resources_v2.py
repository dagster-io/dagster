import atexit
import json
import os
import shutil
from pathlib import Path
from typing import List, Optional, Union, cast

import pytest
from dagster import (
    AssetCheckResult,
    AssetMaterialization,
    AssetObservation,
    FloatMetadataValue,
    TextMetadataValue,
    job,
    materialize,
    op,
)
from dagster._core.execution.context.compute import AssetExecutionContext, OpExecutionContext
from dagster_dbt import dbt_assets
from dagster_dbt.asset_utils import build_dbt_asset_selection
from dagster_dbt.core.resources_v2 import (
    PARTIAL_PARSE_FILE_NAME,
    DbtCliEventMessage,
    DbtCliResource,
)
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator, DagsterDbtTranslatorSettings
from dagster_dbt.dbt_manifest import DbtManifestParam
from dagster_dbt.errors import DagsterDbtCliRuntimeError
from pydantic import ValidationError
from pytest_mock import MockerFixture

from ..conftest import TEST_PROJECT_DIR

pytest.importorskip("dbt.version", minversion="1.4")


manifest_path = Path(TEST_PROJECT_DIR).joinpath("manifest.json")
manifest = json.loads(manifest_path.read_bytes())

test_exception_messages_dbt_project_dir = (
    Path(__file__).joinpath("..", "..", "dbt_projects", "test_dagster_exceptions").resolve()
)


@pytest.mark.parametrize("global_config_flags", [[], ["--quiet"]])
@pytest.mark.parametrize("command", ["run", "parse"])
def test_dbt_cli(global_config_flags: List[str], command: str) -> None:
    dbt = DbtCliResource(project_dir=TEST_PROJECT_DIR, global_config_flags=global_config_flags)
    dbt_cli_invocation = dbt.cli([command])

    assert dbt_cli_invocation.process.args == ["dbt", *global_config_flags, command]
    assert dbt_cli_invocation.is_successful()
    assert dbt_cli_invocation.process.returncode == 0
    assert dbt_cli_invocation.target_path.joinpath("dbt.log").exists()


def test_dbt_cli_executable() -> None:
    dbt_executable = cast(str, shutil.which("dbt"))
    dbt = DbtCliResource(project_dir=TEST_PROJECT_DIR, dbt_executable=dbt_executable)

    assert dbt.cli(["run"], manifest=manifest).is_successful()

    dbt = DbtCliResource(project_dir=TEST_PROJECT_DIR, dbt_executable=Path(dbt_executable))  # type: ignore

    assert dbt.cli(["run"], manifest=manifest).is_successful()

    # dbt executable must exist
    with pytest.raises(ValidationError, match="does not exist"):
        DbtCliResource(project_dir=TEST_PROJECT_DIR, dbt_executable="nonexistent")


@pytest.mark.parametrize("manifest", [None, manifest, manifest_path, os.fspath(manifest_path)])
def test_dbt_cli_manifest_argument(manifest: DbtManifestParam) -> None:
    dbt = DbtCliResource(project_dir=TEST_PROJECT_DIR)

    assert dbt.cli(["run"], manifest=manifest).is_successful()


def test_dbt_cli_project_dir_path() -> None:
    dbt = DbtCliResource(project_dir=Path(TEST_PROJECT_DIR))  # type: ignore

    assert Path(dbt.project_dir).is_absolute()
    assert dbt.cli(["run"]).is_successful()

    # project directory must exist
    with pytest.raises(ValidationError, match="does not exist"):
        DbtCliResource(project_dir="nonexistent")

    # project directory must be a valid dbt project
    with pytest.raises(ValidationError, match="specify a valid path to a dbt project"):
        DbtCliResource(project_dir=f"{TEST_PROJECT_DIR}/models")


def test_dbt_cli_failure() -> None:
    dbt = DbtCliResource(project_dir=os.fspath(test_exception_messages_dbt_project_dir))
    dbt_cli_invocation = dbt.cli(["run", "--selector", "nonexistent"])

    with pytest.raises(
        DagsterDbtCliRuntimeError, match="Could not find selector named nonexistent"
    ):
        dbt_cli_invocation.wait()

    assert not dbt_cli_invocation.is_successful()
    assert dbt_cli_invocation.process.returncode == 2
    assert dbt_cli_invocation.target_path.joinpath("dbt.log").exists()

    dbt = DbtCliResource(
        project_dir=os.fspath(test_exception_messages_dbt_project_dir),
        target="error_dev",
    )

    with pytest.raises(
        DagsterDbtCliRuntimeError, match="Env var required but not provided: 'DBT_DUCKDB_THREADS'"
    ):
        dbt.cli(["parse"]).wait()


def test_dbt_cli_subprocess_cleanup(caplog: pytest.LogCaptureFixture) -> None:
    dbt = DbtCliResource(project_dir=TEST_PROJECT_DIR)
    dbt_cli_invocation_1 = dbt.cli(["run"])

    assert dbt_cli_invocation_1.process.returncode is None

    atexit._run_exitfuncs()  # noqa: SLF001

    assert "Terminating the execution of dbt command." in caplog.text
    assert not dbt_cli_invocation_1.is_successful()
    assert dbt_cli_invocation_1.process.returncode < 0

    caplog.clear()

    dbt_cli_invocation_2 = dbt.cli(["run"]).wait()

    atexit._run_exitfuncs()  # noqa: SLF001

    assert "Terminating the execution of dbt command." not in caplog.text
    assert dbt_cli_invocation_2.is_successful()
    assert dbt_cli_invocation_2.process.returncode == 0


def test_dbt_cli_get_artifact() -> None:
    dbt = DbtCliResource(project_dir=TEST_PROJECT_DIR)

    dbt_cli_invocation_1 = dbt.cli(["run"]).wait()
    dbt_cli_invocation_2 = dbt.cli(["compile"]).wait()

    # `dbt run` produces a manifest.json and run_results.json
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
    assert dbt_cli_invocation_1.target_path.parent == Path(TEST_PROJECT_DIR, "target")

    # As a result, their contents should be different, and newer artifacts
    # should not overwrite older ones.
    assert manifest_json_1 != manifest_json_2


def test_dbt_cli_target_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DBT_TARGET_PATH", os.fspath(tmp_path))
    dbt = DbtCliResource(project_dir=TEST_PROJECT_DIR)

    dbt_cli_invocation_1 = dbt.cli(["compile"]).wait()
    manifest_st_mtime_1 = dbt_cli_invocation_1.target_path.joinpath("manifest.json").stat().st_mtime

    dbt_cli_invocation_2 = dbt.cli(["compile"], target_path=dbt_cli_invocation_1.target_path).wait()
    manifest_st_mtime_2 = dbt_cli_invocation_2.target_path.joinpath("manifest.json").stat().st_mtime

    # The target path should be the same for both invocations
    assert dbt_cli_invocation_1.target_path == dbt_cli_invocation_2.target_path

    # Which results in the manifest.json being overwritten
    assert manifest_st_mtime_1 != manifest_st_mtime_2


@pytest.mark.parametrize("target_path", [Path("tmp"), Path("/tmp")])
def test_dbt_cli_target_path_env_var(monkeypatch: pytest.MonkeyPatch, target_path: Path) -> None:
    dbt = DbtCliResource(project_dir=TEST_PROJECT_DIR)
    expected_target_path = (
        target_path if target_path.is_absolute() else Path(TEST_PROJECT_DIR).joinpath(target_path)
    )

    monkeypatch.setenv("DBT_TARGET_PATH", os.fspath(target_path))

    dbt_cli_invocation = dbt.cli(["compile"]).wait()

    assert dbt_cli_invocation.target_path.parent == expected_target_path
    assert dbt_cli_invocation.get_artifact("manifest.json")


def test_dbt_profile_configuration() -> None:
    dbt = DbtCliResource(project_dir=TEST_PROJECT_DIR, profile="duckdb", target="dev")

    dbt_cli_invocation = dbt.cli(["parse"]).wait()

    assert dbt_cli_invocation.process.args == [
        "dbt",
        "parse",
        "--profile",
        "duckdb",
        "--target",
        "dev",
    ]
    assert dbt_cli_invocation.is_successful()


@pytest.mark.parametrize("profiles_dir", [None, TEST_PROJECT_DIR, Path(TEST_PROJECT_DIR)])
def test_dbt_profiles_dir_configuration(profiles_dir: Union[str, Path]) -> None:
    dbt = DbtCliResource(
        project_dir=TEST_PROJECT_DIR,
        profiles_dir=profiles_dir,  # type: ignore
    )

    assert dbt.cli(["parse"]).is_successful()

    # profiles directory must exist
    with pytest.raises(ValidationError, match="does not exist"):
        DbtCliResource(project_dir=TEST_PROJECT_DIR, profiles_dir="nonexistent")

    # profiles directory must contain profile configuration
    with pytest.raises(ValidationError, match="specify a valid path to a dbt profile directory"):
        DbtCliResource(project_dir=TEST_PROJECT_DIR, profiles_dir=f"{TEST_PROJECT_DIR}/models")


def test_dbt_without_partial_parse() -> None:
    dbt = DbtCliResource(project_dir=TEST_PROJECT_DIR)

    dbt.cli(["clean"]).wait()

    dbt_cli_compile_without_partial_parse_invocation = dbt.cli(["compile"])

    assert dbt_cli_compile_without_partial_parse_invocation.is_successful()
    assert any(
        "Unable to do partial parsing" in event.raw_event["info"]["msg"]
        for event in dbt_cli_compile_without_partial_parse_invocation.stream_raw_events()
    )


def test_dbt_with_partial_parse() -> None:
    dbt = DbtCliResource(project_dir=TEST_PROJECT_DIR)

    dbt.cli(["clean"]).wait()

    # Run `dbt compile` to generate the partial parse file
    dbt_cli_compile_invocation = dbt.cli(["compile"]).wait()

    # Copy the partial parse file to the target directory
    partial_parse_file_path = Path(
        TEST_PROJECT_DIR, dbt_cli_compile_invocation.target_path, PARTIAL_PARSE_FILE_NAME
    )
    original_target_path = Path(TEST_PROJECT_DIR, "target", PARTIAL_PARSE_FILE_NAME)

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


def test_dbt_cli_debug_execution() -> None:
    @dbt_assets(manifest=manifest)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["--debug", "run"], context=context).stream()

    result = materialize(
        [my_dbt_assets],
        resources={
            "dbt": DbtCliResource(project_dir=TEST_PROJECT_DIR),
        },
    )
    assert result.success


def test_dbt_cli_subsetted_execution() -> None:
    dbt_select = " ".join(
        [
            "fqn:dagster_dbt_test_project.subdir.least_caloric",
            "fqn:dagster_dbt_test_project.sort_by_calories",
        ]
    )

    @dbt_assets(manifest=manifest, select=dbt_select)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        dbt_cli_invocation = dbt.cli(["run"], context=context)

        assert dbt_cli_invocation.process.args == ["dbt", "run", "--select", dbt_select]

        yield from dbt_cli_invocation.stream()

    result = materialize(
        [my_dbt_assets],
        resources={
            "dbt": DbtCliResource(project_dir=TEST_PROJECT_DIR),
        },
    )
    assert result.success


def test_dbt_cli_asset_selection() -> None:
    dbt_select = [
        "fqn:dagster_dbt_test_project.subdir.least_caloric",
        "fqn:dagster_dbt_test_project.sort_by_calories",
    ]

    @dbt_assets(manifest=manifest)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        dbt_cli_invocation = dbt.cli(["run"], context=context)

        dbt_cli_args: List[str] = list(dbt_cli_invocation.process.args)  # type: ignore
        *dbt_args, dbt_select_args = dbt_cli_args

        assert dbt_args == ["dbt", "run", "--select"]
        assert set(dbt_select_args.split()) == set(dbt_select)

        yield from dbt_cli_invocation.stream()

    result = materialize(
        [my_dbt_assets],
        resources={
            "dbt": DbtCliResource(project_dir=TEST_PROJECT_DIR),
        },
        selection=build_dbt_asset_selection(
            [my_dbt_assets],
            dbt_select=(
                "fqn:dagster_dbt_test_project.subdir.least_caloric"
                " fqn:dagster_dbt_test_project.sort_by_calories"
            ),
        ),
    )
    assert result.success


@pytest.mark.parametrize("exclude", [None, "fqn:dagster_dbt_test_project.subdir.least_caloric"])
def test_dbt_cli_default_selection(exclude: Optional[str]) -> None:
    @dbt_assets(manifest=manifest, exclude=exclude)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        dbt_cli_invocation = dbt.cli(["run"], context=context)

        expected_args = ["dbt", "run", "--select", "fqn:*"]
        if exclude:
            expected_args += ["--exclude", exclude]

        assert dbt_cli_invocation.process.args == expected_args

        yield from dbt_cli_invocation.stream()

    result = materialize(
        [my_dbt_assets],
        resources={
            "dbt": DbtCliResource(project_dir=TEST_PROJECT_DIR),
        },
    )
    assert result.success


def test_dbt_cli_op_execution() -> None:
    dbt = DbtCliResource(project_dir=TEST_PROJECT_DIR)

    @op
    def my_dbt_op(dbt: DbtCliResource):
        dbt.cli(["run"]).wait()

    @job
    def my_dbt_job():
        my_dbt_op()

    result = my_dbt_job.execute_in_process(resources={"dbt": dbt})

    assert result.success

    @op(out={})
    def my_dbt_op_yield_events(context: OpExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], manifest=manifest, context=context).stream()

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
                "unique_id": "a.b.c",
                "resource_type": "model",
                "node_status": "failure",
                "node_finished_at": "2024-01-01T00:00:00Z",
                "meta": {},
            },
        },
        {
            "node_info": {
                "unique_id": "a.b.c",
                "resource_type": "macro",
                "node_status": "success",
                "node_finished_at": "2024-01-01T00:00:00Z",
                "meta": {},
            },
        },
        {
            "node_info": {
                "unique_id": "a.b.c",
                "resource_type": "model",
                "node_status": "failure",
                "meta": {},
            },
        },
        {
            "node_info": {
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
                "level": "info",
                "invocation_id": "1-2-3",
            },
            "data": data,
        }
    ).to_default_asset_events(manifest={})

    assert list(asset_events) == []


def test_to_default_asset_output_events() -> None:
    raw_event = {
        "info": {
            "level": "info",
            "invocation_id": "1-2-3",
        },
        "data": {
            "node_info": {
                "unique_id": "a.b.c",
                "resource_type": "model",
                "node_name": "node_name",
                "node_status": "success",
                "node_started_at": "2024-01-01T00:00:00Z",
                "node_finished_at": "2024-01-01T00:01:00Z",
                "meta": {},
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
        DbtCliEventMessage(raw_event=raw_event).to_default_asset_events(manifest=manifest)
    )

    assert len(asset_events) == 1
    assert all(isinstance(e, AssetMaterialization) for e in asset_events)
    assert asset_events[0].metadata == {
        "unique_id": TextMetadataValue("a.b.c"),
        "invocation_id": TextMetadataValue("1-2-3"),
        "Execution Duration": FloatMetadataValue(60.0),
    }


@pytest.mark.parametrize("is_asset_check", [False, True])
def test_dbt_tests_to_events(mocker: MockerFixture, is_asset_check: bool) -> None:
    manifest = {
        "nodes": {
            "model.a": {
                "resource_type": "model",
                "config": {},
                "name": "model.a",
            },
            "test.a": {
                "resource_type": "test",
                "config": {
                    "severity": "ERROR",
                },
                "name": "test.a",
                "attached_node": "model.a" if is_asset_check else None,
            },
        },
        "sources": {},
        "parent_map": {
            "test.a": [
                "model.a",
            ]
        },
    }
    raw_event = {
        "info": {
            "level": "info",
            "invocation_id": "1-2-3",
        },
        "data": {
            "node_info": {
                "unique_id": "test.a",
                "resource_type": "test",
                "node_name": "node_name.test.a",
                "node_status": "success",
                "node_finished_at": "2024-01-01T00:00:00Z",
            },
        },
    }

    mock_context = mocker.MagicMock()
    mock_context.has_assets_def = True

    dagster_dbt_translator = DagsterDbtTranslator(
        settings=DagsterDbtTranslatorSettings(enable_asset_checks=is_asset_check)
    )

    asset_events = list(
        DbtCliEventMessage(raw_event=raw_event).to_default_asset_events(
            manifest=manifest,
            dagster_dbt_translator=dagster_dbt_translator,
            context=mock_context,
        )
    )

    expected_event_type = AssetCheckResult if is_asset_check else AssetObservation

    assert len(asset_events) == 1
    assert all(isinstance(e, expected_event_type) for e in asset_events)
