import os
import sys

from dagster import check
from dagster.core.scheduler import RunningSchedule
from dagster_graphql.test.utils import execute_dagster_graphql
from dagster.seven import mock

from .utils import define_context

try:
    # Python 2 tempfile doesn't have tempfile.TemporaryDirectory
    import backports.tempfile as tempfile
except ImportError:
    import tempfile

GET_SCHEDULES_QUERY = '''
{
  scheduler {
        schedulerType
        schedules {
            scheduleId
        }
    }
}
'''


START_SCHEDULE_QUERY = '''
mutation StartSchedule($scheduleId: String!) {
  startRunSchedule(scheduleId: $scheduleId) {
    schedule {
      scheduleId
      pythonPath
      repositoryPath
    }
  }
}
'''

END_SCHEDULE_QUERY = '''
mutation EndSchedule($scheduleId: String!) {
  endRunSchedule(scheduleId: $scheduleId) {
    schedule {
      scheduleId
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
def test_start_and_end_schedule():
    with tempfile.TemporaryDirectory() as schedule_dir:
        context = define_context(schedule_dir=schedule_dir)

        # Start schedule
        schedule_def = get_schedule_definition_from_context(context)
        scheduler = context.scheduler
        schedule = scheduler.start_schedule(schedule_def, sys.executable, "")

        check.inst_param(schedule, 'schedule', RunningSchedule)
        assert schedule.schedule_definition == schedule_def
        assert "/bin/python" in schedule.python_path

        assert "{}_{}.json".format(schedule_def.name, schedule.schedule_id) in os.listdir(
            schedule_dir
        )
        assert "{}_{}.sh".format(schedule_def.name, schedule.schedule_id) in os.listdir(
            schedule_dir
        )

        # End schedule
        scheduler.end_schedule(schedule_def)
        assert "{}_{}.json".format(schedule_def.name, schedule.schedule_id) not in os.listdir(
            schedule_dir
        )
        assert "{}_{}.sh".format(schedule_def.name, schedule.schedule_id) not in os.listdir(
            schedule_dir
        )


@mock.patch.dict(os.environ, {"DAGSTER_HOME": "~/dagster"})
def test_get_all_schedules():
    with tempfile.TemporaryDirectory() as schedule_dir:
        context = define_context(schedule_dir=schedule_dir)

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
        assert scheduler_result.data['scheduler']['schedules']
        assert len(scheduler_result.data['scheduler']['schedules']) == 1

        assert (
            scheduler_result.data['scheduler']['schedules'][0]['scheduleId'] == schedule.schedule_id
        )
