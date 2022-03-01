import os

import pendulum
from dagster_graphql.test.utils import (
    execute_dagster_graphql,
    infer_repository_selector,
    infer_schedule_selector,
    main_repo_location_name,
    main_repo_name,
)

from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.host_representation import (
    ExternalRepositoryOrigin,
    InProcessRepositoryLocationOrigin,
)
from dagster.core.scheduler.instigation import (
    InstigatorState,
    InstigatorStatus,
    InstigatorType,
    ScheduleInstigatorData,
)
from dagster.seven.compat.pendulum import create_pendulum_time
from dagster.utils import Counter, traced_counter

GET_SCHEDULES_QUERY = """
query SchedulesQuery($repositorySelector: RepositorySelector!) {
  schedulesOrError(repositorySelector: $repositorySelector) {
    __typename
    ... on PythonError {
      message
      stack
    }
    ... on Schedules {
      results {
        name
        cronSchedule
        pipelineName
        solidSelection
        mode
        description
        executionTimezone
      }
    }
  }
}
"""

GET_SCHEDULE_QUERY = """
query getSchedule($scheduleSelector: ScheduleSelector!, $ticksAfter: Float) {
  scheduleOrError(scheduleSelector: $scheduleSelector) {
    __typename
    ... on PythonError {
      message
      stack
    }
    ... on Schedule {
      name
      partitionSet {
        name
      }
      executionTimezone
      futureTicks(limit: 3, cursor: $ticksAfter) {
        results {
          timestamp
          evaluationResult {
            runRequests {
              runKey
              tags {
                key
                value
              }
              runConfigYaml
            }
            error {
              message
              stack
            }
            skipReason
          }
        }
        cursor
      }
      scheduleState {
        id
        ticks {
          id
          timestamp
        }
      }
    }
  }
}
"""

GET_SCHEDULE_STATE_QUERY = """
query getScheduleState($scheduleSelector: ScheduleSelector!) {
  scheduleOrError(scheduleSelector: $scheduleSelector) {
    __typename
    ... on Schedule {
      scheduleState {
        id
        status
      }
    }
  }
}
"""

GET_UNLOADABLE_QUERY = """
query getUnloadableSchedules {
  unloadableInstigationStatesOrError(instigationType: SCHEDULE) {
    ... on InstigationStates {
      results {
        id
        name
        status
      }
    }
    ... on PythonError {
      message
      stack
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
        id
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
        id
        status
      }
    }
  }
}
"""

GET_SCHEDULE_FUTURE_TICKS_UNTIL = """
query getSchedule($scheduleSelector: ScheduleSelector!, $ticksAfter: Float, $ticksUntil: Float) {
  scheduleOrError(scheduleSelector: $scheduleSelector) {
    __typename
    ... on PythonError {
      message
      stack
    }
    ... on Schedule {
      name
      futureTicks(cursor: $ticksAfter, until: $ticksUntil) {
        results {
          timestamp
        }
        cursor
      }
    }
  }
}
"""

REPOSITORY_SCHEDULES_QUERY = """
query RepositorySchedulesQuery($repositorySelector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $repositorySelector) {
        ... on Repository {
            id
            schedules {
                id
                name
                scheduleState {
                    id
                    runs(limit: 1) {
                      id
                      runId
                    }
                }
            }
        }
    }
}
"""


def default_execution_params():
    return {
        "selector": {"name": "no_config_pipeline", "solidSelection": None},
        "mode": "default",
    }


def _get_unloadable_schedule_origin(name):
    working_directory = os.path.dirname(__file__)
    recon_repo = ReconstructableRepository.for_file(__file__, "doesnt_exist", working_directory)
    return ExternalRepositoryOrigin(
        InProcessRepositoryLocationOrigin(recon_repo), "fake_repository"
    ).get_instigator_origin(name)


