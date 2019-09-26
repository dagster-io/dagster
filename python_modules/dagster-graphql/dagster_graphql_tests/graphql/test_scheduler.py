import os
import sys

import mock
from dagster_graphql.test.utils import execute_dagster_graphql

from dagster.core.instance import DagsterInstance

from .setup import define_context_for_repository_yaml

GET_SCHEDULES_QUERY = '''
{
    scheduler {
      ... on Scheduler {
        runningSchedules {
          scheduleId
          scheduleDefinition {
            name
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
    instance = DagsterInstance.local_temp(features=['scheduler'])
    context = define_context_for_repository_yaml(instance=instance)

    # Initialize scheduler
    scheduler_handle = context.scheduler_handle
    scheduler_handle.init(python_path=sys.executable, repository_path="")

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
    assert len(scheduler_result.data['scheduler']['runningSchedules']) == 1

    assert (
        scheduler_result.data['scheduler']['runningSchedules'][0]['scheduleId']
        == schedule.schedule_id
    )
