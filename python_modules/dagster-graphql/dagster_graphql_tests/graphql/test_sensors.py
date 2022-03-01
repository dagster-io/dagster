import pendulum
from dagster_graphql.test.utils import (
    execute_dagster_graphql,
    infer_repository_selector,
    infer_sensor_selector,
    main_repo_location_name,
    main_repo_name,
)

from dagster.core.definitions.run_request import InstigatorType
from dagster.core.scheduler.instigation import InstigatorState, InstigatorStatus
from dagster.core.test_utils import create_test_daemon_workspace
from dagster.daemon import get_default_daemon_logger
from dagster.daemon.sensor import execute_sensor_iteration
from dagster.utils import Counter, traced_counter

from .graphql_context_test_suite import (
    ExecutingGraphQLContextTestMatrix,
    NonLaunchableGraphQLContextTestMatrix,
)

GET_SENSORS_QUERY = """
query SensorsQuery($repositorySelector: RepositorySelector!) {
  sensorsOrError(repositorySelector: $repositorySelector) {
    __typename
    ... on PythonError {
      message
      stack
    }
    ... on Sensors {
      results {
        name
        targets {
          pipelineName
          solidSelection
          mode
        }
        description
        minIntervalSeconds
        sensorState {
          status
          runs {
              id
              runId
          }
          runsCount
          ticks {
              id
              status
              timestamp
              runIds
              error {
                  message
                  stack
              }
              skipReason
          }
        }
      }
    }
  }
}
"""

GET_SENSOR_QUERY = """
query SensorQuery($sensorSelector: SensorSelector!) {
  sensorOrError(sensorSelector: $sensorSelector) {
    __typename
    ... on PythonError {
      message
      stack
    }
    ... on Sensor {
      name
      targets {
        pipelineName
        solidSelection
        mode
      }
      minIntervalSeconds
      nextTick {
        timestamp
      }
      sensorState {
        status
        runs {
          id
          runId
        }
        runsCount
        ticks {
            id
            status
            timestamp
            runIds
            error {
                message
                stack
            }
        }
      }
    }
  }
}
"""

GET_SENSOR_STATUS_QUERY = """
query SensorStateQuery($sensorSelector: SensorSelector!) {
  sensorOrError(sensorSelector: $sensorSelector) {
    __typename
    ... on Sensor {
      sensorState {
        id
        status
      }
    }
  }
}
"""


GET_SENSOR_TICK_RANGE_QUERY = """
query SensorQuery($sensorSelector: SensorSelector!, $dayRange: Int, $dayOffset: Int) {
  sensorOrError(sensorSelector: $sensorSelector) {
    __typename
    ... on PythonError {
      message
      stack
    }
    ... on Sensor {
      id
      sensorState {
        id
        ticks(dayRange: $dayRange, dayOffset: $dayOffset) {
          id
          timestamp
        }
      }
    }
  }
}
"""

START_SENSORS_QUERY = """
mutation($sensorSelector: SensorSelector!) {
  startSensor(sensorSelector: $sensorSelector) {
    ... on PythonError {
      message
      className
      stack
    }
    ... on Sensor {
      id
      jobOriginId
      sensorState {
        status
      }
    }
  }
}
"""

STOP_SENSORS_QUERY = """
mutation($jobOriginId: String!) {
  stopSensor(jobOriginId: $jobOriginId) {
    ... on PythonError {
      message
      className
      stack
    }
    ... on StopSensorMutationResult {
      instigationState {
        status
      }
    }
  }
}
"""

