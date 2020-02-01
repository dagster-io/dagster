import os
import sys

import mock
from dagster_graphql.test.utils import define_context_for_repository_yaml, execute_dagster_graphql

from dagster import ScheduleDefinition, seven
from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.scheduler import Schedule, ScheduleStatus, get_schedule_change_set
from dagster.core.storage.event_log import InMemoryEventLogStorage
from dagster.core.storage.local_compute_log_manager import NoOpComputeLogManager
from dagster.core.storage.root import LocalArtifactStorage
from dagster.core.storage.runs import InMemoryRunStorage
from dagster.core.storage.schedules import SqliteScheduleStorage
from dagster.utils import file_relative_path
from dagster.utils.test import FilesytemTestScheduler

GET_SCHEDULES_QUERY = '''
{
    scheduler {
      ... on Scheduler {
        runningSchedules {
          scheduleDefinition {
            name
            executionParamsString
            environmentConfigYaml
          }
          status
          pythonPath
          repositoryPath
        }
      }
    }
}
'''


def default_execution_params():
    return {
        "environmentConfigData": {"storage": {"filesystem": None}},
        "selector": {"name": "no_config_pipeline", "solidSubset": None},
        "mode": "default",
    }


@mock.patch.dict(os.environ, {"DAGSTER_HOME": "~/dagster"})
def test_get_all_schedules():

    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance(
            instance_type=InstanceType.EPHEMERAL,
            local_artifact_storage=LocalArtifactStorage(temp_dir),
            run_storage=InMemoryRunStorage(),
            event_storage=InMemoryEventLogStorage(),
            compute_log_manager=NoOpComputeLogManager(temp_dir),
            schedule_storage=SqliteScheduleStorage.from_local(temp_dir),
            scheduler=FilesytemTestScheduler(temp_dir),
        )

        context = define_context_for_repository_yaml(
            path=file_relative_path(__file__, '../repository.yaml'), instance=instance
        )

        # Initialize scheduler
        repository = context.get_repository()
        scheduler_handle = context.scheduler_handle
        scheduler_handle.up(
            python_path=sys.executable,
            repository_path="",
            repository=repository,
            instance=instance,
        )

        # Start schedule
        schedule = instance.start_schedule(repository, "no_config_pipeline_hourly_schedule")

        # Query Scheduler + all Schedules
        scheduler_result = execute_dagster_graphql(context, GET_SCHEDULES_QUERY)

        assert scheduler_result.data
        assert scheduler_result.data['scheduler']
        assert scheduler_result.data['scheduler']['runningSchedules']
        assert len(scheduler_result.data['scheduler']['runningSchedules']) == 8

        for schedule in scheduler_result.data['scheduler']['runningSchedules']:
            assert (
                schedule['scheduleDefinition']['environmentConfigYaml']
                == 'storage:\n  filesystem: {}\n'
            )


def test_scheduler_change_set_adding_schedule():

    schedule_1 = ScheduleDefinition('schedule_1', "*****", "pipeline_name", {})
    schedule_2 = ScheduleDefinition('schedule_2', "*****", "pipeline_name", {})
    schedule_3 = ScheduleDefinition('schedule_3', "*****", "pipeline_name", {})
    schedule_4 = ScheduleDefinition('schedule_4', "*****", "pipeline_name", {})

    modified_schedule_2 = ScheduleDefinition(
        'schedule_2', "0****", "pipeline_name", {'new_key': "new_value"}
    )
    renamed_schedule_3 = ScheduleDefinition('renamed_schedule_3', "*****", "pipeline_name", {})

    running_1 = Schedule(schedule_1.schedule_definition_data, ScheduleStatus.RUNNING, "", "")
    running_2 = Schedule(schedule_2.schedule_definition_data, ScheduleStatus.RUNNING, "", "")
    running_3 = Schedule(schedule_3.schedule_definition_data, ScheduleStatus.RUNNING, "", "")
    running_4 = Schedule(schedule_4.schedule_definition_data, ScheduleStatus.RUNNING, "", "")

    # Add initial schedules
    change_set_1 = get_schedule_change_set([], [schedule_1, schedule_2])
    assert sorted(change_set_1) == sorted([('add', 'schedule_2', []), ('add', 'schedule_1', [])])

    # Add more schedules
    change_set_2 = get_schedule_change_set(
        [running_1, running_2], [schedule_1, schedule_2, schedule_3, schedule_4]
    )
    assert sorted(change_set_2) == sorted([('add', 'schedule_3', []), ('add', 'schedule_4', [])])

    # Modify schedule_2
    change_set_3 = get_schedule_change_set(
        [running_1, running_2, running_3, running_4],
        [schedule_1, modified_schedule_2, schedule_3, schedule_4],
    )
    assert change_set_3 == [('change', 'schedule_2', [('cron_schedule', ('*****', '0****'))])]

    # Delete schedules
    change_set_3 = get_schedule_change_set(
        [running_1, running_2, running_3, running_4], [schedule_3, schedule_4]
    )
    assert sorted(change_set_3) == sorted(
        [('remove', 'schedule_1', []), ('remove', 'schedule_2', [])]
    )

    # Rename schedules
    change_set_4 = get_schedule_change_set(
        [running_1, running_2, running_3, running_4],
        [schedule_1, schedule_2, renamed_schedule_3, schedule_4],
    )
    assert sorted(change_set_4) == sorted(
        [('add', 'renamed_schedule_3', []), ('remove', 'schedule_3', [])]
    )
