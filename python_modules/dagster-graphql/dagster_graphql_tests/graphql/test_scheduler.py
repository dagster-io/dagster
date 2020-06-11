import os

import mock
from dagster_graphql.test.utils import execute_dagster_graphql, get_legacy_schedule_selector

from .setup import define_test_context, main_repo_location_name, main_repo_name

GET_SCHEDULES_QUERY = '''
{
  schedules {
    scheduleDefinition {
      name
      pipelineName
      mode
      solidSelection
      runConfigYaml
    }
    runs {
        runId
    }
    runsCount
    status
  }
}
'''

GET_SCHEDULE_DEFINITIONS_QUERY = '''
{
  scheduleDefinitions {
    name
    cronSchedule
    pipelineName
    solidSelection
    mode
    runConfigYaml
  }
}
'''

START_SCHEDULES_QUERY = '''
mutation(
  $scheduleSelector: ScheduleSelector!
) {
  startSchedule(
    scheduleSelector: $scheduleSelector,
  ) {
    ... on PythonError {
      message
      className
      stack
    }
    ... on RunningScheduleResult {
      schedule {
        status
      }
    }
  }
}
'''


STOP_SCHEDULES_QUERY = '''
mutation(
  $scheduleSelector: ScheduleSelector!
) {
  stopRunningSchedule(
    scheduleSelector: $scheduleSelector,
  ) {
    ... on PythonError {
      message
      className
      stack
    }
    ... on RunningScheduleResult {
      schedule {
        status
      }
    }
  }
}
'''

GET_SCHEDULE = '''
query getSchedule($scheduleSelector: ScheduleSelector!) {
  scheduleOrError(scheduleSelector: $scheduleSelector) {
    __typename
    ... on PythonError {
      message
      stack
    }
    ... on RunningSchedule {
      scheduleDefinition {
        name
        partitionSet {
          name
        }
      }
    }
  }
}

'''


def default_execution_params():
    return {
        "runConfigData": {"storage": {"filesystem": None}},
        "selector": {"name": "no_config_pipeline", "solidSelection": None},
        "mode": "default",
    }


@mock.patch.dict(os.environ, {"DAGSTER_HOME": "~/dagster"})
def test_get_all_schedule_definitions(graphql_context):
    context = graphql_context

    external_repository = context.get_repository_location(main_repo_location_name()).get_repository(
        main_repo_name()
    )

    result = execute_dagster_graphql(context, GET_SCHEDULE_DEFINITIONS_QUERY)

    assert result
    assert result.data
    assert result.data['scheduleDefinitions']

    # These schedules are defined in dagster_graphql_tests/graphql/setup.py
    # If you add a schedule there, be sure to update the number of schedules below
    assert len(result.data['scheduleDefinitions']) == len(
        external_repository.get_external_schedules()
    )


@mock.patch.dict(os.environ, {"DAGSTER_HOME": "~/dagster"})
def test_start_stop_schedule(graphql_context):
    context = graphql_context
    instance = context.instance

    context = define_test_context(instance)
    # Initialize scheduler
    external_repository = context.get_repository_location(main_repo_location_name()).get_repository(
        main_repo_name()
    )
    instance.reconcile_scheduler_state(external_repository)

    schedule_selector = get_legacy_schedule_selector(context, 'no_config_pipeline_hourly_schedule')

    # Start schedule
    start_result = execute_dagster_graphql(
        context, START_SCHEDULES_QUERY, variables={'scheduleSelector': schedule_selector},
    )
    assert start_result.data['startSchedule']['schedule']['status'] == 'RUNNING'

    # Stop schedule
    stop_result = execute_dagster_graphql(
        context, STOP_SCHEDULES_QUERY, variables={'scheduleSelector': schedule_selector},
    )
    assert stop_result.data['stopRunningSchedule']['schedule']['status'] == 'STOPPED'


@mock.patch.dict(os.environ, {"DAGSTER_HOME": "~/dagster"})
def test_get_all_schedules(graphql_context):
    context = graphql_context
    instance = context.instance

    external_repository = context.get_repository_location(main_repo_location_name()).get_repository(
        main_repo_name()
    )
    instance.reconcile_scheduler_state(external_repository)

    # Initialize scheduler
    instance.reconcile_scheduler_state(external_repository)

    # Start schedule
    schedule = instance.start_schedule_and_update_storage_state(
        external_repository.get_external_schedule("no_config_pipeline_hourly_schedule")
    )

    # Query Scheduler + all Schedules
    scheduler_result = execute_dagster_graphql(context, GET_SCHEDULES_QUERY)

    # These schedules are defined in dagster_graphql_tests/graphql/setup.py
    # If you add a schedule there, be sure to update the number of schedules below
    assert scheduler_result.data
    assert scheduler_result.data['schedules']
    assert len(scheduler_result.data['schedules']) == 18

    for schedule in scheduler_result.data['schedules']:
        if schedule['scheduleDefinition']['name'] == 'no_config_pipeline_hourly_schedule':
            assert schedule['status'] == 'RUNNING'

        if schedule['scheduleDefinition']['name'] == 'environment_dict_error_schedule':
            assert schedule['scheduleDefinition']['runConfigYaml'] is None
        elif schedule['scheduleDefinition']['name'] == 'invalid_config_schedule':
            assert (
                schedule['scheduleDefinition']['runConfigYaml']
                == 'solids:\n  takes_an_enum:\n    config: invalid\n'
            )
        else:
            assert schedule['scheduleDefinition']['runConfigYaml'] == 'storage:\n  filesystem: {}\n'


def test_get_schedule(graphql_context):
    context = graphql_context
    instance = context.instance

    instance.reconcile_scheduler_state(
        external_repository=context.get_repository_location(
            main_repo_location_name()
        ).get_repository(main_repo_name()),
    )

    schedule_selector = get_legacy_schedule_selector(
        context, 'partition_based_multi_mode_decorator'
    )
    result = execute_dagster_graphql(
        context, GET_SCHEDULE, variables={'scheduleSelector': schedule_selector}
    )

    assert result.data
    assert result.data['scheduleOrError']['__typename'] == 'RunningSchedule'
    assert result.data['scheduleOrError']['scheduleDefinition']['partitionSet']