REPOSITORY_SENSORS_QUERY = """
query RepositorySensorsQuery($repositorySelector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $repositorySelector) {
        ... on Repository {
            id
            sensors {
                id
                name
                sensorState {
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


class TestSensors(NonLaunchableGraphQLContextTestMatrix):
    def test_get_sensors(self, graphql_context, snapshot):
        selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            GET_SENSORS_QUERY,
            variables={"repositorySelector": selector},
        )

        assert result.data
        assert result.data["sensorsOrError"]
        assert result.data["sensorsOrError"]["__typename"] == "Sensors"
        results = result.data["sensorsOrError"]["results"]
        snapshot.assert_match(results)

    def test_get_sensor(self, graphql_context, snapshot):
        sensor_selector = infer_sensor_selector(graphql_context, "always_no_config_sensor")
        result = execute_dagster_graphql(
            graphql_context,
            GET_SENSOR_QUERY,
            variables={"sensorSelector": sensor_selector},
        )

        assert result.data
        assert result.data["sensorOrError"]
        assert result.data["sensorOrError"]["__typename"] == "Sensor"
        sensor = result.data["sensorOrError"]
        snapshot.assert_match(sensor)


class TestSensorMutations(ExecutingGraphQLContextTestMatrix):
    def test_start_sensor(self, graphql_context):
        sensor_selector = infer_sensor_selector(graphql_context, "always_no_config_sensor")
        result = execute_dagster_graphql(
            graphql_context,
            START_SENSORS_QUERY,
            variables={"sensorSelector": sensor_selector},
        )
        assert result.data

        assert result.data["startSensor"]["sensorState"]["status"] == InstigatorStatus.RUNNING.value

    def test_stop_sensor(self, graphql_context):
        sensor_selector = infer_sensor_selector(graphql_context, "always_no_config_sensor")

        # start sensor
        start_result = execute_dagster_graphql(
            graphql_context,
            START_SENSORS_QUERY,
            variables={"sensorSelector": sensor_selector},
        )
        assert (
            start_result.data["startSensor"]["sensorState"]["status"]
            == InstigatorStatus.RUNNING.value
        )

        job_origin_id = start_result.data["startSensor"]["jobOriginId"]
        result = execute_dagster_graphql(
            graphql_context,
            STOP_SENSORS_QUERY,
            variables={"jobOriginId": job_origin_id},
        )
        assert result.data
        assert (
            result.data["stopSensor"]["instigationState"]["status"]
            == InstigatorStatus.STOPPED.value
        )

    def test_start_sensor_with_default_status(self, graphql_context):
        sensor_selector = infer_sensor_selector(graphql_context, "running_in_code_sensor")

        result = execute_dagster_graphql(
            graphql_context,
            GET_SENSOR_STATUS_QUERY,
            variables={"sensorSelector": sensor_selector},
        )

        assert result.data["sensorOrError"]["sensorState"]["status"] == "RUNNING"
        sensor_origin_id = result.data["sensorOrError"]["sensorState"]["id"]

        start_result = execute_dagster_graphql(
            graphql_context,
            START_SENSORS_QUERY,
            variables={"sensorSelector": sensor_selector},
        )

        assert (
            "You have attempted to start sensor running_in_code_sensor, but it is already running"
            in start_result.data["startSensor"]["message"]
        )

        stop_result = execute_dagster_graphql(
            graphql_context,
            STOP_SENSORS_QUERY,
            variables={"jobOriginId": sensor_origin_id},
        )

        assert stop_result.data["stopSensor"]["instigationState"]["status"] == "STOPPED"

        # Now can be restarted
        start_result = execute_dagster_graphql(
            graphql_context,
            START_SENSORS_QUERY,
            variables={"sensorSelector": sensor_selector},
        )

        assert start_result.data["startSensor"]["sensorState"]["status"] == "RUNNING"


def test_sensor_next_ticks(graphql_context):
    external_repository = graphql_context.get_repository_location(
        main_repo_location_name()
    ).get_repository(main_repo_name())

    sensor_name = "always_no_config_sensor"
    external_sensor = external_repository.get_external_sensor(sensor_name)
    sensor_selector = infer_sensor_selector(graphql_context, sensor_name)

    result = execute_dagster_graphql(
        graphql_context, GET_SENSOR_QUERY, variables={"sensorSelector": sensor_selector}
    )

    # test default sensor off
    assert result.data
    assert result.data["sensorOrError"]["__typename"] == "Sensor"
    next_tick = result.data["sensorOrError"]["nextTick"]
    assert not next_tick

    # test default sensor with no tick
    graphql_context.instance.add_instigator_state(
        InstigatorState(
            external_sensor.get_external_origin(), InstigatorType.SENSOR, InstigatorStatus.RUNNING
        )
    )
    result = execute_dagster_graphql(
        graphql_context, GET_SENSOR_QUERY, variables={"sensorSelector": sensor_selector}
    )
    assert result.data
    assert len(result.data["sensorOrError"]["sensorState"]["ticks"]) == 0
    assert result.data["sensorOrError"]["__typename"] == "Sensor"
    next_tick = result.data["sensorOrError"]["nextTick"]
    assert not next_tick

    # test default sensor with last tick
    _create_tick(graphql_context)

    result = execute_dagster_graphql(
        graphql_context, GET_SENSOR_QUERY, variables={"sensorSelector": sensor_selector}
    )
    assert len(result.data["sensorOrError"]["sensorState"]["ticks"]) == 1
    assert result.data
    assert result.data["sensorOrError"]["__typename"] == "Sensor"
    next_tick = result.data["sensorOrError"]["nextTick"]
    assert next_tick


def _create_tick(graphql_context):
    with create_test_daemon_workspace(
        graphql_context.process_context.workspace_load_target
    ) as workspace:
        list(
            execute_sensor_iteration(
                graphql_context.instance, get_default_daemon_logger("SensorDaemon"), workspace
            )
        )


def test_sensor_tick_range(graphql_context):
    external_repository = graphql_context.get_repository_location(
        main_repo_location_name()
    ).get_repository(main_repo_name())

    sensor_name = "always_no_config_sensor"
    external_sensor = external_repository.get_external_sensor(sensor_name)
    sensor_selector = infer_sensor_selector(graphql_context, sensor_name)

    # test with no job state
    result = execute_dagster_graphql(
        graphql_context,
        GET_SENSOR_TICK_RANGE_QUERY,
        variables={"sensorSelector": sensor_selector, "dayRange": None, "dayOffset": None},
    )
    assert len(result.data["sensorOrError"]["sensorState"]["ticks"]) == 0

    # turn the sensor on
    graphql_context.instance.add_instigator_state(
        InstigatorState(
            external_sensor.get_external_origin(), InstigatorType.SENSOR, InstigatorStatus.RUNNING
        )
    )

    now = pendulum.now("US/Central")
    one = now.subtract(days=2).subtract(hours=1)
    with pendulum.test(one):
        _create_tick(graphql_context)

    two = now.subtract(days=1).subtract(hours=1)
    with pendulum.test(two):
        _create_tick(graphql_context)

    three = now.subtract(hours=1)
    with pendulum.test(three):
        _create_tick(graphql_context)

    result = execute_dagster_graphql(
        graphql_context,
        GET_SENSOR_TICK_RANGE_QUERY,
        variables={"sensorSelector": sensor_selector, "dayRange": None, "dayOffset": None},
    )
    assert len(result.data["sensorOrError"]["sensorState"]["ticks"]) == 3

    result = execute_dagster_graphql(
        graphql_context,
        GET_SENSOR_TICK_RANGE_QUERY,
        variables={"sensorSelector": sensor_selector, "dayRange": 1, "dayOffset": None},
    )
    assert len(result.data["sensorOrError"]["sensorState"]["ticks"]) == 1
    assert result.data["sensorOrError"]["sensorState"]["ticks"][0]["timestamp"] == three.timestamp()

    result = execute_dagster_graphql(
        graphql_context,
        GET_SENSOR_TICK_RANGE_QUERY,
        variables={"sensorSelector": sensor_selector, "dayRange": 1, "dayOffset": 1},
    )
    assert len(result.data["sensorOrError"]["sensorState"]["ticks"]) == 1
    assert result.data["sensorOrError"]["sensorState"]["ticks"][0]["timestamp"] == two.timestamp()

    result = execute_dagster_graphql(
        graphql_context,
        GET_SENSOR_TICK_RANGE_QUERY,
        variables={
            "sensorSelector": sensor_selector,
            "dayRange": 2,
            "dayOffset": None,
        },
    )
    assert len(result.data["sensorOrError"]["sensorState"]["ticks"]) == 2


def test_repository_batching(graphql_context):
    traced_counter.set(Counter())
    selector = infer_repository_selector(graphql_context)
    result = execute_dagster_graphql(
        graphql_context,
        REPOSITORY_SENSORS_QUERY,
        variables={"repositorySelector": selector},
    )
    assert result.data
    assert "repositoryOrError" in result.data
    assert "sensors" in result.data["repositoryOrError"]
    counter = traced_counter.get()
    counts = counter.counts()
    assert counts
    assert len(counts) == 2

    # We should have a single batch call to fetch run records (to fetch sensor runs) and a single
    # batch call to fetch instigator state, instead of separate calls for each sensor (~5 distinct
    # sensors in the repo)
    # 1) `get_run_records` is fetched to instantiate GrapheneRun
    # 2) `all_instigator_state` is fetched to instantiate GrapheneSensor
    assert counts.get("DagsterInstance.get_run_records") == 1
    assert counts.get("DagsterInstance.all_instigator_state") == 1
