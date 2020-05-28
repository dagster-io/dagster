from dagster import file_relative_path
from dagster.api.snapshot_repository import sync_get_external_repository
from dagster.core.code_pointer import FileCodePointer
from dagster.core.host_representation import ExternalRepository, LocationHandle


def test_repository_snapshot_api():
    location_handle = LocationHandle(
        'test', FileCodePointer(file_relative_path(__file__, 'api_tests_repo.py'), 'bar_repo'),
    )
    external_repository = sync_get_external_repository(location_handle)

    assert isinstance(external_repository, ExternalRepository)
    assert external_repository.name == 'bar'
