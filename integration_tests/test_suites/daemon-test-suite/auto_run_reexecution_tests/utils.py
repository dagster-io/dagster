import os
import sys
from contextlib import contextmanager

from dagster import job, op, repository
from dagster._core.host_representation import (
    ManagedGrpcPythonEnvRepositoryLocationOrigin,
    PipelineHandle,
)
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.load_target import PythonFileTarget


@op
def do_something():
    pass


@job
def foo():
    do_something()


@repository
def bar_repo():
    return [foo]


@contextmanager
def get_bar_repo_repository_location(instance):
    loadable_target_origin = LoadableTargetOrigin(
        executable_path=sys.executable,
        python_file=__file__,
        attribute="bar_repo",
    )
    location_name = "cloud_daemon_test_location"

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


def workspace_load_target():
    return PythonFileTarget(
        python_file=__file__,
        attribute=None,
        working_directory=os.path.dirname(__file__),
        location_name="cloud_daemon_test_location",
    )
