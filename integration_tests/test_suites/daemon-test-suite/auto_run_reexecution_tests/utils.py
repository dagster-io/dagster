import os
import sys
from contextlib import contextmanager

from dagster import job, op, repository
from dagster._core.remote_representation import JobHandle, ManagedGrpcPythonEnvCodeLocationOrigin
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.load_target import PythonFileTarget


@op
def do_something():
    pass


@op
def do_something_else():
    pass


@job
def foo():
    do_something()
    do_something_else()


@repository
def bar_repo():
    return [foo]


@contextmanager
def get_bar_repo_code_location(instance):
    loadable_target_origin = LoadableTargetOrigin(
        executable_path=sys.executable,
        python_file=__file__,
        attribute="bar_repo",
    )
    location_name = "cloud_daemon_test_location"

    origin = ManagedGrpcPythonEnvCodeLocationOrigin(loadable_target_origin, location_name)

    with origin.create_single_location(instance) as location:
        yield location


@contextmanager
def get_bar_repo_handle(instance):
    with get_bar_repo_code_location(instance) as location:
        yield location.get_repository("bar_repo").handle


@contextmanager
def get_foo_job_handle(instance):
    with get_bar_repo_handle(instance) as repo_handle:
        yield JobHandle("foo", repo_handle)


def workspace_load_target():
    return PythonFileTarget(
        python_file=__file__,
        attribute=None,
        working_directory=os.path.dirname(__file__),
        location_name="cloud_daemon_test_location",
    )
