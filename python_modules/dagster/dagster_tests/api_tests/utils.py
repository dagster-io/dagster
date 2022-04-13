import sys
from contextlib import contextmanager

from dagster import file_relative_path
from dagster.core.host_representation import (
    ManagedGrpcPythonEnvRepositoryLocationOrigin,
    PipelineHandle,
)
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.core.workspace.context import WorkspaceProcessContext
from dagster.core.workspace.load_target import PythonFileTarget


@contextmanager
def get_bar_workspace(instance):
    with WorkspaceProcessContext(
        instance,
        PythonFileTarget(
            python_file=file_relative_path(__file__, "api_tests_repo.py"),
            attribute="bar_repo",
            working_directory=None,
            location_name="bar_repo_location",
        ),
    ) as workspace_process_context:
        yield workspace_process_context.create_request_context()


@contextmanager
def get_bar_repo_repository_location(instance):
    loadable_target_origin = LoadableTargetOrigin(
        executable_path=sys.executable,
        python_file=file_relative_path(__file__, "api_tests_repo.py"),
        attribute="bar_repo",
    )
    location_name = "bar_repo_location"

    origin = ManagedGrpcPythonEnvRepositoryLocationOrigin(loadable_target_origin, location_name)

    with origin.create_single_location(instance) as location:
        yield location


@contextmanager
def get_bar_repo_handle(instance):
    with get_bar_repo_repository_location(instance) as location:
        yield location.get_repository("bar_repo").handle


@contextmanager
def get_foo_pipeline_handle(instance):
    with get_bar_repo_handle(instance) as repo_handle:
        yield PipelineHandle("foo", repo_handle)
