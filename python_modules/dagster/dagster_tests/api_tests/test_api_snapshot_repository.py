from dagster import file_relative_path
from dagster.api.snapshot_repository import sync_get_external_repository
from dagster.core.host_representation import EnvironmentHandle, ExternalRepository, RepositoryHandle


def test_repository_snapshot_api():
    repo_handle = RepositoryHandle(
        repository_name='bar',
        environment_handle=EnvironmentHandle.legacy_from_yaml(
            'test', file_relative_path(__file__, 'repository_file.yaml')
        ),
    )

    external_repository = sync_get_external_repository(repo_handle)

    assert isinstance(external_repository, ExternalRepository)
    assert external_repository.name == 'bar'
