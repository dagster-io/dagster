import sys
from contextlib import ExitStack, contextmanager
from typing import Iterator, Optional

from dagster import file_relative_path
from dagster._core.host_representation import (
    JobHandle,
    ManagedGrpcPythonEnvCodeLocationOrigin,
)
from dagster._core.host_representation.code_location import GrpcServerCodeLocation
from dagster._core.host_representation.handle import RepositoryHandle
from dagster._core.instance import DagsterInstance
from dagster._core.test_utils import instance_for_test
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.context import WorkspaceProcessContext, WorkspaceRequestContext
from dagster._core.workspace.load_target import PythonFileTarget


@contextmanager
def get_bar_workspace(instance: DagsterInstance) -> Iterator[WorkspaceRequestContext]:
    with WorkspaceProcessContext(
        instance,
        PythonFileTarget(
            python_file=file_relative_path(__file__, "api_tests_repo.py"),
            attribute="bar_repo",
            working_directory=None,
            location_name="bar_code_location",
        ),
    ) as workspace_process_context:
        yield workspace_process_context.create_request_context()


@contextmanager
def get_bar_repo_code_location(
    instance: Optional[DagsterInstance] = None,
) -> Iterator[GrpcServerCodeLocation]:
    with ExitStack() as stack:
        if not instance:
            instance = stack.enter_context(instance_for_test())

        loadable_target_origin = LoadableTargetOrigin(
            executable_path=sys.executable,
            python_file=file_relative_path(__file__, "api_tests_repo.py"),
            attribute="bar_repo",
        )
        location_name = "bar_code_location"

        origin = ManagedGrpcPythonEnvCodeLocationOrigin(loadable_target_origin, location_name)

        with origin.create_single_location(instance) as location:
            yield location


@contextmanager
def get_bar_repo_handle(instance: Optional[DagsterInstance] = None) -> Iterator[RepositoryHandle]:
    with ExitStack() as stack:
        if not instance:
            instance = stack.enter_context(instance_for_test())

        with get_bar_repo_code_location(instance) as location:
            yield location.get_repository("bar_repo").handle


@contextmanager
def get_foo_job_handle(instance: Optional[DagsterInstance] = None) -> Iterator[JobHandle]:
    with ExitStack() as stack:
        if not instance:
            instance = stack.enter_context(instance_for_test())

        with get_bar_repo_handle(instance) as repo_handle:
            yield JobHandle("foo", repo_handle)
