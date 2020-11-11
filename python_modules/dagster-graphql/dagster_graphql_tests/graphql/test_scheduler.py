from dagster.core.scheduler.scheduler import ScheduleStatus
from dagster_graphql.test.utils import (
    execute_dagster_graphql,
    infer_repository_selector,
    infer_schedule_selector,
    main_repo_location_name,
    main_repo_name,
)

GET_SCHEDULE_STATES_QUERY = """
query ScheduleStateQuery($repositorySelector: RepositorySelector!) {
  scheduleStatesOrError(repositorySelector: $repositorySelector) {
    __typename
    ... on PythonError {
      message
      stack
    }
    ... on ScheduleStates {
      results {
        runs {
            runId
        }
        runsCount
        status
      }
    }
  }
}
"""

GET_SCHEDULE_STATES_WITHOUT_DEFINITIONS_QUERY = """
query ScheduleStateQuery($repositorySelector: RepositorySelector!) {
  scheduleStatesOrError(repositorySelector: $repositorySelector, withNoScheduleDefinition: true) {
    __typename
    ... on PythonError {
      message
      stack
    }
    ... on ScheduleStates {
      results {
        runs {
            runId
        }
        runsCount
        status
      }
    }
  }
}
"""

GET_SCHEDULE_DEFINITIONS_QUERY = """
query ScheduleDefinitionsQuery($repositorySelector: RepositorySelector!) {
  scheduleDefinitionsOrError(repositorySelector: $repositorySelector) {
    __typename
    ... on PythonError {
      message
      stack
    }
    ... on ScheduleDefinitions {
      results {
        name
        cronSchedule
        pipelineName
        solidSelection
        mode
        executionTimezone
        runConfigOrError {
          __typename
          ... on ScheduleRunConfig {
            yaml
          }
        }
      }
    }
  }
}
"""

GET_SCHEDULE_DEFINITION = """
query getScheduleDefinition($scheduleSelector: ScheduleSelector!) {
  scheduleDefinitionOrError(scheduleSelector: $scheduleSelector) {
    __typename
    ... on PythonError {
      message
      stack
    }
    ... on ScheduleDefinition {
      name
      partitionSet {
        name
      }
      executionTimezone
    }
  }
}
"""

RECONCILE_SCHEDULER_STATE_QUERY = """
mutation(
  $repositorySelector: RepositorySelector!
) {
  reconcileSchedulerState(
    repositorySelector: $repositorySelector,
  ) {
      ... on PythonError {
        message
        stack
      }
      ... on ReconcileSchedulerStateSuccess {
        message
      }
    }
}
"""


START_SCHEDULES_QUERY = """
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
    ... on ScheduleStateResult {
      scheduleState {
        scheduleOriginId
        status
      }
    }
  }
}
"""


STOP_SCHEDULES_QUERY = """
mutation(
  $scheduleOriginId: String!
) {
  stopRunningSchedule(
    scheduleOriginId: $scheduleOriginId,
  ) {
    ... on PythonError {
      message
      className
      stack
    }
    ... on ScheduleStateResult {
      scheduleState {
        status
      }
    }
  }
}
"""


def default_execution_params():
    return {
        "runConfigData": {"storage": {"filesystem": None}},
        "selector": {"name": "no_config_pipeline", "solidSelection": None},
        "mode": "default",
    }


def test_get_schedule_definitions_for_repository(graphql_context):
    selector = infer_repository_selector(graphql_context)
    result = execute_dagster_graphql(
        graphql_context, GET_SCHEDULE_DEFINITIONS_QUERY, variables={"repositorySelector": selector},
    )

    assert result.data
    assert result.data["scheduleDefinitionsOrError"]
    assert result.data["scheduleDefinitionsOrError"]["__typename"] == "ScheduleDefinitions"

    external_repository = graphql_context.get_repository_location(
        main_repo_location_name()
    ).get_repository(main_repo_name())

    results = result.data["scheduleDefinitionsOrError"]["results"]
    assert len(results) == len(external_repository.get_external_schedules())

    for schedule in results:
        if (
            schedule["name"] == "run_config_error_schedule"
            or schedule["name"] == "tags_error_schedule"
        ):
            assert schedule["runConfigOrError"]["__typename"] == "PythonError"
        elif schedule["name"] == "invalid_config_schedule":
            assert (
                schedule["runConfigOrError"]["yaml"]
                == "solids:\n  takes_an_enum:\n    config: invalid\n"
            )
        elif schedule["name"] == "timezone_schedule":
            assert schedule["executionTimezone"] == "US/Central"
        else:
            assert schedule["runConfigOrError"]["yaml"] == "storage:\n  filesystem: {}\n"


def test_get_schedule_states_for_repository(graphql_context):
    selector = infer_repository_selector(graphql_context)
    result = execute_dagster_graphql(
        graphql_context, GET_SCHEDULE_STATES_QUERY, variables={"repositorySelector": selector},
    )

    assert result.data
    assert result.data["scheduleStatesOrError"]
    assert result.data["scheduleStatesOrError"]["__typename"] == "ScheduleStates"

    # Since we haven't run reconcile yet, there should be no states in storage
    results = result.data["scheduleStatesOrError"]["results"]
    assert len(results) == 0


