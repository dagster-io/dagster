import string

from dagster.api.snapshot_partition import (
    sync_get_external_partition_config,
    sync_get_external_partition_config_grpc,
    sync_get_external_partition_names,
    sync_get_external_partition_names_grpc,
    sync_get_external_partition_tags,
    sync_get_external_partition_tags_grpc,
)
from dagster.core.host_representation import (
    ExternalPartitionConfigData,
    ExternalPartitionExecutionErrorData,
    ExternalPartitionNamesData,
    ExternalPartitionTagsData,
)

from .utils import get_bar_grpc_repo_handle, get_bar_repo_handle


def test_external_partition_names():
    repository_handle = get_bar_repo_handle()
    data = sync_get_external_partition_names(repository_handle, 'baz_partitions')
    assert isinstance(data, ExternalPartitionNamesData)
    assert data.partition_names == list(string.ascii_lowercase)


def test_external_partition_names_error():
    repository_handle = get_bar_repo_handle()
    error = sync_get_external_partition_names(repository_handle, 'error_partitions')
    assert isinstance(error, ExternalPartitionExecutionErrorData)
    assert 'womp womp' in error.error.to_string()


def test_external_partition_names_grpc():
    repository_handle = get_bar_grpc_repo_handle()
    data = sync_get_external_partition_names_grpc(
        repository_handle.repository_location_handle.client, repository_handle, 'baz_partitions'
    )
    assert isinstance(data, ExternalPartitionNamesData)
    assert data.partition_names == list(string.ascii_lowercase)


def test_external_partition_names_error_grpc():
    repository_handle = get_bar_grpc_repo_handle()

    error = sync_get_external_partition_names_grpc(
        repository_handle.repository_location_handle.client, repository_handle, 'error_partitions'
    )
    assert isinstance(error, ExternalPartitionExecutionErrorData)
    assert 'womp womp' in error.error.to_string()


def test_external_partitions_config():
    repository_handle = get_bar_repo_handle()
    data = sync_get_external_partition_config(repository_handle, 'baz_partitions', 'c')
    assert isinstance(data, ExternalPartitionConfigData)
    assert data.run_config
    assert data.run_config['solids']['do_input']['inputs']['x']['value'] == 'c'


def test_external_partitions_config_error():
    repository_handle = get_bar_repo_handle()
    error = sync_get_external_partition_config(repository_handle, 'error_partition_config', 'c')
    assert isinstance(error, ExternalPartitionExecutionErrorData)


def test_external_partitions_config_grpc():
    repository_handle = get_bar_grpc_repo_handle()
    data = sync_get_external_partition_config_grpc(
        repository_handle.repository_location_handle.client,
        repository_handle,
        'baz_partitions',
        'c',
    )
    assert isinstance(data, ExternalPartitionConfigData)
    assert data.run_config
    assert data.run_config['solids']['do_input']['inputs']['x']['value'] == 'c'


def test_external_partitions_config_error_grpc():
    repository_handle = get_bar_grpc_repo_handle()
    error = sync_get_external_partition_config_grpc(
        repository_handle.repository_location_handle.client,
        repository_handle,
        'error_partition_config',
        'c',
    )
    assert isinstance(error, ExternalPartitionExecutionErrorData)


def test_external_partitions_tags():
    repository_handle = get_bar_repo_handle()
    data = sync_get_external_partition_tags(repository_handle, 'baz_partitions', 'c')
    assert isinstance(data, ExternalPartitionTagsData)
    assert data.tags
    assert data.tags['foo'] == 'bar'


def test_external_partitions_tags_error():
    repository_handle = get_bar_repo_handle()
    error = sync_get_external_partition_tags(repository_handle, 'error_partition_tags', 'c')
    assert isinstance(error, ExternalPartitionExecutionErrorData)


def test_external_partitions_tags_grpc():
    repository_handle = get_bar_grpc_repo_handle()
    data = sync_get_external_partition_tags_grpc(
        repository_handle.repository_location_handle.client,
        repository_handle,
        'baz_partitions',
        'c',
    )
    assert isinstance(data, ExternalPartitionTagsData)
    assert data.tags
    assert data.tags['foo'] == 'bar'


def test_external_partitions_tags_error_grpc():
    repository_handle = get_bar_grpc_repo_handle()
    error = sync_get_external_partition_tags_grpc(
        repository_handle.repository_location_handle.client,
        repository_handle,
        'error_partition_tags',
        'c',
    )
    assert isinstance(error, ExternalPartitionExecutionErrorData)
