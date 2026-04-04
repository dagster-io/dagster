import os

import pytest
from dagster import build_input_context, build_output_context, job, repository
from dagster._core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from dagstermill.examples.repository import hello_world
from dagstermill.io_managers import LocalOutputNotebookIOManager
from dagstermill.test_utils import exec_for_test


def test_yes_output_notebook_no_file_manager():
    with pytest.raises(DagsterInvalidDefinitionError):

        @job
        def _job():
            hello_world()

        @repository
        def _repo():
            return [_job]


@pytest.mark.notebook_test
def test_no_output_notebook_yes_file_manager():
    # when output_notebook is not set and file_manager is provided:
    # * persist output notebook (but no op output)
    with exec_for_test("hello_world_no_output_notebook_job") as result:
        assert result.success
        materializations = [
            x for x in result.all_events if x.event_type_value == "ASSET_MATERIALIZATION"
        ]
        assert len(materializations) == 0

        with pytest.raises(DagsterInvariantViolationError, match="Did not find result"):
            result.output_for_node("hello_world_no_output_notebook")


@pytest.mark.notebook_test
def test_no_output_notebook_no_file_manager():
    # when output_notebook is not set and file_manager is not provided:
    # * throw warning and persisting fails
    with exec_for_test("hello_world_no_output_notebook_no_file_manager_job") as result:
        assert result.success
        materializations = [
            x for x in result.all_events if x.event_type_value == "ASSET_MATERIALIZATION"
        ]
        assert len(materializations) == 0

        with pytest.raises(DagsterInvariantViolationError, match="Did not find result"):
            result.output_for_node("hello_world_no_output_notebook")


@pytest.mark.notebook_test
def test_yes_output_notebook_yes_io_manager():
    # when output_notebook is set and io manager is provided:
    # * persist the output notebook via notebook_io_manager
    # * yield AssetMaterialization
    # * yield Output(value=bytes, name=output_notebook)
    with exec_for_test("hello_world_with_output_notebook_job") as result:
        assert result.success
        materializations = [
            x for x in result.all_events if x.event_type_value == "ASSET_MATERIALIZATION"
        ]
        assert len(materializations) == 1

        assert result.output_for_node("hello_world", "notebook")

        output_path = (
            materializations[0]
            .event_specific_data.materialization.metadata["Executed notebook"]  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
            .path
        )
        assert os.path.exists(output_path)  # pyright: ignore[reportArgumentType]

        with open(output_path, "rb") as f:  # pyright: ignore[reportCallIssue,reportArgumentType]
            assert f.read() == result.output_for_node("load_notebook")


def test_local_output_notebook_io_manager_supports_html_artifacts(tmp_path):
    manager = LocalOutputNotebookIOManager(base_dir=str(tmp_path))
    html_bytes = b"<html><body><h1>hello</h1></body></html>"

    with build_output_context(
        asset_key=["hello_world_html_asset"],
        output_metadata={"dagstermill/serialized_artifact_type": "html"},
    ) as context:
        manager.handle_output(context, html_bytes)
        output_path = context.get_logged_metadata()["Rendered notebook"].path

    assert output_path.endswith(".html")
    assert os.path.exists(output_path)

    with open(output_path, "rb") as f:
        assert f.read() == html_bytes

    input_context = build_input_context(upstream_output=context)
    assert manager.load_input(input_context) == html_bytes
