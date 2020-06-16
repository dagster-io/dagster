from dagster import file_relative_path
from dagster.core.code_pointer import FileCodePointer
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.host_representation.handle import PipelineHandle, RepositoryLocationHandle
from dagster.core.host_representation.repository_location import (
    InProcessRepositoryLocation,
    PythonEnvRepositoryLocation,
)


def get_bar_repo_repository_location_handle():
    return RepositoryLocationHandle.create_out_of_process_location(
        location_name='bar_repo_location',
        repository_code_pointer_dict={
            'bar_repo': FileCodePointer(
                file_relative_path(__file__, 'api_tests_repo.py'), 'bar_repo'
            )
        },
    )


def get_bar_repo_handle():
    return (
        PythonEnvRepositoryLocation(get_bar_repo_repository_location_handle())
        .get_repository('bar_repo')
        .handle
    )


def get_foo_pipeline_handle():
    return PipelineHandle('foo', get_bar_repo_handle())


def legacy_get_bar_repo_handle():
    recon_repo = ReconstructableRepository.from_legacy_repository_yaml(
        file_relative_path(__file__, 'repository_file.yaml')
    )
    return InProcessRepositoryLocation(recon_repo).get_repository('bar_repo').handle


def legacy_get_foo_pipeline_handle():
    return PipelineHandle('foo', legacy_get_bar_repo_handle())
