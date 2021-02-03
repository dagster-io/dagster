import pendulum
from dagster.core.definitions.job import JobType
from dagster.core.scheduler.job import JobState, JobStatus
from dagster.daemon import get_default_daemon_logger
from dagster.scheduler.sensor import execute_sensor_iteration
from dagster_graphql.test.utils import (
    execute_dagster_graphql,
    infer_repository_selector,
    infer_sensor_selector,
    main_repo_location_name,
    main_repo_name,
)

from .graphql_context_test_suite import (
    ExecutingGraphQLContextTestMatrix,
    ReadonlyGraphQLContextTestMatrix,
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
        id
        name
        pipelineName
        solidSelection
        mode
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
      id
      name
      pipelineName
      solidSelection
      mode
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
      jobState {
        status
      }
    }
  }
}
"""


class TestSensors(ReadonlyGraphQLContextTestMatrix):
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

        assert result.data["startSensor"]["sensorState"]["status"] == JobStatus.RUNNING.value

    def test_stop_sensor(self, graphql_context):
        sensor_selector = infer_sensor_selector(graphql_context, "always_no_config_sensor")

        # start sensor
        start_result = execute_dagster_graphql(
            graphql_context,
            START_SENSORS_QUERY,
            variables={"sensorSelector": sensor_selector},
        )
        assert start_result.data["startSensor"]["sensorState"]["status"] == JobStatus.RUNNING.value

        job_origin_id = start_result.data["startSensor"]["jobOriginId"]
        result = execute_dagster_graphql(
            graphql_context,
            STOP_SENSORS_QUERY,
            variables={"jobOriginId": job_origin_id},
        )
        assert result.data
        assert result.data["stopSensor"]["jobState"]["status"] == JobStatus.STOPPED.value


def test_sensor_next_ticks(graphql_context):
    external_repository = graphql_context.get_repository_location(
        main_repo_location_name()
    ).get_repository(main_repo_name())
    graphql_context.instance.reconcile_scheduler_state(external_repository)

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
    graphql_context.instance.add_job_state(
        JobState(external_sensor.get_external_origin(), JobType.SENSOR, JobStatus.RUNNING)
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
    list(
        execute_sensor_iteration(
            graphql_context.instance, get_default_daemon_logger("SensorDaemon")
        )
    )
    result = execute_dagster_graphql(
        graphql_context, GET_SENSOR_QUERY, variables={"sensorSelector": sensor_selector}
    )
    assert len(result.data["sensorOrError"]["sensorState"]["ticks"]) == 1
    assert result.data
    assert result.data["sensorOrError"]["__typename"] == "Sensor"
    next_tick = result.data["sensorOrError"]["nextTick"]
    assert next_tick


def _create_tick(instance):
    list(execute_sensor_iteration(instance, get_default_daemon_logger("SensorDaemon")))


def test_sensor_tick_range(graphql_context):
    external_repository = graphql_context.get_repository_location(
        main_repo_location_name()
    ).get_repository(main_repo_name())
    graphql_context.instance.reconcile_scheduler_state(external_repository)

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
    graphql_context.instance.add_job_state(
        JobState(external_sensor.get_external_origin(), JobType.SENSOR, JobStatus.RUNNING)
    )

    now = pendulum.now().in_tz("US/Central")
    one = now.subtract(days=2).subtract(hours=1)
    with pendulum.test(one):
        _create_tick(graphql_context.instance)

    two = now.subtract(days=1).subtract(hours=1)
    with pendulum.test(two):
        _create_tick(graphql_context.instance)

    three = now.subtract(hours=1)
    with pendulum.test(three):
        _create_tick(graphql_context.instance)

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
