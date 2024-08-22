import os
import shutil
from pathlib import Path
from typing import cast

import pydantic
import pytest
from dagster import In, Nothing, Out, job, op
from dagster._core.errors import DagsterExecutionInterruptedError
from dagster._core.execution.context.compute import OpExecutionContext
from dagster_sdf.constants import (
    DAGSTER_SDF_CATALOG_NAME,
    DAGSTER_SDF_DIALECT,
    DAGSTER_SDF_PURPOSE,
    DAGSTER_SDF_SCHEMA_NAME,
    DAGSTER_SDF_TABLE_ID,
    DAGSTER_SDF_TABLE_NAME,
    SDF_DAGSTER_OUTPUT_DIR,
    SDF_TARGET_DIR,
)
from dagster_sdf.resource import SdfCliResource
from pydantic import ValidationError
from pytest_mock import MockerFixture

from dagster_sdf_tests.sdf_workspaces import moms_flower_shop_path


@pytest.fixture(name="sdf", scope="module")
def sdf_fixture() -> SdfCliResource:
    return SdfCliResource(workspace_dir=os.fspath(moms_flower_shop_path))


def test_sdf_cli() -> None:
    expected_sdf_cli_args = [
        "sdf",
        "--log-level",
        "info",
        "compile",
        "--save",
        "table-deps",
        "--environment",
        "dbg",
        "--target-dir",
    ]

    sdf = SdfCliResource(workspace_dir=os.fspath(moms_flower_shop_path))
    sdf_cli_invocation = sdf.cli(["compile", "--save", "table-deps"])
    *_, target_dir = sdf_cli_invocation.process.args  # type: ignore

    assert sdf_cli_invocation.process.args == [*expected_sdf_cli_args, target_dir]
    assert sdf_cli_invocation.is_successful()
    assert sdf_cli_invocation.process.returncode == 0
    assert sdf_cli_invocation.target_dir.joinpath(
        "sdftarget", "dbg", "makefile-compile.json"
    ).exists()


def test_sdf_cli_executable() -> None:
    sdf_executable = cast(str, shutil.which("sdf"))
    invocation = SdfCliResource(
        workspace_dir=os.fspath(moms_flower_shop_path), sdf_executable=sdf_executable
    ).cli(["compile", "--save", "table-deps"])
    assert invocation.is_successful()
    assert not invocation.get_error()

    # sdf executable must exist
    with pytest.raises(ValidationError, match="does not exist"):
        SdfCliResource(workspace_dir=os.fspath(moms_flower_shop_path), sdf_executable="nonexistent")


def test_sdf_cli_workspace_dir_path() -> None:
    sdf = SdfCliResource(workspace_dir=os.fspath(moms_flower_shop_path))

    assert Path(sdf.workspace_dir).is_absolute()
    assert sdf.cli(["compile", "--save", "table-deps"]).is_successful()

    # workspace directory must exist
    with pytest.raises(ValidationError, match="does not exist"):
        SdfCliResource(workspace_dir="nonexistent")

    # workspace directory must be a valid sdf workspace
    with pytest.raises(ValidationError, match="specify a valid path to an sdf workspace."):
        SdfCliResource(workspace_dir=f"{os.fspath(moms_flower_shop_path)}/models")


def test_sdf_cli_subprocess_cleanup(
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
    sdf: SdfCliResource,
) -> None:
    sdf_cli_invocation_1 = sdf.cli(["run"])

    assert sdf_cli_invocation_1.process.returncode is None

    with pytest.raises(DagsterExecutionInterruptedError):
        mock_stdout = mocker.patch.object(sdf_cli_invocation_1.process, "stdout")
        mock_stdout.__enter__.side_effect = DagsterExecutionInterruptedError()
        mock_stdout.closed = False

        sdf_cli_invocation_1.wait()

    assert "Forwarding interrupt signal to sdf command" in caplog.text
    assert sdf_cli_invocation_1.process.returncode < 0


def test_sdf_cli_get_artifact(sdf: SdfCliResource) -> None:
    sdf_cli_invocation_1 = sdf.cli(["compile"]).wait()
    sdf_cli_invocation_2 = sdf.cli(["run"]).wait()

    # `sdf compile` produces a makefile-compile.json
    makefile_compile_json = sdf_cli_invocation_1.get_artifact("makefile-compile.json")
    assert makefile_compile_json

    # `sdf compile` produces a makefile-run.json
    makefile_run_json = sdf_cli_invocation_2.get_artifact("makefile-run.json")
    assert makefile_run_json

    # Artifacts are stored in separate paths by manipulating SDF_TARGET_PATH.
    # By default, they are stored in the `target` directory of the SDF workspace.
    assert sdf_cli_invocation_1.target_dir.parent == moms_flower_shop_path.joinpath(
        SDF_DAGSTER_OUTPUT_DIR
    )

    # As a result, their contents should be different, and newer artifacts
    # should not overwrite older ones.
    assert makefile_compile_json != makefile_run_json


