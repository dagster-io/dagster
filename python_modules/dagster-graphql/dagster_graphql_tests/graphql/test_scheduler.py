import datetime
import os
import sys
import time

import pytest
from dagster._core.remote_representation import InProcessCodeLocationOrigin, RemoteRepositoryOrigin
from dagster._core.remote_representation.external import CompoundID
from dagster._core.scheduler.instigation import (
    InstigatorState,
    InstigatorStatus,
    InstigatorType,
    ScheduleInstigatorData,
)
from dagster._core.test_utils import freeze_time
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster._time import create_datetime, get_timezone
from dagster._utils import Counter, traced_counter
from dagster_graphql.implementation.utils import UserFacingGraphQLError
from dagster_graphql.test.utils import (
    execute_dagster_graphql,
    infer_repository_selector,
    infer_schedule_selector,
    main_repo_location_name,
    main_repo_name,
)

from dagster_graphql_tests.graphql.graphql_context_test_suite import (
    ExecutingGraphQLContextTestMatrix,
    ReadonlyGraphQLContextTestMatrix,
)

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

GET_SCHEDULES_BY_STATUS_QUERY = """
query SchedulesByStatusQuery($repositorySelector: RepositorySelector!, $status: InstigationStatus) {
  schedulesOrError(repositorySelector: $repositorySelector, scheduleStatus: $status) {
    __typename
    ... on PythonError {
      message
      stack
    }
    ... on Schedules {
      results {
        name
        scheduleState {
          status
        }
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
      potentialTickTimestamps(startTimestamp: $ticksAfter, upperLimit: 3, lowerLimit: 3)
      scheduleState {
        id
        ticks {
          id
          timestamp
        }
        typeSpecificData {
          ... on ScheduleData {
            cronSchedule
          }
        }
      }
      assetSelection {
        assetSelectionString
        assetKeys {
          path
        }
        assets {
          key {
            path
          }
          definition {
            assetKey {
              path
            }
          }
        }
        assetsOrError {
          ... on AssetConnection {
            nodes {
              key {
                path
              }
            }
          }
          ... on PythonError {
            message
          }
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
      defaultStatus
      canReset
      scheduleState {
        id
        status
        hasStartPermission
        hasStopPermission
      }
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
    __typename
    ... on PythonError {
      message
      className
      stack
    }
    ... on ScheduleStateResult {
      scheduleState {
        id
        selectorId
        status
      }
    }
  }
}
"""


