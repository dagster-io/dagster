import dagster as dg
import pytest
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._core.workspace.load_target import PythonFileTarget


@pytest.fixture(scope="module")
def instance():
    with dg.instance_for_test() as the_instance:
        yield the_instance


@pytest.fixture(scope="module")
def workspace(instance):
    with WorkspaceProcessContext(
        instance,
        PythonFileTarget(
            python_file=dg.file_relative_path(__file__, "test_default_run_launcher.py"),
            attribute="nope",
            working_directory=None,
            location_name="test",
        ),
    ) as workspace_process_context:
        yield workspace_process_context.create_request_context()


@pytest.fixture(scope="module")
def pending_workspace(instance):
    with WorkspaceProcessContext(
        instance,
        PythonFileTarget(
            python_file=dg.file_relative_path(__file__, "pending_repository.py"),
            attribute="pending",
            working_directory=None,
            location_name="test2",
        ),
    ) as workspace_process_context:
        yield workspace_process_context.create_request_context()