def test_sdf_cli_target_dir(tmp_path: Path, sdf: SdfCliResource) -> None:
    sdf_cli_invocation_1 = sdf.cli(["compile"], target_dir=tmp_path).wait()
    manifest_st_mtime_1 = (
        sdf_cli_invocation_1.target_dir.joinpath(
            SDF_TARGET_DIR, sdf_cli_invocation_1.environment, "makefile-compile.json"
        )
        .stat()
        .st_mtime
    )

    sdf_cli_invocation_2 = sdf.cli(["compile"], target_dir=sdf_cli_invocation_1.target_dir).wait()
    manifest_st_mtime_2 = (
        sdf_cli_invocation_2.target_dir.joinpath(
            SDF_TARGET_DIR, sdf_cli_invocation_2.environment, "makefile-compile.json"
        )
        .stat()
        .st_mtime
    )

    # The target path should be the same for both invocations
    assert sdf_cli_invocation_1.target_dir == sdf_cli_invocation_2.target_dir

    # Timestamps should be equal since the cache is entirely reused
    assert manifest_st_mtime_1 == manifest_st_mtime_2


def test_sdf_environment_configuration(sdf: SdfCliResource) -> None:
    expected_sdf_cli_args = [
        "sdf",
        "--log-level",
        "info",
        "compile",
        "--environment",
        "dev",
        "--target-dir",
    ]

    sdf_cli_invocation = sdf.cli(["compile"], environment="dev").wait()
    *_, target_dir = list(sdf_cli_invocation.process.args)  # type: ignore

    assert sdf_cli_invocation.process.args == [*expected_sdf_cli_args, target_dir]
    assert sdf_cli_invocation.is_successful()


def test_sdf_cli_op_execution(sdf: SdfCliResource) -> None:
    @op(out={})
    def my_sdf_op_yield_events(context: OpExecutionContext, sdf: SdfCliResource):
        yield from sdf.cli(["run", "--save", "info-schema"], context=context).stream()

    @op(out=Out(Nothing))
    def my_sdf_op_yield_events_with_downstream(context: OpExecutionContext, sdf: SdfCliResource):
        yield from sdf.cli(["run", "--save", "info-schema"], context=context).stream()

    @op(ins={"depends_on": In(dagster_type=Nothing)})
    def my_downstream_op(): ...

    @job
    def my_sdf_job_yield_events():
        my_sdf_op_yield_events()
        my_downstream_op(depends_on=my_sdf_op_yield_events_with_downstream())

    result = my_sdf_job_yield_events.execute_in_process(resources={"sdf": sdf})
    assert result.success


def test_custom_subclass():
    CustomSdfCliResource = pydantic.create_model(
        "CustomSdfCliResource",
        __base__=SdfCliResource,
        custom_field=(str, ...),
    )
    custom = CustomSdfCliResource(
        workspace_dir=os.fspath(moms_flower_shop_path), custom_field="custom_value"
    )
    assert isinstance(custom, SdfCliResource)


def test_metadata(sdf: SdfCliResource) -> None:
    @op(out={})
    def my_sdf_op_yield_events(context: OpExecutionContext, sdf: SdfCliResource):
        yield from sdf.cli(["run", "--save", "info-schema"], context=context).stream()

    @job
    def my_sdf_job_yield_events():
        my_sdf_op_yield_events()

    result = my_sdf_job_yield_events.execute_in_process(resources={"sdf": sdf})
    assert result.success

    materialization_events = result.get_asset_materialization_events()
    assert len(materialization_events) == 12

    for event in materialization_events:
        metadata = event.materialization.metadata
        assert metadata[DAGSTER_SDF_TABLE_ID]
        assert metadata[DAGSTER_SDF_CATALOG_NAME]
        assert metadata[DAGSTER_SDF_SCHEMA_NAME]
        assert metadata[DAGSTER_SDF_TABLE_NAME]
        assert metadata[DAGSTER_SDF_PURPOSE]
        assert metadata[DAGSTER_SDF_DIALECT]
        assert metadata["Execution Duration"]
        assert metadata["Materialized From Cache"] is not None
