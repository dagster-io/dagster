import os

import pendulum
import yaml
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.host_representation import (
    ExternalRepositoryOrigin,
    InProcessRepositoryLocationOrigin,
)
from dagster.core.scheduler.job import JobState, JobStatus, JobType, ScheduleJobData
from dagster_graphql.test.utils import (
    execute_dagster_graphql,
    infer_repository_selector,
    infer_schedule_selector,
    main_repo_location_name,
    main_repo_name,
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

GET_UNLOADABLE_QUERY = """
query getUnloadableSchedules {
  unloadableJobStatesOrError(jobType: SCHEDULE) {
    ... on JobStates {
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


def default_execution_params():
    return {
        "runConfigData": {"intermediate_storage": {"filesystem": None}},
        "selector": {"name": "no_config_pipeline", "solidSelection": None},
        "mode": "default",
    }


def _get_unloadable_schedule_origin(job_name):
    working_directory = os.path.dirname(__file__)
    recon_repo = ReconstructableRepository.for_file(__file__, "doesnt_exist", working_directory)
    return ExternalRepositoryOrigin(
        InProcessRepositoryLocationOrigin(recon_repo), "fake_repository"
    ).get_job_origin(job_name)


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
    external_repository = graphql_context.get_repository_location(
        main_repo_location_name()
    ).get_repository(main_repo_name())
    graphql_context.instance.reconcile_scheduler_state(external_repository)

    schedule_selector = infer_schedule_selector(
        graphql_context, "no_config_pipeline_hourly_schedule"
    )

    # Start a single schedule
    start_result = execute_dagster_graphql(
        graphql_context,
        START_SCHEDULES_QUERY,
        variables={"scheduleSelector": schedule_selector},
    )
    assert start_result.data["startSchedule"]["scheduleState"]["status"] == JobStatus.RUNNING.value

    schedule_origin_id = start_result.data["startSchedule"]["scheduleState"]["id"]

    # Stop a single schedule
    stop_result = execute_dagster_graphql(
        graphql_context,
        STOP_SCHEDULES_QUERY,
        variables={"scheduleOriginId": schedule_origin_id},
    )
    assert (
        stop_result.data["stopRunningSchedule"]["scheduleState"]["status"]
        == JobStatus.STOPPED.value
    )


def test_get_single_schedule_definition(graphql_context):
    context = graphql_context
    instance = context.instance

    schedule_selector = infer_schedule_selector(context, "partition_based_multi_mode_decorator")

    # fetch schedule before reconcile
    result = execute_dagster_graphql(
        context, GET_SCHEDULE_QUERY, variables={"scheduleSelector": schedule_selector}
    )
    assert result.data
    assert result.data["scheduleOrError"]["__typename"] == "Schedule"
    assert result.data["scheduleOrError"]["scheduleState"]

    instance.reconcile_scheduler_state(
        external_repository=context.get_repository_location(
            main_repo_location_name()
        ).get_repository(main_repo_name()),
    )

    result = execute_dagster_graphql(
        context, GET_SCHEDULE_QUERY, variables={"scheduleSelector": schedule_selector}
    )

    assert result.data

    assert result.data["scheduleOrError"]["__typename"] == "Schedule"
    assert result.data["scheduleOrError"]["partitionSet"]
    assert result.data["scheduleOrError"]["executionTimezone"] == pendulum.now().timezone.name

    future_ticks = result.data["scheduleOrError"]["futureTicks"]
    assert future_ticks
    assert len(future_ticks["results"]) == 3

    schedule_selector = infer_schedule_selector(context, "timezone_schedule")

    future_ticks_start_time = pendulum.create(2019, 2, 27, tz="US/Central").timestamp()

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
        pendulum.create(2019, 2, 27, tz="US/Central").timestamp(),
        pendulum.create(2019, 2, 28, tz="US/Central").timestamp(),
        pendulum.create(2019, 3, 1, tz="US/Central").timestamp(),
    ]

    cursor = future_ticks["cursor"]

    assert future_ticks["cursor"] == (pendulum.create(2019, 3, 1, tz="US/Central").timestamp() + 1)

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
        pendulum.create(2019, 3, 2, tz="US/Central").timestamp(),
        pendulum.create(2019, 3, 3, tz="US/Central").timestamp(),
        pendulum.create(2019, 3, 4, tz="US/Central").timestamp(),
    ]


def test_next_tick(graphql_context):
    external_repository = graphql_context.get_repository_location(
        main_repo_location_name()
    ).get_repository(main_repo_name())
    graphql_context.instance.reconcile_scheduler_state(external_repository)

    schedule_selector = infer_schedule_selector(
        graphql_context, "no_config_pipeline_hourly_schedule"
    )

    # Start a single schedule, future tick run requests only available for running schedules
    start_result = execute_dagster_graphql(
        graphql_context,
        START_SCHEDULES_QUERY,
        variables={"scheduleSelector": schedule_selector},
    )
    assert start_result.data["startSchedule"]["scheduleState"]["status"] == JobStatus.RUNNING.value

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
        assert tick["evaluationResult"]["runRequests"][0]["runConfigYaml"] == yaml.dump(
            {"intermediate_storage": {"filesystem": {}}},
            default_flow_style=False,
            allow_unicode=True,
        )


def test_next_tick_bad_schedule(graphql_context):
    external_repository = graphql_context.get_repository_location(
        main_repo_location_name()
    ).get_repository(main_repo_name())
    graphql_context.instance.reconcile_scheduler_state(external_repository)

    schedule_selector = infer_schedule_selector(graphql_context, "run_config_error_schedule")

    # Start a single schedule, future tick run requests only available for running schedules
    start_result = execute_dagster_graphql(
        graphql_context,
        START_SCHEDULES_QUERY,
        variables={"scheduleSelector": schedule_selector},
    )
    assert start_result.data["startSchedule"]["scheduleState"]["status"] == JobStatus.RUNNING.value

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
    initial_datetime = pendulum.datetime(
        year=2019,
        month=2,
        day=27,
        hour=23,
        minute=59,
        second=59,
    )
    with pendulum.test(initial_datetime):
        instance.add_job_state(
            JobState(
                _get_unloadable_schedule_origin("unloadable_running"),
                JobType.SCHEDULE,
                JobStatus.RUNNING,
                ScheduleJobData(
                    "0 0 * * *",
                    pendulum.now("UTC").timestamp(),
                    graphql_context.instance.scheduler.__class__.__name__,
                ),
            )
        )

        instance.add_job_state(
            JobState(
                _get_unloadable_schedule_origin("unloadable_stopped"),
                JobType.SCHEDULE,
                JobStatus.STOPPED,
                ScheduleJobData(
                    "0 0 * * *",
                    pendulum.now("UTC").timestamp(),
                    graphql_context.instance.scheduler.__class__.__name__,
                ),
            )
        )

    result = execute_dagster_graphql(graphql_context, GET_UNLOADABLE_QUERY)
    assert len(result.data["unloadableJobStatesOrError"]["results"]) == 1
    assert result.data["unloadableJobStatesOrError"]["results"][0]["name"] == "unloadable_running"
