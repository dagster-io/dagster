import os
import sys

import mock
import pytest
from dagster_graphql.test.utils import execute_dagster_graphql

from dagster import ScheduleDefinition
from dagster.core.instance import DagsterInstance
from dagster.core.scheduler import Schedule, ScheduleStatus, get_schedule_change_set
from dagster.utils import file_relative_path

from .setup import define_context_for_repository_yaml

GET_SCHEDULES_QUERY = '''
{
    scheduler {
      ... on Scheduler {
        runningSchedules {
          id
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
    instance = DagsterInstance.local_temp()
    context = define_context_for_repository_yaml(
        path=file_relative_path(__file__, '../repository.yaml'), instance=instance
    )

    # Initialize scheduler
    scheduler_handle = context.scheduler_handle
    scheduler_handle.up(python_path=sys.executable, repository_path="")

    # Get scheduler
    scheduler = scheduler_handle.get_scheduler()

    # Start schedule
    schedule = scheduler.start_schedule("no_config_pipeline_hourly_schedule")

    # Query Scheduler + all Schedules
    scheduler_result = execute_dagster_graphql(
        context, GET_SCHEDULES_QUERY, variables={"pipelineName": "no_config_pipeline"}
    )

    assert scheduler_result.data
    assert scheduler_result.data['scheduler']
    assert scheduler_result.data['scheduler']['runningSchedules']
    assert len(scheduler_result.data['scheduler']['runningSchedules']) == 6

    assert scheduler_result.data['scheduler']['runningSchedules'][0]['id'] == schedule.schedule_id
    for schedule in scheduler_result.data['scheduler']['runningSchedules']:
        assert (
            schedule['scheduleDefinition']['environmentConfigYaml']
            == 'storage:\n  filesystem: {}\n'
        )


def test_schedule_definition_deprecation_warning():
    def load_context():
        instance = DagsterInstance.local_temp()
        define_context_for_repository_yaml(
            path=file_relative_path(__file__, '../repository.yaml'), instance=instance
        )

    with pytest.warns(
        DeprecationWarning,
        match='The `environment_dict` argument to ' '`ScheduleDefinition` is deprecated.',
    ):
        load_context()

    with pytest.warns(
        DeprecationWarning, match='The `tags` argument to `ScheduleDefinition` ' 'is deprecated.'
    ):
        load_context()


def test_scheduler_change_set_adding_schedule():

    schedule_1 = ScheduleDefinition('schedule_1', "*****", "pipeline_name", {})
    schedule_2 = ScheduleDefinition('schedule_2', "*****", "pipeline_name", {})
    schedule_3 = ScheduleDefinition('schedule_3', "*****", "pipeline_name", {})
    schedule_4 = ScheduleDefinition('schedule_4', "*****", "pipeline_name", {})

    modified_schedule_2 = ScheduleDefinition(
        'schedule_2', "0****", "pipeline_name", {'new_key': "new_value"}
    )
    renamed_schedule_3 = ScheduleDefinition('renamed_schedule_3', "*****", "pipeline_name", {})

    running_1 = Schedule("1", schedule_1.schedule_definition_data, ScheduleStatus.RUNNING, "", "")
    running_2 = Schedule("2", schedule_2.schedule_definition_data, ScheduleStatus.RUNNING, "", "")
    running_3 = Schedule("3", schedule_3.schedule_definition_data, ScheduleStatus.RUNNING, "", "")
    running_4 = Schedule("4", schedule_4.schedule_definition_data, ScheduleStatus.RUNNING, "", "")

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
