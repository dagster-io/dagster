from dagster import file_relative_path
from dagster.api.snapshot_repository import sync_get_external_repositories
from dagster.core.code_pointer import FileCodePointer
from dagster.core.host_representation import ExternalRepository, RepositoryLocationHandle


def test_external_repositories_api():
    repository_location_handle = RepositoryLocationHandle.create_out_of_process_location(
        location_name='bare_repo_location',
        repository_code_pointer_dict={
            'bar_repo': FileCodePointer(
                file_relative_path(__file__, 'api_tests_repo.py'), 'bar_repo'
            )
        },
    )
    external_repos = sync_get_external_repositories(repository_location_handle)

    assert len(external_repos) == 1

    external_repository = external_repos[0]

    assert isinstance(external_repository, ExternalRepository)
    assert external_repository.name == 'bar_repo'