STOP_SCHEDULES_QUERY = """
mutation(
  $id: String
  $scheduleOriginId: String
  $scheduleSelectorId: String
) {
  stopRunningSchedule(
    id: $id
    scheduleOriginId: $scheduleOriginId,
    scheduleSelectorId: $scheduleSelectorId
  ) {
    __typename
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

RESET_SCHEDULES_QUERY = """
mutation(
  $scheduleSelector: ScheduleSelector!
) {
  resetSchedule(
    scheduleSelector: $scheduleSelector,
  ) {
    __typename
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

GET_SCHEDULE_TICKS_FROM_TIMESTAMP = """
query getSchedule($scheduleSelector: ScheduleSelector!, $startTimestamp: Float, $ticksAfter: Int, $ticksBefore: Int) {
  scheduleOrError(scheduleSelector: $scheduleSelector) {
    __typename
    ... on PythonError {
      message
      stack
    }
    ... on Schedule {
      name
      potentialTickTimestamps(startTimestamp: $startTimestamp, upperLimit: $ticksAfter, lowerLimit: $ticksBefore)
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
                    ticks(limit: 1) {
                      id
                      timestamp
                    }
                }
            }
        }
    }
}
"""

SCHEDULE_DRY_RUN_MUTATION = """
mutation($selectorData: ScheduleSelector!, $timestamp: Float) {
  scheduleDryRun(selectorData: $selectorData, timestamp: $timestamp) {
    __typename
    ... on PythonError {
      message
      stack
    }
    ... on DryRunInstigationTick {
      timestamp
      evaluationResult {
        runRequests {
          runConfigYaml
        }
        skipReason
        error {
          message
          stack
        }
      }
    }
    ... on ScheduleNotFoundError {
      scheduleName
    }
  }
}
"""


def default_execution_params():
    return {
        "selector": {"name": "no_config_job", "solidSelection": None},
        "mode": "default",
    }


def _get_unloadable_schedule_origin(name):
    working_directory = os.path.dirname(__file__)
    loadable_target_origin = LoadableTargetOrigin(
        executable_path=sys.executable,
        python_file=__file__,
        working_directory=working_directory,
    )
    return RemoteRepositoryOrigin(
        InProcessCodeLocationOrigin(loadable_target_origin), "fake_repository"
    ).get_instigator_origin(name)


@pytest.mark.parametrize("starting_case", ["on_tick_time", "offset_tick_time"])
def test_get_potential_ticks_starting_at_tick_time(graphql_context, starting_case):
    schedule_selector = infer_schedule_selector(graphql_context, "timezone_schedule")

    if starting_case == "on_tick_time":
        # Starting timestamp falls exactly on the timestamp of a tick
        start_timestamp = datetime.datetime(
            2019, 2, 27, tzinfo=get_timezone("US/Central")
        ).timestamp()
    else:
        # Starting timestamp is offset from tick times
        start_timestamp = datetime.datetime(
            2019, 2, 26, hour=1, tzinfo=get_timezone("US/Central")
        ).timestamp()

    result = execute_dagster_graphql(
        graphql_context,
        GET_SCHEDULE_TICKS_FROM_TIMESTAMP,
        variables={
            "scheduleSelector": schedule_selector,
            "ticksAfter": 3,
            "ticksBefore": 2,
            "startTimestamp": start_timestamp,
        },
    )
    assert result.data["scheduleOrError"]["__typename"] == "Schedule"
    assert result.data["scheduleOrError"]["name"] == "timezone_schedule"
    assert len(result.data["scheduleOrError"]["potentialTickTimestamps"]) == 5
    assert result.data["scheduleOrError"]["potentialTickTimestamps"] == [
        datetime.datetime(2019, 2, 25, tzinfo=get_timezone("US/Central")).timestamp(),
        datetime.datetime(2019, 2, 26, tzinfo=get_timezone("US/Central")).timestamp(),
        datetime.datetime(2019, 2, 27, tzinfo=get_timezone("US/Central")).timestamp(),
        datetime.datetime(2019, 2, 28, tzinfo=get_timezone("US/Central")).timestamp(),
        datetime.datetime(2019, 3, 1, tzinfo=get_timezone("US/Central")).timestamp(),
    ]


def test_jobless_asset_selection(graphql_context):
    schedule_name = "jobless_schedule"
    schedule_selector = infer_schedule_selector(graphql_context, schedule_name)

    result = execute_dagster_graphql(
        graphql_context, GET_SCHEDULE_QUERY, variables={"scheduleSelector": schedule_selector}
    )

    assert result.data
    assert result.data["scheduleOrError"]["__typename"] == "Schedule"
    assert result.data["scheduleOrError"]["assetSelection"]["assetSelectionString"] == "asset_one"
    assert result.data["scheduleOrError"]["assetSelection"]["assetKeys"] == [
        {"path": ["asset_one"]}
    ]
    assert result.data["scheduleOrError"]["assetSelection"]["assets"] == [
        {
            "key": {"path": ["asset_one"]},
            "definition": {"assetKey": {"path": ["asset_one"]}},
        }
    ]
    assert result.data["scheduleOrError"]["assetSelection"]["assetsOrError"]["nodes"] == [
        {
            "key": {"path": ["asset_one"]},
        }
    ]


def test_schedule_dry_run(graphql_context):
    context = graphql_context

    schedule_selector = infer_schedule_selector(context, "provide_config_schedule")

    timestamp = time.time()
    result = execute_dagster_graphql(
        context,
        SCHEDULE_DRY_RUN_MUTATION,
        variables={
            "selectorData": schedule_selector,
            "timestamp": timestamp,
        },
    )
    assert result.data
    assert result.data["scheduleDryRun"]["__typename"] == "DryRunInstigationTick"
    assert result.data["scheduleDryRun"]["timestamp"] == timestamp
    evaluation_result = result.data["scheduleDryRun"]["evaluationResult"]
    assert len(evaluation_result["runRequests"]) == 1
    assert "foo: bar" in evaluation_result["runRequests"][0]["runConfigYaml"]
    assert not evaluation_result["skipReason"]
    assert not evaluation_result["error"]


def test_schedule_dry_run_errors(graphql_context):
    context = graphql_context

    schedule_selector = infer_schedule_selector(context, "always_error")

    timestamp = time.time()
    result = execute_dagster_graphql(
        context,
        SCHEDULE_DRY_RUN_MUTATION,
        variables={
            "selectorData": schedule_selector,
            "timestamp": timestamp,
        },
    )
    assert result.data
    assert result.data["scheduleDryRun"]["__typename"] == "DryRunInstigationTick"
    assert result.data["scheduleDryRun"]["timestamp"] == timestamp
    evaluation_result = result.data["scheduleDryRun"]["evaluationResult"]
    assert not evaluation_result["runRequests"]
    assert not evaluation_result["skipReason"]
    assert (
        "Error occurred during the evaluation of schedule always_error"
        in evaluation_result["error"]["message"]
    )


def test_dry_run_nonexistent_schedule(graphql_context):
    context = graphql_context

    unknown_instigator_selector = infer_schedule_selector(context, "schedule_doesnt_exist")

    timestamp = time.time()
    with pytest.raises(UserFacingGraphQLError, match="GrapheneScheduleNotFoundError"):
        execute_dagster_graphql(
            context,
            SCHEDULE_DRY_RUN_MUTATION,
            variables={
                "selectorData": unknown_instigator_selector,
                "timestamp": timestamp,
            },
        )
    unknown_repo_selector = {**unknown_instigator_selector}
    unknown_repo_selector["repositoryName"] = "doesnt_exist"
    with pytest.raises(UserFacingGraphQLError, match="GrapheneRepositoryNotFoundError"):
        execute_dagster_graphql(
            context,
            SCHEDULE_DRY_RUN_MUTATION,
            variables={
                "selectorData": unknown_repo_selector,
                "timestamp": timestamp,
            },
        )
    unknown_repo_location_selector = {**unknown_instigator_selector}
    unknown_repo_location_selector["repositoryLocationName"] = "doesnt_exist"
    with pytest.raises(UserFacingGraphQLError, match="GrapheneRepositoryLocationNotFound"):
        execute_dagster_graphql(
            graphql_context,
            SCHEDULE_DRY_RUN_MUTATION,
            variables={
                "selectorData": unknown_repo_location_selector,
                "timestamp": timestamp,
            },
        )


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

    external_repository = graphql_context.get_code_location(
        main_repo_location_name()
    ).get_repository(main_repo_name())

    results = result.data["schedulesOrError"]["results"]
    assert len(results) == len(external_repository.get_external_schedules())

    for schedule in results:
        if schedule["name"] == "timezone_schedule":
            assert schedule["executionTimezone"] == "US/Central"


def test_get_filtered_schedule_definitions(graphql_context):
    selector = infer_repository_selector(graphql_context)
    result = execute_dagster_graphql(
        graphql_context,
        GET_SCHEDULES_BY_STATUS_QUERY,
        variables={"repositorySelector": selector, "status": "RUNNING"},
    )

    assert result.data
    assert result.data["schedulesOrError"]
    assert result.data["schedulesOrError"]["__typename"] == "Schedules"

    # running status includes automatically running schedules
    assert "running_in_code_schedule" in {
        schedule["name"] for schedule in result.data["schedulesOrError"]["results"]
    }

    result = execute_dagster_graphql(
        graphql_context,
        GET_SCHEDULES_BY_STATUS_QUERY,
        variables={"repositorySelector": selector, "status": "STOPPED"},
    )

    assert result.data
    assert result.data["schedulesOrError"]
    assert result.data["schedulesOrError"]["__typename"] == "Schedules"

    assert "running_in_code_schedule" not in {
        schedule["name"] for schedule in result.data["schedulesOrError"]["results"]
    }


def test_get_single_schedule_definition(graphql_context):
    context = graphql_context

    bad_selector = infer_schedule_selector(context, "does_not_exist")
    result = execute_dagster_graphql(
        context, GET_SCHEDULE_QUERY, variables={"scheduleSelector": bad_selector}
    )
    assert result.data
    assert result.data["scheduleOrError"]["__typename"] == "ScheduleNotFoundError"

    schedule_selector = infer_schedule_selector(context, "no_config_job_hourly_schedule")

    # fetch schedule before reconcile
    result = execute_dagster_graphql(
        context, GET_SCHEDULE_QUERY, variables={"scheduleSelector": schedule_selector}
    )
    assert result.data
    assert result.data["scheduleOrError"]["__typename"] == "Schedule"
    assert result.data["scheduleOrError"]["scheduleState"]
    assert result.data["scheduleOrError"]["executionTimezone"] == "UTC"

    future_ticks = result.data["scheduleOrError"]["futureTicks"]
    assert future_ticks
    assert len(future_ticks["results"]) == 3

    schedule_selector = infer_schedule_selector(context, "timezone_schedule")

    future_ticks_start_time = datetime.datetime(
        2019, 2, 27, tzinfo=get_timezone("US/Central")
    ).timestamp()

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
        datetime.datetime(2019, 2, 27, tzinfo=get_timezone("US/Central")).timestamp(),
        datetime.datetime(2019, 2, 28, tzinfo=get_timezone("US/Central")).timestamp(),
        datetime.datetime(2019, 3, 1, tzinfo=get_timezone("US/Central")).timestamp(),
    ]

    cursor = future_ticks["cursor"]

    assert future_ticks["cursor"] == (
        datetime.datetime(2019, 3, 1, tzinfo=get_timezone("US/Central")).timestamp() + 1
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
        datetime.datetime(2019, 3, 2, tzinfo=get_timezone("US/Central")).timestamp(),
        datetime.datetime(2019, 3, 3, tzinfo=get_timezone("US/Central")).timestamp(),
        datetime.datetime(2019, 3, 4, tzinfo=get_timezone("US/Central")).timestamp(),
    ]


def test_composite_cron_schedule_definition(graphql_context):
    schedule_selector = infer_schedule_selector(graphql_context, "composite_cron_schedule")
    result = execute_dagster_graphql(
        graphql_context,
        GET_SCHEDULE_QUERY,
        variables={"scheduleSelector": schedule_selector},
    )
    assert result.data
    assert result.data["scheduleOrError"]["__typename"] == "Schedule"
    assert result.data["scheduleOrError"]["scheduleState"]


def test_next_tick(graphql_context):
    schedule_selector = infer_schedule_selector(graphql_context, "no_config_job_hourly_schedule")

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


def test_ticks_from_timestamp(graphql_context):
    schedule_selector = infer_schedule_selector(graphql_context, "past_tick_schedule")

    # get schedule past ticks
    cur_timestamp = time.time()
    result = execute_dagster_graphql(
        graphql_context,
        GET_SCHEDULE_QUERY,
        variables={"scheduleSelector": schedule_selector, "ticksAfter": cur_timestamp},
    )

    ticks = result.data["scheduleOrError"]["potentialTickTimestamps"]
    assert len(ticks) == 6
    assert len([tick for tick in ticks if tick > cur_timestamp]) == 3
    assert len([tick for tick in ticks if tick <= cur_timestamp]) == 3


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


def test_unloadable_schedule(graphql_context):
    instance = graphql_context.instance
    initial_datetime = create_datetime(
        year=2019,
        month=2,
        day=27,
        hour=23,
        minute=59,
        second=59,
    )

    running_origin = _get_unloadable_schedule_origin("unloadable_running")
    running_instigator_state = InstigatorState(
        running_origin,
        InstigatorType.SCHEDULE,
        InstigatorStatus.RUNNING,
        ScheduleInstigatorData(
            "0 0 * * *",
            time.time(),
        ),
    )

    stopped_origin = _get_unloadable_schedule_origin("unloadable_stopped")

    with freeze_time(initial_datetime):
        instance.add_instigator_state(running_instigator_state)

        instance.add_instigator_state(
            InstigatorState(
                stopped_origin,
                InstigatorType.SCHEDULE,
                InstigatorStatus.STOPPED,
                ScheduleInstigatorData(
                    "0 0 * * *",
                    time.time(),
                ),
            )
        )

    # Verify that we can stop the unloadable schedule
    stop_result = execute_dagster_graphql(
        graphql_context,
        STOP_SCHEDULES_QUERY,
        variables={
            "scheduleOriginId": running_instigator_state.instigator_origin_id,
            "scheduleSelectorId": running_instigator_state.selector_id,
        },
    )
    assert (
        stop_result.data["stopRunningSchedule"]["scheduleState"]["status"]
        == InstigatorStatus.STOPPED.value
    )


def test_future_ticks_until(graphql_context):
    schedule_selector = infer_schedule_selector(graphql_context, "timezone_schedule")

    future_ticks_start_time = datetime.datetime(
        2019, 2, 27, tzinfo=get_timezone("US/Central")
    ).timestamp()

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

    future_ticks_start_time = datetime.datetime(
        2019, 2, 27, tzinfo=get_timezone("US/Central")
    ).timestamp()
    future_ticks_end_time = datetime.datetime(
        2019, 3, 2, tzinfo=get_timezone("US/Central")
    ).timestamp()

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
        datetime.datetime(2019, 2, 27, tzinfo=get_timezone("US/Central")).timestamp(),
        datetime.datetime(2019, 2, 28, tzinfo=get_timezone("US/Central")).timestamp(),
        datetime.datetime(2019, 3, 1, tzinfo=get_timezone("US/Central")).timestamp(),
    ]