def test_get_schedule_definitions_for_repository(graphql_context):
    selector = infer_repository_selector(graphql_context)
    result = execute_dagster_graphql(
        graphql_context,
        GET_SCHEDULES_QUERY,
        variables={"repositorySelector": selector},
    )

    assert result.data
    assert result.data["schedulesOrError"]
    assert result.data["schedulesOrError"]["__typename"] == "Schedules"

    external_repository = graphql_context.get_repository_location(
        main_repo_location_name()
    ).get_repository(main_repo_name())

    results = result.data["schedulesOrError"]["results"]
    assert len(results) == len(external_repository.get_external_schedules())

    for schedule in results:
        if schedule["name"] == "timezone_schedule":
            assert schedule["executionTimezone"] == "US/Central"


def test_start_and_stop_schedule(graphql_context):
    schedule_selector = infer_schedule_selector(
        graphql_context, "no_config_pipeline_hourly_schedule"
    )

    # Start a single schedule
    start_result = execute_dagster_graphql(
        graphql_context,
        START_SCHEDULES_QUERY,
        variables={"scheduleSelector": schedule_selector},
    )
    assert (
        start_result.data["startSchedule"]["scheduleState"]["status"]
        == InstigatorStatus.RUNNING.value
    )

    schedule_origin_id = start_result.data["startSchedule"]["scheduleState"]["id"]

    # Stop a single schedule
    stop_result = execute_dagster_graphql(
        graphql_context,
        STOP_SCHEDULES_QUERY,
        variables={"scheduleOriginId": schedule_origin_id},
    )
    assert (
        stop_result.data["stopRunningSchedule"]["scheduleState"]["status"]
        == InstigatorStatus.STOPPED.value
    )


def test_get_single_schedule_definition(graphql_context):
    context = graphql_context

    schedule_selector = infer_schedule_selector(context, "partition_based_multi_mode_decorator")

    # fetch schedule before reconcile
    result = execute_dagster_graphql(
        context, GET_SCHEDULE_QUERY, variables={"scheduleSelector": schedule_selector}
    )
    assert result.data
    assert result.data["scheduleOrError"]["__typename"] == "Schedule"
    assert result.data["scheduleOrError"]["scheduleState"]

    result = execute_dagster_graphql(
        context, GET_SCHEDULE_QUERY, variables={"scheduleSelector": schedule_selector}
    )

    assert result.data

    assert result.data["scheduleOrError"]["__typename"] == "Schedule"
    assert result.data["scheduleOrError"]["partitionSet"]
    assert result.data["scheduleOrError"]["executionTimezone"] == "UTC"

    future_ticks = result.data["scheduleOrError"]["futureTicks"]
    assert future_ticks
    assert len(future_ticks["results"]) == 3

    schedule_selector = infer_schedule_selector(context, "timezone_schedule")

    future_ticks_start_time = create_pendulum_time(2019, 2, 27, tz="US/Central").timestamp()

    result = execute_dagster_graphql(
        context,
        GET_SCHEDULE_QUERY,
        variables={"scheduleSelector": schedule_selector, "ticksAfter": future_ticks_start_time},
    )

    assert result.data
    assert result.data["scheduleOrError"]["__typename"] == "Schedule"
    assert result.data["scheduleOrError"]["executionTimezone"] == "US/Central"

    future_ticks = result.data["scheduleOrError"]["futureTicks"]
    assert future_ticks
    assert len(future_ticks["results"]) == 3
    timestamps = [future_tick["timestamp"] for future_tick in future_ticks["results"]]

    assert timestamps == [
        create_pendulum_time(2019, 2, 27, tz="US/Central").timestamp(),
        create_pendulum_time(2019, 2, 28, tz="US/Central").timestamp(),
        create_pendulum_time(2019, 3, 1, tz="US/Central").timestamp(),
    ]

    cursor = future_ticks["cursor"]

    assert future_ticks["cursor"] == (
        create_pendulum_time(2019, 3, 1, tz="US/Central").timestamp() + 1
    )

    result = execute_dagster_graphql(
        context,
        GET_SCHEDULE_QUERY,
        variables={"scheduleSelector": schedule_selector, "ticksAfter": cursor},
    )

    future_ticks = result.data["scheduleOrError"]["futureTicks"]

    assert future_ticks
    assert len(future_ticks["results"]) == 3
    timestamps = [future_tick["timestamp"] for future_tick in future_ticks["results"]]

    assert timestamps == [
        create_pendulum_time(2019, 3, 2, tz="US/Central").timestamp(),
        create_pendulum_time(2019, 3, 3, tz="US/Central").timestamp(),
        create_pendulum_time(2019, 3, 4, tz="US/Central").timestamp(),
    ]


