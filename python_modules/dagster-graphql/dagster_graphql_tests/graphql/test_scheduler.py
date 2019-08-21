import os
import sys

import mock
from dagster_graphql.test.utils import execute_dagster_graphql

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


def get_schedule_definition_from_context(context):
    repository = context.get_handle().build_repository_definition()
    schedule_def = repository.get_schedule("no_config_pipeline_hourly_schedule")

    return schedule_def


@mock.patch.dict(os.environ, {"DAGSTER_HOME": "~/dagster"})
def test_get_all_schedules():
    instance = DagsterInstance.local_temp(features={'scheduler'})
    context = define_context(instance=instance)

    # Start schedule
    schedule_def = get_schedule_definition_from_context(context)
    scheduler = context.scheduler
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