def test_repository_batching(graphql_context):
    instance = graphql_context.instance
    if not instance.supports_batch_tick_queries:
        pytest.skip("storage cannot batch fetch")

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
    assert len(counts) == 3

    # We should have a single batch call to fetch instigator state, instead of separate calls for
    # each schedule (~18 distinct schedules in the repo)
    # 1) `get_batch_ticks` is fetched to grab ticks
    # 2) `all_instigator_state` is fetched to instantiate GrapheneSchedule
    assert counts.get("DagsterInstance.get_batch_ticks") == 1
    assert counts.get("DagsterInstance.all_instigator_state") == 1


class TestScheduleMutations(ExecutingGraphQLContextTestMatrix):
    def test_start_and_stop_schedule(self, graphql_context: WorkspaceRequestContext):
        schedule_selector = infer_schedule_selector(
            graphql_context, "no_config_job_hourly_schedule"
        )

        result = execute_dagster_graphql(
            graphql_context,
            GET_SCHEDULE_STATE_QUERY,
            variables={"scheduleSelector": schedule_selector},
        )

        assert result.data["scheduleOrError"]["defaultStatus"] == "STOPPED"

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

        schedule_id = start_result.data["startSchedule"]["scheduleState"]["id"]

        # Stop a single schedule
        stop_result = execute_dagster_graphql(
            graphql_context,
            STOP_SCHEDULES_QUERY,
            variables={
                "id": schedule_id,
            },
        )
        assert (
            stop_result.data["stopRunningSchedule"]["scheduleState"]["status"]
            == InstigatorStatus.STOPPED.value
        )

    def test_start_and_reset_schedule(self, graphql_context: WorkspaceRequestContext):
        schedule_selector = infer_schedule_selector(
            graphql_context, "no_config_job_hourly_schedule"
        )

        result = execute_dagster_graphql(
            graphql_context,
            GET_SCHEDULE_STATE_QUERY,
            variables={"scheduleSelector": schedule_selector},
        )

        assert result.data["scheduleOrError"]["defaultStatus"] == "STOPPED"
        assert result.data["scheduleOrError"]["canReset"] is False

        # Start a single schedule
        start_result = execute_dagster_graphql(
            graphql_context,
            START_SCHEDULES_QUERY,
            variables={"scheduleSelector": schedule_selector},
        )

        schedule_id = start_result.data["startSchedule"]["scheduleState"]["id"]
        cid = CompoundID.from_string(schedule_id)
        instigator_state = graphql_context.instance.get_instigator_state(
            cid.external_origin_id, cid.selector_id
        )

        assert instigator_state
        assert instigator_state.status == InstigatorStatus.RUNNING
        assert (
            start_result.data["startSchedule"]["scheduleState"]["status"]
            == InstigatorStatus.RUNNING.value
        )

        result = execute_dagster_graphql(
            graphql_context,
            GET_SCHEDULE_STATE_QUERY,
            variables={"scheduleSelector": schedule_selector},
        )

        assert result.data["scheduleOrError"]["canReset"] is True

        # Reset a single schedule
        stop_result = execute_dagster_graphql(
            graphql_context,
            RESET_SCHEDULES_QUERY,
            variables={"scheduleSelector": schedule_selector},
        )
        reset_instigator_state = graphql_context.instance.get_instigator_state(
            cid.external_origin_id, cid.selector_id
        )

        assert reset_instigator_state
        assert reset_instigator_state.status == InstigatorStatus.DECLARED_IN_CODE
        assert (
            stop_result.data["resetSchedule"]["scheduleState"]["status"]
            == InstigatorStatus.STOPPED.value
        )

        result = execute_dagster_graphql(
            graphql_context,
            GET_SCHEDULE_STATE_QUERY,
            variables={"scheduleSelector": schedule_selector},
        )

        assert result.data["scheduleOrError"]["canReset"] is False

    def test_start_schedule_with_default_status(self, graphql_context: WorkspaceRequestContext):
        schedule_selector = infer_schedule_selector(graphql_context, "running_in_code_schedule")

        result = execute_dagster_graphql(
            graphql_context,
            GET_SCHEDULE_STATE_QUERY,
            variables={"scheduleSelector": schedule_selector},
        )

        schedule_id = result.data["scheduleOrError"]["scheduleState"]["id"]

        assert result.data["scheduleOrError"]["defaultStatus"] == "RUNNING"
        assert result.data["scheduleOrError"]["canReset"] is False
        assert result.data["scheduleOrError"]["scheduleState"]["status"] == "RUNNING"

        assert result.data["scheduleOrError"]["scheduleState"]["hasStartPermission"] is True
        assert result.data["scheduleOrError"]["scheduleState"]["hasStopPermission"] is True

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

        # Stop a single schedule
        stop_result = execute_dagster_graphql(
            graphql_context,
            STOP_SCHEDULES_QUERY,
            variables={
                "id": schedule_id,
            },
        )
        assert (
            stop_result.data["stopRunningSchedule"]["scheduleState"]["status"]
            == InstigatorStatus.STOPPED.value
        )

        result = execute_dagster_graphql(
            graphql_context,
            GET_SCHEDULE_STATE_QUERY,
            variables={"scheduleSelector": schedule_selector},
        )

        assert result.data["scheduleOrError"]["canReset"] is True

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

        # Reset a single schedule
        reset_result = execute_dagster_graphql(
            graphql_context,
            RESET_SCHEDULES_QUERY,
            variables={"scheduleSelector": schedule_selector},
        )
        cid = CompoundID.from_string(schedule_id)
        reset_instigator_state = graphql_context.instance.get_instigator_state(
            cid.external_origin_id, cid.selector_id
        )

        assert reset_instigator_state
        assert reset_instigator_state.status == InstigatorStatus.DECLARED_IN_CODE
        assert (
            reset_result.data["resetSchedule"]["scheduleState"]["status"]
            == InstigatorStatus.RUNNING.value
        )

        result = execute_dagster_graphql(
            graphql_context,
            GET_SCHEDULE_STATE_QUERY,
            variables={"scheduleSelector": schedule_selector},
        )

        assert result.data["scheduleOrError"]["canReset"] is False


