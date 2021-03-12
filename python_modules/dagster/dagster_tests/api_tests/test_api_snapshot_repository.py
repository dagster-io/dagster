import sys
from contextlib import contextmanager

from dagster import lambda_solid, pipeline, repository
from dagster.api.snapshot_repository import sync_get_streaming_external_repositories_data_grpc
from dagster.core.host_representation import (
    ExternalRepositoryData,
    ManagedGrpcPythonEnvRepositoryLocationOrigin,
)
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin

from .utils import get_bar_repo_grpc_repository_location_handle


def test_streaming_external_repositories_api_grpc():
    with get_bar_repo_grpc_repository_location_handle() as repository_location_handle:
        external_repo_datas = sync_get_streaming_external_repositories_data_grpc(
            repository_location_handle.client, repository_location_handle
        )

        assert len(external_repo_datas) == 1

        external_repository_data = external_repo_datas["bar_repo"]

        assert isinstance(external_repository_data, ExternalRepositoryData)
        assert external_repository_data.name == "bar_repo"


@lambda_solid
def do_something():
    return 1


@pipeline
def giant_pipeline():
    # Pipeline big enough to be larger than the max size limit for a gRPC message in its
    # external repository
    for _i in range(20000):
        do_something()


@repository
def giant_repo():
    return {
        "pipelines": {
            "giant": giant_pipeline,
        },
    }


@contextmanager
def get_giant_repo_grpc_repository_location_handle():
    with ManagedGrpcPythonEnvRepositoryLocationOrigin(
        loadable_target_origin=LoadableTargetOrigin(
            executable_path=sys.executable,
            attribute="giant_repo",
            module_name="dagster_tests.api_tests.test_api_snapshot_repository",
        ),
        location_name="giant_repo_location",
    ).create_handle() as handle:
        yield handle


def test_giant_external_repository_streaming_grpc():
    with get_giant_repo_grpc_repository_location_handle() as repository_location_handle:
        # Using streaming allows the giant repo to load
        external_repos_data = sync_get_streaming_external_repositories_data_grpc(
            repository_location_handle.client, repository_location_handle
        )

        assert len(external_repos_data) == 1

        external_repository_data = external_repos_data["giant_repo"]

        assert isinstance(external_repository_data, ExternalRepositoryData)
        assert external_repository_data.name == "giant_repo"
