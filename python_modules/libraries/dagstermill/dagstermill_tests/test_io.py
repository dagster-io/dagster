import os

import pytest
from dagster import FileHandle, pipeline
from dagster.core.errors import DagsterInvalidDefinitionError
from dagstermill.examples.repository import hello_world

from .test_solids import exec_for_test


@pytest.mark.notebook_test
def test_yes_output_notebook_yes_file_manager():
    # when output_notebook is set and file_manager is provided:
    # * persist the output notebook in a temp file
    # * yield AssetMaterialization
    # * yield Output(value=FileHandle(...), name=output_notebook)
    with exec_for_test("hello_world_with_output_notebook_pipeline") as result:
        assert result.success
        materializations = [
            x for x in result.event_list if x.event_type_value == "ASSET_MATERIALIZATION"
        ]
        assert len(materializations) == 1

        assert result.result_for_solid("hello_world").success
        assert "notebook" in result.result_for_solid("hello_world").output_values
        assert isinstance(
            result.result_for_solid("hello_world").output_values["notebook"], FileHandle
        )

        assert os.path.exists(
            result.result_for_solid("hello_world").output_values["notebook"].path_desc
        )
        assert (
            materializations[0]
            .event_specific_data.materialization.metadata_entries[0]
            .entry_data.path
            == result.result_for_solid("hello_world").output_values["notebook"].path_desc
        )

        assert result.result_for_solid("load_notebook").success
        assert result.result_for_solid("load_notebook").output_value() is True


def test_yes_output_notebook_no_file_manager():
    with pytest.raises(
        DagsterInvalidDefinitionError, match='Resource key "file_manager" is required'
    ):

        @pipeline
        def _pipe():
            hello_world()


@pytest.mark.notebook_test
def test_no_output_notebook_yes_file_manager():
    # when output_notebook is not set and file_manager is not provided:
    # * persist output notebook (but no solid output)
    # * yield AssetMaterialization
    with exec_for_test("hello_world_no_output_notebook_pipeline") as result:
        assert result.success
        materializations = [
            x for x in result.event_list if x.event_type_value == "ASSET_MATERIALIZATION"
        ]
        assert len(materializations) == 1
        assert os.path.exists(
            materializations[0]
            .event_specific_data.materialization.metadata_entries[0]
            .entry_data.path
        )

        assert result.result_for_solid("hello_world_no_output_notebook").success
        assert not result.result_for_solid("hello_world_no_output_notebook").output_values


@pytest.mark.notebook_test
def test_no_output_notebook_no_file_manager():
    # when output_notebook is not set and file_manager is not provided:
    # * throw warning and persisting fails
    # * yield AssetMaterialization - FIXME: shouldn't yield AssetMaterialization when persisting fails
    with exec_for_test("hello_world_no_output_notebook_no_file_manager_pipeline") as result:
        assert result.success
        materializations = [
            x for x in result.event_list if x.event_type_value == "ASSET_MATERIALIZATION"
        ]
        assert len(materializations) == 1
        assert not os.path.exists(
            materializations[0]
            .event_specific_data.materialization.metadata_entries[0]
            .entry_data.path
        )

        assert result.result_for_solid("hello_world_no_output_notebook_no_file_manager").success
        assert not result.result_for_solid(
            "hello_world_no_output_notebook_no_file_manager"
        ).output_values
