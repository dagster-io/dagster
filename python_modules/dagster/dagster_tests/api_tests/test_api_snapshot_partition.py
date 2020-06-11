from dagster.api.snapshot_partition import sync_get_external_partition
from dagster.core.host_representation import ExternalPartitionData

from .utils import get_bar_repo_handle


def test_external_partitions_api():
    repository_handle = get_bar_repo_handle()
    partition_data = sync_get_external_partition(repository_handle, 'baz_partitions', 'c')
    assert isinstance(partition_data, ExternalPartitionData)
    assert partition_data.run_config
    assert partition_data.run_config['solids']['do_input']['inputs']['x']['value'] == 'c'
