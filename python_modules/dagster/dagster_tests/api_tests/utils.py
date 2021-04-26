import sys
from contextlib import contextmanager

from dagster import file_relative_path
from dagster.core.host_representation import (
    ManagedGrpcPythonEnvRepositoryLocationOrigin,
    PipelineHandle,
)
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin


@contextmanager
def get_bar_repo_repository_location():
    loadable_target_origin = LoadableTargetOrigin(
        executable_path=sys.executable,
        python_file=file_relative_path(__file__, "api_tests_repo.py"),
        attribute="bar_repo",
    )
    location_name = "bar_repo_location"

    origin = ManagedGrpcPythonEnvRepositoryLocationOrigin(loadable_target_origin, location_name)

    with origin.create_test_location() as location:
        yield location


@contextmanager
def get_bar_repo_handle():
    with get_bar_repo_repository_location() as location:
        yield location.get_repository("bar_repo").handle


@contextmanager
def get_foo_pipeline_handle():
    with get_bar_repo_handle() as repo_handle:
        yield PipelineHandle("foo", repo_handle)


@contextmanager
def get_foo_external_pipeline():
    with get_bar_repo_repository_location() as location:
        yield location.get_repository("bar_repo").get_full_external_pipeline("foo")
