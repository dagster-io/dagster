import sys
from contextlib import contextmanager

import pytest
from dagster import file_relative_path
from dagster.core.host_representation import (
    ManagedGrpcPythonEnvRepositoryLocationOrigin,
    PipelineHandle,
    RepositoryLocation,
    RepositoryLocationHandle,
)
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin


def get_example_repository_location_handle():
    loadable_target_origin = LoadableTargetOrigin(
        executable_path=sys.executable,
        python_file=file_relative_path(__file__, "repo.py"),
    )
    location_name = "example_repo_location"

    origin = ManagedGrpcPythonEnvRepositoryLocationOrigin(loadable_target_origin, location_name)

    return RepositoryLocationHandle.create_from_repository_location_origin(origin)


@contextmanager
def get_example_repo_handle():
    with get_example_repository_location_handle() as location_handle:
        yield RepositoryLocation.from_handle(location_handle).get_repository("example_repo").handle


@pytest.fixture
def foo_pipeline_handle():
    with get_example_repo_handle() as repo_handle:
        yield PipelineHandle("foo_pipeline", repo_handle)
