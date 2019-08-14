import json
import os

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

CREATE_SCHEDULE_QUERY = '''
mutation CreateSchedule($schedule: RunScheduleInput!) {
  createRunSchedule(schedule: $schedule) {
    schedule {
      scheduleId
      name
      cronSchedule
      executionParamsString
    }
  }
}
'''


DELETE_SCHEDULE_QUERY = '''
mutation DeleteSchedule($scheduleId: String!) {
  deleteRunSchedule(scheduleId: $scheduleId) {
    deletedSchedule {
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


def create_schedule(context, name, cron_schedule, execution_params):
    variables = {
        "schedule": {
            "name": name,
            "cronSchedule": cron_schedule,
            "executionParams": execution_params,
        }
    }

    return execute_dagster_graphql(context, CREATE_SCHEDULE_QUERY, variables=variables)


def create_default_schedule(context):
    execution_params = default_execution_params()
    return create_schedule(context, "run_no_config_pipeline", "* * * * *", execution_params)


def test_create_schedule():
    with tempfile.TemporaryDirectory() as schedule_dir:
        context = define_context(schedule_dir=schedule_dir)

        execution_params = default_execution_params()
        result = create_schedule(context, "run_no_config_pipeline", "* * * * *", execution_params)

        assert result.data
        assert result.data['createRunSchedule']

        schedule = result.data['createRunSchedule']['schedule']
        assert schedule
        assert schedule['scheduleId']
        assert schedule['name'] == "run_no_config_pipeline"
        assert schedule['cronSchedule'] == "* * * * *"
        assert json.loads(schedule['executionParamsString']) == execution_params


@mock.patch.dict(os.environ, {"DAGSTER_HOME": "~/dagster"})
def test_start_and_end_schedule():
    with tempfile.TemporaryDirectory() as schedule_dir:
        context = define_context(schedule_dir=schedule_dir)

        result = create_default_schedule(context)
        schedule_name = result.data['createRunSchedule']['schedule']['name']
        schedule_id = result.data['createRunSchedule']['schedule']['scheduleId']

        # Delete Schedule
        start_result = execute_dagster_graphql(
            context, START_SCHEDULE_QUERY, variables={"scheduleId": schedule_id}
        )

        assert start_result.data
        assert start_result.data['startRunSchedule']
        assert start_result.data['startRunSchedule']['schedule']
        assert start_result.data['startRunSchedule']['schedule']['scheduleId'] == schedule_id

        assert "/bin/python" in start_result.data['startRunSchedule']['schedule']['pythonPath']

        # Check bash script was created
        assert "{}_{}.sh".format(schedule_name, schedule_id) in os.listdir(schedule_dir)

        end_result = execute_dagster_graphql(
            context, END_SCHEDULE_QUERY, variables={"scheduleId": schedule_id}
        )

        assert end_result.data
        assert end_result.data['endRunSchedule']
        assert end_result.data['endRunSchedule']['schedule']
        assert end_result.data['endRunSchedule']['schedule']['scheduleId'] == schedule_id

        # Check bash script was deleted
        assert "{}_{}.sh".format(schedule_name, schedule_id) not in os.listdir(schedule_dir)


def test_delete_schedule():
    with tempfile.TemporaryDirectory() as schedule_dir:
        context = define_context(schedule_dir=schedule_dir)

        result = create_default_schedule(context)
        schedule_id = result.data['createRunSchedule']['schedule']['scheduleId']

        # Delete Schedule
        delete_result = execute_dagster_graphql(
            context, DELETE_SCHEDULE_QUERY, variables={"scheduleId": schedule_id}
        )

        assert delete_result.data
        assert delete_result.data['deleteRunSchedule']
        assert delete_result.data['deleteRunSchedule']['deletedSchedule']
        assert (
            delete_result.data['deleteRunSchedule']['deletedSchedule']['scheduleId'] == schedule_id
        )

        # Query all Schedules
        scheduler_result = execute_dagster_graphql(
            context, GET_SCHEDULES_QUERY, variables={"pipelineName": "no_config_pipeline"}
        )

        assert scheduler_result.data
        assert len(scheduler_result.data['scheduler']['schedules']) == 0


def test_get_all_schedules():
    with tempfile.TemporaryDirectory() as schedule_dir:
        context = define_context(schedule_dir=schedule_dir)

        result = create_default_schedule(context)
        schedule_id = result.data['createRunSchedule']['schedule']['scheduleId']

        # Query Scheduler + all Schedules
        scheduler_result = execute_dagster_graphql(
            context, GET_SCHEDULES_QUERY, variables={"pipelineName": "no_config_pipeline"}
        )

        assert scheduler_result.data
        assert scheduler_result.data['scheduler']
        assert scheduler_result.data['scheduler']['schedules']
        assert len(scheduler_result.data['scheduler']['schedules']) == 1

        assert scheduler_result.data['scheduler']['schedules'][0]['scheduleId'] == schedule_id
