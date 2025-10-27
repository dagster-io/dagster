import os
import sys
from contextlib import contextmanager

import dagster as dg
from dagster._core.remote_origin import ManagedGrpcPythonEnvCodeLocationOrigin
from dagster._core.remote_representation.handle import JobHandle
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.load_target import PythonFileTarget


@dg.op
def do_something():
    pass


@dg.op
def do_something_else():
    pass


@dg.job
def foo():
    do_something()
    do_something_else()


class MyConfig(dg.Config):
    my_field: str


@dg.asset
def my_asset(config: MyConfig) -> None: ...


@dg.asset_check(asset=my_asset)
def my_failing_check() -> dg.AssetCheckResult:
    raise Exception("FAILS")


@dg.repository
def bar_repo():
    return [foo, my_asset, my_failing_check]


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
