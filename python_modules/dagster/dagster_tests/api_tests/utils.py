import sys

from dagster import file_relative_path
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.host_representation.handle import PipelineHandle, RepositoryLocationHandle
from dagster.core.host_representation.repository_location import (
    GrpcServerRepositoryLocation,
    InProcessRepositoryLocation,
    PythonEnvRepositoryLocation,
)
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin


def get_bar_repo_repository_location_handle():
    return RepositoryLocationHandle.create_python_env_location(
        loadable_target_origin=LoadableTargetOrigin(
            executable_path=sys.executable,
            python_file=file_relative_path(__file__, 'api_tests_repo.py'),
            attribute='bar_repo',
        ),
        location_name='bar_repo_location',
    )


def get_bar_repo_grpc_repository_location_handle():
    return RepositoryLocationHandle.create_process_bound_grpc_server_location(
        loadable_target_origin=LoadableTargetOrigin(
            attribute='bar_repo', python_file=file_relative_path(__file__, 'api_tests_repo.py'),
        ),
        location_name='bar_repo',
    )


def get_bar_repo_handle():
    return (
        PythonEnvRepositoryLocation(get_bar_repo_repository_location_handle())
        .get_repository('bar_repo')
        .handle
    )


def get_bar_grpc_repo_handle():
    return (
        GrpcServerRepositoryLocation(get_bar_repo_grpc_repository_location_handle())
        .get_repository('bar_repo')
        .handle
    )


def get_foo_pipeline_handle():
    return PipelineHandle('foo', get_bar_repo_handle())


def get_foo_grpc_pipeline_handle():
    return PipelineHandle('foo', get_bar_grpc_repo_handle())


def legacy_get_bar_repo_handle():
    recon_repo = ReconstructableRepository.from_legacy_repository_yaml(
        file_relative_path(__file__, 'repository_file.yaml')
    )
    return InProcessRepositoryLocation(recon_repo).get_repository('bar_repo').handle


def legacy_get_foo_pipeline_handle():
    return PipelineHandle('foo', legacy_get_bar_repo_handle())
