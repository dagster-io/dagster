import os

import pytest
from dagstermill.examples.repository import hello_world

from dagster import FileHandle, pipeline
from dagster.core.errors import DagsterInvalidDefinitionError

from .test_solids import exec_for_test


@pytest.mark.notebook_test
def test_yes_output_notebook_yes_file_manager():
    # when output_notebook is set and file_manager is provided:
    # * persist the output notebook in a temp file
    # * yield AssetMaterialization
    # * yield Output(value=FileHandle(...), name=output_notebook)
    with exec_for_test("hello_world_with_output_notebook_pipeline_legacy") as result:
        assert result.success
        materializations = [
            x for x in result.event_list if x.event_type_value == "ASSET_MATERIALIZATION"
        ]
        assert len(materializations) == 1

        assert result.result_for_solid("hello_world_legacy").success
        assert "notebook" in result.result_for_solid("hello_world_legacy").output_values
        assert isinstance(
            result.result_for_solid("hello_world_legacy").output_values["notebook"], FileHandle
        )

        assert os.path.exists(
            result.result_for_solid("hello_world_legacy").output_values["notebook"].path_desc
        )
        assert (
            materializations[0]
            .event_specific_data.materialization.metadata_entries[0]
            .entry_data.path
            == result.result_for_solid("hello_world_legacy").output_values["notebook"].path_desc
        )

        assert result.result_for_solid("load_notebook_legacy").success
        assert result.result_for_solid("load_notebook_legacy").output_value() is True


def test_yes_output_notebook_no_file_manager():
    with pytest.raises(DagsterInvalidDefinitionError):

        @pipeline
        def _pipe():
            hello_world()


@pytest.mark.notebook_test
def test_no_output_notebook_yes_file_manager():
    # when output_notebook is not set and file_manager is provided:
    # * persist output notebook (but no solid output)
    with exec_for_test("hello_world_no_output_notebook_pipeline") as result:
        assert result.success
        materializations = [
            x for x in result.event_list if x.event_type_value == "ASSET_MATERIALIZATION"
        ]
        assert len(materializations) == 0

        assert result.result_for_solid("hello_world_no_output_notebook").success
        assert not result.result_for_solid("hello_world_no_output_notebook").output_values


@pytest.mark.notebook_test
def test_no_output_notebook_no_file_manager():
    # when output_notebook is not set and file_manager is not provided:
    # * throw warning and persisting fails
    with exec_for_test("hello_world_no_output_notebook_no_file_manager_pipeline") as result:
        assert result.success
        materializations = [
            x for x in result.event_list if x.event_type_value == "ASSET_MATERIALIZATION"
        ]
        assert len(materializations) == 0

        assert result.result_for_solid("hello_world_no_output_notebook_no_file_manager").success
        assert not result.result_for_solid(
            "hello_world_no_output_notebook_no_file_manager"
        ).output_values


@pytest.mark.notebook_test
def test_yes_output_notebook_yes_io_manager():
    # when output_notebook is set and io manager is provided:
    # * persist the output notebook via notebook_io_manager
    # * yield AssetMaterialization
    # * yield Output(value=bytes, name=output_notebook)
    with exec_for_test("hello_world_with_output_notebook_pipeline") as result:
        assert result.success
        materializations = [
            x for x in result.event_list if x.event_type_value == "ASSET_MATERIALIZATION"
        ]
        assert len(materializations) == 1

        assert result.result_for_solid("hello_world").success
        assert "notebook" in result.result_for_solid("hello_world").output_values

        output_path = (
            materializations[0]
            .event_specific_data.materialization.metadata_entries[0]
            .entry_data.path
        )
        assert os.path.exists(output_path)

        assert result.result_for_solid("load_notebook").success
        with open(output_path, "rb") as f:
            assert f.read() == result.result_for_solid("load_notebook").output_value()
