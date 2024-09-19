import os

import pytest
from dagster import job, repository
from dagster._core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from dagstermill.examples.repository import hello_world

from dagstermill_tests.test_ops import exec_for_test


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
            .event_specific_data.materialization.metadata["Executed notebook"]
            .path
        )
        assert os.path.exists(output_path)

        with open(output_path, "rb") as f:
            assert f.read() == result.output_for_node("load_notebook")
