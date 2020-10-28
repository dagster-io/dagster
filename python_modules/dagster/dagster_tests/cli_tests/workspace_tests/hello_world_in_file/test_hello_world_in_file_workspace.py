import re

import pytest
from dagster.cli.workspace import Workspace
from dagster.cli.workspace.load import load_workspace_from_yaml_paths
from dagster.utils import file_relative_path


def get_hello_world_path():
    return file_relative_path(__file__, "hello_world_repository.py")


def test_load_in_process_location_handle_hello_world_nested_no_def():
    file_name = file_relative_path(__file__, "nested_python_file_workspace.yaml")
    with load_workspace_from_yaml_paths([file_name]) as workspace:
        assert isinstance(workspace, Workspace)
        assert len(workspace.repository_location_handles) == 1
        assert workspace.repository_location_handles[0].location_name == "hello_world_repository.py"


def test_load_in_process_location_handle_hello_world_nested_with_def():
    file_name = file_relative_path(__file__, "nested_with_def_python_file_workspace.yaml")
    with load_workspace_from_yaml_paths([file_name]) as workspace:
        assert isinstance(workspace, Workspace)
        assert len(workspace.repository_location_handles) == 1
        assert (
            workspace.repository_location_handles[0].location_name
            == "hello_world_repository.py:hello_world_repository"
        )


def test_load_in_process_location_handle_hello_world_terse():
    file_name = file_relative_path(__file__, "terse_python_file_workspace.yaml")

    with load_workspace_from_yaml_paths([file_name]) as workspace:
        assert isinstance(workspace, Workspace)
        assert len(workspace.repository_location_handles) == 1
        assert workspace.repository_location_handles[0].location_name == "hello_world_repository.py"


def test_load_legacy_repository_yaml():
    with pytest.warns(
        UserWarning,
        match=re.escape(
            "You are using the legacy repository yaml format. Please update your file "
            "to abide by the new workspace file format."
        ),
    ):
        with load_workspace_from_yaml_paths(
            [file_relative_path(__file__, "legacy_repository.yaml")],
        ) as workspace:
            assert isinstance(workspace, Workspace)
            assert len(workspace.repository_location_handles) == 1