def test_get_schedule_state_with_for_repository_not_reconciled(graphql_context):
    selector = infer_repository_selector(graphql_context)
    result = execute_dagster_graphql(
        graphql_context, GET_SCHEDULE_STATES_QUERY, variables={"repositorySelector": selector},
    )

    assert result.data
    assert result.data["scheduleStatesOrError"]
    assert result.data["scheduleStatesOrError"]["__typename"] == "ScheduleStates"

    # Since we haven't run reconcile yet, there should be no states in storage
    results = result.data["scheduleStatesOrError"]["results"]
    assert len(results) == 0


def test_get_schedule_states_for_repository_after_reconcile(graphql_context):
    selector = infer_repository_selector(graphql_context)

    external_repository = graphql_context.get_repository_location(
        main_repo_location_name()
    ).get_repository(main_repo_name())
    graphql_context.instance.reconcile_scheduler_state(external_repository)

    result = execute_dagster_graphql(
        graphql_context, GET_SCHEDULE_STATES_QUERY, variables={"repositorySelector": selector},
    )

    assert result.data
    assert result.data["scheduleStatesOrError"]
    assert result.data["scheduleStatesOrError"]["__typename"] == "ScheduleStates"

    results = result.data["scheduleStatesOrError"]["results"]
    assert len(results) == len(external_repository.get_external_schedules())

    for schedule_state in results:
        assert schedule_state["status"] == ScheduleStatus.STOPPED.value


def test_get_schedule_states_for_repository_after_reconcile_using_mutation(graphql_context):
    selector = infer_repository_selector(graphql_context)

    external_repository = graphql_context.get_repository_location(
        main_repo_location_name()
    ).get_repository(main_repo_name())

    result = execute_dagster_graphql(
        graphql_context,
        RECONCILE_SCHEDULER_STATE_QUERY,
        variables={"repositorySelector": selector},
    )

    assert result.data
    assert result.data["reconcileSchedulerState"]
    assert result.data["reconcileSchedulerState"]["message"] == "Success"

    result = execute_dagster_graphql(
        graphql_context, GET_SCHEDULE_STATES_QUERY, variables={"repositorySelector": selector},
    )

    assert result.data
    assert result.data["scheduleStatesOrError"]
    assert result.data["scheduleStatesOrError"]["__typename"] == "ScheduleStates"

    results = result.data["scheduleStatesOrError"]["results"]
    assert len(results) == len(external_repository.get_external_schedules())

    for schedule_state in results:
        assert schedule_state["status"] == ScheduleStatus.STOPPED.value


def test_get_schedule_states_for_repository_with_removed_schedule_definitions(graphql_context):
    selector = infer_repository_selector(graphql_context)

    external_repository = graphql_context.get_repository_location(
        main_repo_location_name()
    ).get_repository(main_repo_name())
    graphql_context.instance.reconcile_scheduler_state(external_repository)

    result = execute_dagster_graphql(
        graphql_context,
        GET_SCHEDULE_STATES_WITHOUT_DEFINITIONS_QUERY,
        variables={"repositorySelector": selector},
    )

    assert result.data["scheduleStatesOrError"]
    assert result.data["scheduleStatesOrError"]["__typename"] == "ScheduleStates"
    results = result.data["scheduleStatesOrError"]["results"]
    assert len(results) == 0


def test_start_and_stop_schedule(graphql_context):
    # selector = infer_repository_selector(graphql_context)

    external_repository = graphql_context.get_repository_location(
        main_repo_location_name()
    ).get_repository(main_repo_name())
    graphql_context.instance.reconcile_scheduler_state(external_repository)

    schedule_selector = infer_schedule_selector(
        graphql_context, "no_config_pipeline_hourly_schedule"
    )

    # Start a single schedule
    start_result = execute_dagster_graphql(
        graphql_context, START_SCHEDULES_QUERY, variables={"scheduleSelector": schedule_selector},
    )
    assert (
        start_result.data["startSchedule"]["scheduleState"]["status"]
        == ScheduleStatus.RUNNING.value
    )

    schedule_origin_id = start_result.data["startSchedule"]["scheduleState"]["scheduleOriginId"]

    # Stop a single schedule
    stop_result = execute_dagster_graphql(
        graphql_context, STOP_SCHEDULES_QUERY, variables={"scheduleOriginId": schedule_origin_id},
    )
    assert (
        stop_result.data["stopRunningSchedule"]["scheduleState"]["status"]
        == ScheduleStatus.STOPPED.value
    )


def test_get_single_schedule_definition(graphql_context):
    context = graphql_context
    instance = context.instance

    instance.reconcile_scheduler_state(
        external_repository=context.get_repository_location(
            main_repo_location_name()
        ).get_repository(main_repo_name()),
    )

    schedule_selector = infer_schedule_selector(context, "partition_based_multi_mode_decorator")
    result = execute_dagster_graphql(
        context, GET_SCHEDULE_DEFINITION, variables={"scheduleSelector": schedule_selector}
    )

    assert result.data

    assert result.data["scheduleDefinitionOrError"]["__typename"] == "ScheduleDefinition"
    assert result.data["scheduleDefinitionOrError"]["partitionSet"]
    assert not result.data["scheduleDefinitionOrError"]["executionTimezone"]

    schedule_selector = infer_schedule_selector(context, "timezone_schedule")
    result = execute_dagster_graphql(
        context, GET_SCHEDULE_DEFINITION, variables={"scheduleSelector": schedule_selector}
    )

    assert result.data
    assert result.data["scheduleDefinitionOrError"]["__typename"] == "ScheduleDefinition"
    assert result.data["scheduleDefinitionOrError"]["executionTimezone"] == "US/Central"
