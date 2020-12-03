import pendulum
from dagster.core.scheduler.job import JobStatus
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
        scheduleName
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
      }
    }
  }
}
"""

GET_SCHEDULE_DEFINITION = """
query getScheduleDefinition($scheduleSelector: ScheduleSelector!, $ticksAfter: Float) {
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
      futureTicks(limit: 3, cursor: $ticksAfter) {
        results {
          timestamp
        }
        cursor
      }
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
        "runConfigData": {"intermediate_storage": {"filesystem": None}},
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
        if schedule["name"] == "timezone_schedule":
            assert schedule["executionTimezone"] == "US/Central"


def test_get_schedule_states_for_repository(graphql_context):
    selector = infer_repository_selector(graphql_context)
    result = execute_dagster_graphql(
        graphql_context, GET_SCHEDULE_STATES_QUERY, variables={"repositorySelector": selector},
    )

    external_repository = graphql_context.get_repository_location(
        main_repo_location_name()
    ).get_repository(main_repo_name())

    assert result.data
    assert result.data["scheduleStatesOrError"]
    assert result.data["scheduleStatesOrError"]["__typename"] == "ScheduleStates"

    results = result.data["scheduleStatesOrError"]["results"]
    assert len(results) == len(external_repository.get_external_schedules())

    for schedule_state in results:
        assert schedule_state["status"] == JobStatus.STOPPED.value


def test_get_schedule_state_with_for_repository_not_reconciled(graphql_context):
    selector = infer_repository_selector(graphql_context)
    result = execute_dagster_graphql(
        graphql_context, GET_SCHEDULE_STATES_QUERY, variables={"repositorySelector": selector},
    )

    external_repository = graphql_context.get_repository_location(
        main_repo_location_name()
    ).get_repository(main_repo_name())

    assert result.data
    assert result.data["scheduleStatesOrError"]
    assert result.data["scheduleStatesOrError"]["__typename"] == "ScheduleStates"

    results = result.data["scheduleStatesOrError"]["results"]
    assert len(results) == len(external_repository.get_external_schedules())

    for schedule_state in results:
        assert schedule_state["status"] == JobStatus.STOPPED.value


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
        assert schedule_state["status"] == JobStatus.STOPPED.value


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
        assert schedule_state["status"] == JobStatus.STOPPED.value


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


def test_start_without_initial_reconcile(graphql_context):

    repo_selector = infer_repository_selector(graphql_context)

    external_repository = graphql_context.get_repository_location(
        main_repo_location_name()
    ).get_repository(main_repo_name())

    schedule_selector = infer_schedule_selector(
        graphql_context, "no_config_pipeline_hourly_schedule"
    )

    # Start a single schedule
    start_result = execute_dagster_graphql(
        graphql_context, START_SCHEDULES_QUERY, variables={"scheduleSelector": schedule_selector},
    )
    assert start_result.data["startSchedule"]["scheduleState"]["status"] == JobStatus.RUNNING.value

    result = execute_dagster_graphql(
        graphql_context, GET_SCHEDULE_STATES_QUERY, variables={"repositorySelector": repo_selector},
    )

    assert result.data
    assert result.data["scheduleStatesOrError"]
    assert result.data["scheduleStatesOrError"]["__typename"] == "ScheduleStates"

    results = result.data["scheduleStatesOrError"]["results"]
    assert len(results) == len(external_repository.get_external_schedules())

    for schedule_state in results:
        assert (
            schedule_state["status"] == JobStatus.RUNNING.value
            if schedule_state["scheduleName"] == "no_config_pipeline_hourly_schedule"
            else JobStatus.STOPPED.value
        )


def test_start_and_stop_schedule(graphql_context):
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
    assert start_result.data["startSchedule"]["scheduleState"]["status"] == JobStatus.RUNNING.value

    schedule_origin_id = start_result.data["startSchedule"]["scheduleState"]["scheduleOriginId"]

    # Stop a single schedule
    stop_result = execute_dagster_graphql(
        graphql_context, STOP_SCHEDULES_QUERY, variables={"scheduleOriginId": schedule_origin_id},
    )
    assert (
        stop_result.data["stopRunningSchedule"]["scheduleState"]["status"]
        == JobStatus.STOPPED.value
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

    future_ticks = result.data["scheduleDefinitionOrError"]["futureTicks"]
    assert future_ticks
    assert len(future_ticks["results"]) == 3

    schedule_selector = infer_schedule_selector(context, "timezone_schedule")

    future_ticks_start_time = pendulum.create(2019, 2, 27, tz="US/Central").timestamp()

    result = execute_dagster_graphql(
        context,
        GET_SCHEDULE_DEFINITION,
        variables={"scheduleSelector": schedule_selector, "ticksAfter": future_ticks_start_time},
    )

    assert result.data
    assert result.data["scheduleDefinitionOrError"]["__typename"] == "ScheduleDefinition"
    assert result.data["scheduleDefinitionOrError"]["executionTimezone"] == "US/Central"

    future_ticks = result.data["scheduleDefinitionOrError"]["futureTicks"]
    assert future_ticks
    assert len(future_ticks["results"]) == 3
    timestamps = [future_tick["timestamp"] for future_tick in future_ticks["results"]]

    assert timestamps == [
        pendulum.create(2019, 2, 27, tz="US/Central").timestamp(),
        pendulum.create(2019, 2, 28, tz="US/Central").timestamp(),
        pendulum.create(2019, 3, 1, tz="US/Central").timestamp(),
    ]

    cursor = future_ticks["cursor"]

    assert future_ticks["cursor"] == (pendulum.create(2019, 3, 1, tz="US/Central").timestamp() + 1)

    result = execute_dagster_graphql(
        context,
        GET_SCHEDULE_DEFINITION,
        variables={"scheduleSelector": schedule_selector, "ticksAfter": cursor},
    )

    future_ticks = result.data["scheduleDefinitionOrError"]["futureTicks"]

    assert future_ticks
    assert len(future_ticks["results"]) == 3
    timestamps = [future_tick["timestamp"] for future_tick in future_ticks["results"]]

    assert timestamps == [
        pendulum.create(2019, 3, 2, tz="US/Central").timestamp(),
        pendulum.create(2019, 3, 3, tz="US/Central").timestamp(),
        pendulum.create(2019, 3, 4, tz="US/Central").timestamp(),
    ]