def test_next_tick(graphql_context):
    schedule_selector = infer_schedule_selector(
        graphql_context, "no_config_pipeline_hourly_schedule"
    )

    # Start a single schedule, future tick run requests only available for running schedules
    start_result = execute_dagster_graphql(
        graphql_context,
        START_SCHEDULES_QUERY,
        variables={"scheduleSelector": schedule_selector},
    )
    assert (
        start_result.data["startSchedule"]["scheduleState"]["status"]
        == InstigatorStatus.RUNNING.value
    )

    # get schedule next tick
    result = execute_dagster_graphql(
        graphql_context, GET_SCHEDULE_QUERY, variables={"scheduleSelector": schedule_selector}
    )

    future_ticks = result.data["scheduleOrError"]["futureTicks"]

    assert future_ticks
    assert len(future_ticks["results"]) == 3
    for tick in future_ticks["results"]:
        assert tick["evaluationResult"]
        assert tick["evaluationResult"]["runRequests"]
        assert len(tick["evaluationResult"]["runRequests"]) == 1


def test_next_tick_bad_schedule(graphql_context):
    schedule_selector = infer_schedule_selector(graphql_context, "run_config_error_schedule")

    # Start a single schedule, future tick run requests only available for running schedules
    start_result = execute_dagster_graphql(
        graphql_context,
        START_SCHEDULES_QUERY,
        variables={"scheduleSelector": schedule_selector},
    )
    assert (
        start_result.data["startSchedule"]["scheduleState"]["status"]
        == InstigatorStatus.RUNNING.value
    )

    # get schedule next tick
    result = execute_dagster_graphql(
        graphql_context, GET_SCHEDULE_QUERY, variables={"scheduleSelector": schedule_selector}
    )

    future_ticks = result.data["scheduleOrError"]["futureTicks"]

    assert future_ticks
    assert len(future_ticks["results"]) == 3
    for tick in future_ticks["results"]:
        assert tick["evaluationResult"]
        assert not tick["evaluationResult"]["runRequests"]
        assert not tick["evaluationResult"]["skipReason"]
        assert tick["evaluationResult"]["error"]


def test_get_unloadable_job(graphql_context):
    instance = graphql_context.instance
    initial_datetime = create_pendulum_time(
        year=2019,
        month=2,
        day=27,
        hour=23,
        minute=59,
        second=59,
    )
    with pendulum.test(initial_datetime):
        instance.add_instigator_state(
            InstigatorState(
                _get_unloadable_schedule_origin("unloadable_running"),
                InstigatorType.SCHEDULE,
                InstigatorStatus.RUNNING,
                ScheduleInstigatorData(
                    "0 0 * * *",
                    pendulum.now("UTC").timestamp(),
                ),
            )
        )

        instance.add_instigator_state(
            InstigatorState(
                _get_unloadable_schedule_origin("unloadable_stopped"),
                InstigatorType.SCHEDULE,
                InstigatorStatus.STOPPED,
                ScheduleInstigatorData(
                    "0 0 * * *",
                    pendulum.now("UTC").timestamp(),
                ),
            )
        )

    result = execute_dagster_graphql(graphql_context, GET_UNLOADABLE_QUERY)
    assert len(result.data["unloadableInstigationStatesOrError"]["results"]) == 1
    assert (
        result.data["unloadableInstigationStatesOrError"]["results"][0]["name"]
        == "unloadable_running"
    )


