import os
import sys

import mock
from dagster_graphql.test.utils import execute_dagster_graphql
from dagster_tests.utils import MockScheduler

from dagster import ScheduleDefinition
from dagster.core.instance import DagsterInstance

from .utils import define_context

GET_SCHEDULES_QUERY = '''
{
    scheduler {
      ... on Scheduler {
        runningSchedules {
          scheduleId
          scheduleDefinition {
            name
          }
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


def define_scheduler(artifacts_dir):
    no_config_pipeline_hourly_schedule = ScheduleDefinition(
        name="no_config_pipeline_hourly_schedule",
        cron_schedule="0 0 * * *",
        execution_params={
            "environmentConfigData": {"storage": {"filesystem": None}},
            "selector": {"name": "no_config_pipeline", "solidSubset": None},
            "mode": "default",
        },
    )
    return MockScheduler(
        schedule_defs=[no_config_pipeline_hourly_schedule], artifacts_dir=artifacts_dir
    )


@mock.patch.dict(os.environ, {"DAGSTER_HOME": "~/dagster"})
def test_get_all_schedules():
    instance = DagsterInstance.local_temp(features=['scheduler'])
    scheduler = define_scheduler(instance.schedules_directory())
    context = define_context(instance=instance, scheduler=scheduler)

    # Start schedule
    schedule_def = scheduler.get_schedule_def("no_config_pipeline_hourly_schedule")
    schedule = scheduler.start_schedule(schedule_def, sys.executable, "")

    # Query Scheduler + all Schedules
    scheduler_result = execute_dagster_graphql(
        context, GET_SCHEDULES_QUERY, variables={"pipelineName": "no_config_pipeline"}
    )

    assert scheduler_result.data
    assert scheduler_result.data['scheduler']
    assert scheduler_result.data['scheduler']['runningSchedules']
    assert len(scheduler_result.data['scheduler']['runningSchedules']) == 1

    assert (
        scheduler_result.data['scheduler']['runningSchedules'][0]['scheduleId']
        == schedule.schedule_id
    )
