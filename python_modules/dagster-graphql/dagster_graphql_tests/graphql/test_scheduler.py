import json

from dagster_graphql.test.utils import execute_dagster_graphql

from .utils import define_context

try:
    # Python 2 tempfile doesn't have tempfile.TemporaryDirectory
    import backports.tempfile as tempfile
except ImportError:
    import tempfile


CREATE_PIPELINE_SCHEDULE_QUERY = '''
mutation CreatePipelineScheduleResult($schedule: RunScheduleInput!) {
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

DELETE_SCHEDULE_QUERY = '''
mutation DeletePipelineSchedule($scheduleId: String!) {
  deleteRunSchedule(scheduleId: $scheduleId) {
    deletedSchedule {
      scheduleId
    }
  }
}
'''


def create_default_schedule(context):
    execution_params = {
        "environmentConfigData": {"storage": {"filesystem": None}},
        "selector": {"name": "many_events", "solidSubset": None},
        "mode": "default",
    }

    return create_schedule(context, "run_many_events", "* * * * *", execution_params)


def create_schedule(context, name, cron_schedule, execution_params):
    variables = {
        "schedule": {
            "name": name,
            "cronSchedule": cron_schedule,
            "executionParams": execution_params,
        }
    }

    return execute_dagster_graphql(context, CREATE_PIPELINE_SCHEDULE_QUERY, variables=variables)


def test_create_schedule():
    with tempfile.TemporaryDirectory() as schedule_dir:
        context = define_context(schedule_dir=schedule_dir)

        execution_params = {
            "environmentConfigData": {"storage": {"filesystem": None}},
            "selector": {"name": "many_events", "solidSubset": None},
            "mode": "default",
        }

        result = create_schedule(context, "run_many_events", "* * * * *", execution_params)

        assert result.data
        assert result.data['createRunSchedule']

        schedule = result.data['createRunSchedule']['schedule']
        assert schedule
        assert schedule['scheduleId']
        assert schedule['name'] == "run_many_events"
        assert schedule['cronSchedule'] == "* * * * *"
        assert json.loads(schedule['executionParamsString']) == execution_params


def test_get_all_schedules():
    with tempfile.TemporaryDirectory() as schedule_dir:
        context = define_context(schedule_dir=schedule_dir)

        result = create_default_schedule(context)
        schedule_id = result.data['createRunSchedule']['schedule']['scheduleId']

        # Query Scheduler + all Schedules
        scheduler_result = execute_dagster_graphql(
            context, GET_SCHEDULES_QUERY, variables={"pipelineName": "many_events"}
        )

        assert scheduler_result.data
        assert scheduler_result.data['scheduler']
        assert scheduler_result.data['scheduler']['schedules']
        assert len(scheduler_result.data['scheduler']['schedules']) == 1

        assert scheduler_result.data['scheduler']['schedules'][0]['scheduleId'] == schedule_id


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
            context, GET_SCHEDULES_QUERY, variables={"pipelineName": "many_events"}
        )

        assert scheduler_result.data
        assert len(scheduler_result.data['scheduler']['schedules']) == 0