def test_future_ticks_until(graphql_context):
    schedule_selector = infer_schedule_selector(graphql_context, "timezone_schedule")

    future_ticks_start_time = create_pendulum_time(2019, 2, 27, tz="US/Central").timestamp()

    # Start a single schedule, future tick run requests only available for running schedules
    start_result = execute_dagster_graphql(
        graphql_context,
        START_SCHEDULES_QUERY,
        variables={"scheduleSelector": schedule_selector},
    )
    assert (
        start_result.data["startSchedule"]["scheduleState"]["status"]
        == InstigatorStatus.RUNNING.value
    )

    future_ticks_start_time = create_pendulum_time(2019, 2, 27, tz="US/Central").timestamp()
    future_ticks_end_time = create_pendulum_time(2019, 3, 2, tz="US/Central").timestamp()

    result = execute_dagster_graphql(
        graphql_context,
        GET_SCHEDULE_FUTURE_TICKS_UNTIL,
        variables={
            "scheduleSelector": schedule_selector,
            "ticksAfter": future_ticks_start_time,
            "ticksUntil": future_ticks_end_time,
        },
    )

    future_ticks = result.data["scheduleOrError"]["futureTicks"]

    assert future_ticks
    assert len(future_ticks["results"]) == 3

    timestamps = [future_tick["timestamp"] for future_tick in future_ticks["results"]]

    assert timestamps == [
        create_pendulum_time(2019, 2, 27, tz="US/Central").timestamp(),
        create_pendulum_time(2019, 2, 28, tz="US/Central").timestamp(),
        create_pendulum_time(2019, 3, 1, tz="US/Central").timestamp(),
    ]


def test_repository_batching(graphql_context):
    traced_counter.set(Counter())
    selector = infer_repository_selector(graphql_context)
    result = execute_dagster_graphql(
        graphql_context,
        REPOSITORY_SCHEDULES_QUERY,
        variables={"repositorySelector": selector},
    )
    assert result.data
    assert "repositoryOrError" in result.data
    assert "schedules" in result.data["repositoryOrError"]
    counter = traced_counter.get()
    counts = counter.counts()
    assert counts
    assert len(counts) == 2

    # We should have a single batch call to fetch run records (to fetch schedule runs) and a single
    # batch call to fetch instigator state, instead of separate calls for each schedule (~18
    # distinct schedules in the repo)
    # 1) `get_run_records` is fetched to instantiate GrapheneRun
    # 2) `all_instigator_state` is fetched to instantiate GrapheneSchedule
    assert counts.get("DagsterInstance.get_run_records") == 1
    assert counts.get("DagsterInstance.all_instigator_state") == 1


def test_start_schedule_with_default_status(graphql_context):
    schedule_selector = infer_schedule_selector(graphql_context, "running_in_code_schedule")

    result = execute_dagster_graphql(
        graphql_context,
        GET_SCHEDULE_STATE_QUERY,
        variables={"scheduleSelector": schedule_selector},
    )

    schedule_origin_id = result.data["scheduleOrError"]["scheduleState"]["id"]
    assert result.data["scheduleOrError"]["scheduleState"]["status"] == "RUNNING"

    # Start a single schedule
    start_result = execute_dagster_graphql(
        graphql_context,
        START_SCHEDULES_QUERY,
        variables={"scheduleSelector": schedule_selector},
    )

    assert (
        "You have attempted to start schedule running_in_code_schedule, but it is already running"
        in start_result.data["startSchedule"]["message"]
    )

    # Stop a single schedule
    stop_result = execute_dagster_graphql(
        graphql_context,
        STOP_SCHEDULES_QUERY,
        variables={"scheduleOriginId": schedule_origin_id},
    )
    assert (
        stop_result.data["stopRunningSchedule"]["scheduleState"]["status"]
        == InstigatorStatus.STOPPED.value
    )

    # Start a single schedule
    start_result = execute_dagster_graphql(
        graphql_context,
        START_SCHEDULES_QUERY,
        variables={"scheduleSelector": schedule_selector},
    )

    assert (
        start_result.data["startSchedule"]["scheduleState"]["status"]
        == InstigatorStatus.RUNNING.value
    )