class TestSchedulePermissions(ReadonlyGraphQLContextTestMatrix):
    def test_start_schedule_failure(self, graphql_context):
        assert graphql_context.read_only is True

        schedule_selector = infer_schedule_selector(
            graphql_context, "no_config_job_hourly_schedule"
        )

        # Start a single schedule
        result = execute_dagster_graphql(
            graphql_context,
            START_SCHEDULES_QUERY,
            variables={"scheduleSelector": schedule_selector},
        )

        assert not result.errors
        assert result.data

        assert result.data["startSchedule"]["__typename"] == "UnauthorizedError"

    def test_stop_schedule_failure(self, graphql_context):
        schedule_selector = infer_schedule_selector(graphql_context, "running_in_code_schedule")

        result = execute_dagster_graphql(
            graphql_context,
            GET_SCHEDULE_STATE_QUERY,
            variables={"scheduleSelector": schedule_selector},
        )

        assert result.data["scheduleOrError"]["scheduleState"]["hasStartPermission"] is False
        assert result.data["scheduleOrError"]["scheduleState"]["hasStopPermission"] is False

        schedule_id = result.data["scheduleOrError"]["scheduleState"]["id"]

        stop_result = execute_dagster_graphql(
            graphql_context,
            STOP_SCHEDULES_QUERY,
            variables={
                "id": schedule_id,
            },
        )
        assert stop_result.data["stopRunningSchedule"]["__typename"] == "UnauthorizedError"
