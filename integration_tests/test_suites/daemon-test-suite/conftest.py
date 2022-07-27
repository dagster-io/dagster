import os

import pytest

from dagster import file_relative_path
from dagster._core.test_utils import instance_for_test
from dagster._core.workspace import WorkspaceProcessContext
from dagster._core.workspace.load_target import PythonFileTarget


@pytest.fixture(name="instance")
def instance_fixture():
    with instance_for_test(
        overrides={
            "run_coordinator": {
                "module": "dagster.core.run_coordinator",
                "class": "QueuedRunCoordinator",
                "config": {"dequeue_interval_seconds": 1},
            },
        }
    ) as instance:
        yield instance


@pytest.fixture(name="foo_example_workspace")
def foo_example_workspace_fixture(instance):
    with WorkspaceProcessContext(
        instance,
        PythonFileTarget(
            python_file=file_relative_path(__file__, "repo.py"),
            attribute=None,
            working_directory=os.path.dirname(__file__),
            location_name=None,
        ),
    ) as workspace_process_context:
        yield workspace_process_context.create_request_context()


@pytest.fixture
def foo_example_repo(foo_example_workspace):
    return foo_example_workspace.repository_locations[0].get_repository("example_repo")
