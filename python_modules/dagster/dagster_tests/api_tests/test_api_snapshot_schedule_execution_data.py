from dagster import seven
from dagster.api.snapshot_schedule import sync_get_external_schedule_execution_data
from dagster.core.host_representation.external_data import ExternalScheduleExecutionData
from dagster.core.instance import DagsterInstance

from .utils import get_bar_repo_handle


def test_external_partitions_api():
    repository_handle = get_bar_repo_handle()
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        execution_data = sync_get_external_schedule_execution_data(
            instance, repository_handle, 'foo_schedule'
        )
        assert isinstance(execution_data, ExternalScheduleExecutionData)
        assert execution_data.run_config is not None
