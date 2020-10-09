import sys
from contextlib import contextmanager

from dagster import file_relative_path
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.host_representation.handle import (
    PipelineHandle,
    RepositoryLocationHandle,
    UserProcessApi,
)
from dagster.core.host_representation.repository_location import (
    GrpcServerRepositoryLocation,
    InProcessRepositoryLocation,
    RepositoryLocation,
)
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin


def get_bar_repo_repository_location_handle(user_process_api=UserProcessApi.CLI):
    return RepositoryLocationHandle.create_python_env_location(
        loadable_target_origin=LoadableTargetOrigin(
            executable_path=sys.executable,
            python_file=file_relative_path(__file__, "api_tests_repo.py"),
            attribute="bar_repo",
        ),
        location_name="bar_repo_location",
        user_process_api=user_process_api,
    )


@contextmanager
def get_bar_repo_grpc_repository_location_handle():
    handle = RepositoryLocationHandle.create_process_bound_grpc_server_location(
        loadable_target_origin=LoadableTargetOrigin(
            attribute="bar_repo", python_file=file_relative_path(__file__, "api_tests_repo.py"),
        ),
        location_name="bar_repo",
    )
    try:
        yield handle
    finally:
        handle.cleanup()


def get_bar_repo_handle():
    return (
        RepositoryLocation.from_handle(get_bar_repo_repository_location_handle(UserProcessApi.CLI))
        .get_repository("bar_repo")
        .handle
    )


@contextmanager
def get_bar_grpc_repo_handle():
    with get_bar_repo_grpc_repository_location_handle() as handle:
        yield GrpcServerRepositoryLocation(handle).get_repository("bar_repo").handle


def get_foo_pipeline_handle():
    return PipelineHandle("foo", get_bar_repo_handle())


@contextmanager
def get_foo_grpc_pipeline_handle():
    with get_bar_grpc_repo_handle() as repo_handle:
        yield PipelineHandle("foo", repo_handle)


def legacy_get_bar_repo_handle():
    recon_repo = ReconstructableRepository.from_legacy_repository_yaml(
        file_relative_path(__file__, "legacy_repository_file.yaml")
    )
    return InProcessRepositoryLocation(recon_repo).get_repository("bar_repo").handle


def legacy_get_foo_pipeline_handle():
    return PipelineHandle("foo", legacy_get_bar_repo_handle())
