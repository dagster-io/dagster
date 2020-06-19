import string

from dagster.api.snapshot_partition import (
    sync_get_external_partition,
    sync_get_external_partition_names,
)
from dagster.core.host_representation import (
    ExternalPartitionData,
    ExternalPartitionExecutionErrorData,
    ExternalPartitionNamesData,
)

from .utils import get_bar_repo_handle


def test_external_partitions_api():
    repository_handle = get_bar_repo_handle()
    partition_data = sync_get_external_partition(repository_handle, 'baz_partitions', 'c')
    assert isinstance(partition_data, ExternalPartitionData)
    assert partition_data.run_config
    assert partition_data.run_config['solids']['do_input']['inputs']['x']['value'] == 'c'


def test_external_partition_names_api():
    repository_handle = get_bar_repo_handle()
    data = sync_get_external_partition_names(repository_handle, 'baz_partitions')
    assert isinstance(data, ExternalPartitionNamesData)
    assert data.partition_names == list(string.ascii_lowercase)


def test_external_partition_names_api_error():
    repository_handle = get_bar_repo_handle()
    data = sync_get_external_partition_names(repository_handle, 'error_partitions')
    assert isinstance(data, ExternalPartitionExecutionErrorData)
    assert 'womp womp' in data.error.to_string()
