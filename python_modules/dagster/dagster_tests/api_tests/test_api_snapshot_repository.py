from dagster.api.snapshot_repository import (
    sync_get_external_repositories,
    sync_get_external_repositories_grpc,
)
from dagster.core.host_representation import ExternalRepository

from .utils import (
    get_bar_repo_grpc_repository_location_handle,
    get_bar_repo_repository_location_handle,
)


def test_external_repositories_api():
    repository_location_handle = get_bar_repo_repository_location_handle()
    external_repos = sync_get_external_repositories(repository_location_handle)

    assert len(external_repos) == 1

    external_repository = external_repos[0]

    assert isinstance(external_repository, ExternalRepository)
    assert external_repository.name == "bar_repo"


def test_external_repositories_api_grpc():
    with get_bar_repo_grpc_repository_location_handle() as repository_location_handle:
        external_repos = sync_get_external_repositories_grpc(
            repository_location_handle.client, repository_location_handle
        )

        assert len(external_repos) == 1

        external_repository = external_repos[0]

        assert isinstance(external_repository, ExternalRepository)
        assert external_repository.name == "bar_repo"
