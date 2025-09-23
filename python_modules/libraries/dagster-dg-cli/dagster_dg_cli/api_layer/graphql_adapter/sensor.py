"""GraphQL implementation for sensor operations."""

from typing import TYPE_CHECKING, Any, Optional

from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.sensor import DgApiSensor, DgApiSensorList

LIST_SENSORS_QUERY = """
query ListSensors($repositorySelector: RepositorySelector!) {
    sensorsOrError(repositorySelector: $repositorySelector) {
        __typename
        ... on Sensors {
            results {
                id
                name
                sensorState {
                    status
                }
                sensorType
                description
            }
        }
        ... on RepositoryNotFoundError {
            message
        }
        ... on PythonError {
            message
            stack
        }
    }
}
"""

LIST_REPOSITORIES_QUERY = """
query ListRepositories {
    repositoriesOrError {
        __typename
        ... on RepositoryConnection {
            nodes {
                name
                location {
                    name
                }
                sensors {
                    id
                    name
                    sensorState {
                        status
                    }
                    sensorType
                    description
                }
            }
        }
        ... on PythonError {
            message
            stack
        }
    }
}
"""

GET_SENSOR_QUERY = """
query GetSensor($sensorSelector: SensorSelector!) {
    sensorOrError(sensorSelector: $sensorSelector) {
        __typename
        ... on Sensor {
            id
            name
            sensorState {
                status
            }
            sensorType
            description
        }
        ... on SensorNotFoundError {
            message
        }
        ... on PythonError {
            message
            stack
        }
    }
}
"""


def process_repositories_response(graphql_response: dict[str, Any]) -> "DgApiSensorList":
    """Process GraphQL response from repositories query into DgApiSensorList."""
    from dagster_dg_cli.api_layer.schemas.sensor import (
        DgApiSensor,
        DgApiSensorList,
        DgApiSensorStatus,
        DgApiSensorType,
    )

    repositories_result = graphql_response.get("repositoriesOrError")
    if not repositories_result:
        raise Exception("No repositories data in GraphQL response")

    typename = repositories_result.get("__typename")
    if typename != "RepositoryConnection":
        error_msg = repositories_result.get("message", f"GraphQL error: {typename}")
        raise Exception(error_msg)

    repositories_data = repositories_result.get("nodes", [])

    sensors = []
    for repo in repositories_data:
        repo_name = repo.get("name", "")
        location_name = repo.get("location", {}).get("name", "")
        repository_origin = f"{location_name}@{repo_name}" if location_name and repo_name else None

        for s in repo.get("sensors", []):
            sensor_state = s.get("sensorState", {})
            status = sensor_state.get("status", "STOPPED")

            sensor = DgApiSensor(
                id=s["id"],
                name=s["name"],
                status=DgApiSensorStatus(status),
                sensor_type=DgApiSensorType(s.get("sensorType", "STANDARD")),
                description=s.get("description"),
                repository_origin=repository_origin,
                next_tick_timestamp=None,
            )
            sensors.append(sensor)

    return DgApiSensorList(
        items=sensors,
        total=len(sensors),
    )


def process_sensors_response(graphql_response: dict[str, Any]) -> "DgApiSensorList":
    """Process GraphQL response into DgApiSensorList.

    Args:
        graphql_response: Raw GraphQL response containing "sensorsOrError"

    Returns:
        DgApiSensorList: Processed sensor data
    """
    from dagster_dg_cli.api_layer.schemas.sensor import (
        DgApiSensor,
        DgApiSensorList,
        DgApiSensorStatus,
        DgApiSensorType,
    )

    sensors_result = graphql_response.get("sensorsOrError")
    if not sensors_result:
        raise Exception("No sensors data in GraphQL response")

    typename = sensors_result.get("__typename")
    if typename != "Sensors":
        error_msg = sensors_result.get("message", f"GraphQL error: {typename}")
        raise Exception(error_msg)

    sensors_data = sensors_result.get("results", [])

    sensors = []
    for s in sensors_data:
        sensor_state = s.get("sensorState", {})
        status = sensor_state.get("status", "STOPPED")

        sensor = DgApiSensor(
            id=s["id"],
            name=s["name"],
            status=DgApiSensorStatus(status),
            sensor_type=DgApiSensorType(s.get("sensorType", "STANDARD")),
            description=s.get("description"),
            repository_origin=None,
            next_tick_timestamp=None,
        )
        sensors.append(sensor)

    return DgApiSensorList(
        items=sensors,
        total=len(sensors),
    )


def process_sensor_response(graphql_response: dict[str, Any]) -> "DgApiSensor":
    """Process GraphQL response into DgApiSensor.

    Args:
        graphql_response: Raw GraphQL response containing "sensorOrError"

    Returns:
        DgApiSensor: Processed sensor data
    """
    from dagster_dg_cli.api_layer.schemas.sensor import (
        DgApiSensor,
        DgApiSensorStatus,
        DgApiSensorType,
    )

    sensor_result = graphql_response.get("sensorOrError")
    if not sensor_result:
        raise Exception("No sensor data in GraphQL response")

    typename = sensor_result.get("__typename")
    if typename != "Sensor":
        error_msg = sensor_result.get("message", f"GraphQL error: {typename}")
        raise Exception(error_msg)

    sensor_state = sensor_result.get("sensorState", {})
    status = sensor_state.get("status", "STOPPED")

    return DgApiSensor(
        id=sensor_result["id"],
        name=sensor_result["name"],
        status=DgApiSensorStatus(status),
        sensor_type=DgApiSensorType(sensor_result.get("sensorType", "STANDARD")),
        description=sensor_result.get("description"),
        repository_origin=None,
        next_tick_timestamp=None,
    )


def list_sensors_via_graphql(
    client: IGraphQLClient,
    repository_location_name: Optional[str] = None,
    repository_name: Optional[str] = None,
) -> "DgApiSensorList":
    """Fetch sensors using GraphQL."""
    if repository_location_name and repository_name:
        variables = {
            "repositorySelector": {
                "repositoryLocationName": repository_location_name,
                "repositoryName": repository_name,
            }
        }
        result = client.execute(LIST_SENSORS_QUERY, variables)
        return process_sensors_response(result)
    else:
        result = client.execute(LIST_REPOSITORIES_QUERY)
        return process_repositories_response(result)


def get_sensor_via_graphql(
    client: IGraphQLClient,
    sensor_name: str,
    repository_location_name: str,
    repository_name: str,
) -> "DgApiSensor":
    """Get single sensor via GraphQL."""
    variables = {
        "sensorSelector": {
            "sensorName": sensor_name,
            "repositoryLocationName": repository_location_name,
            "repositoryName": repository_name,
        }
    }

    try:
        result = client.execute(GET_SENSOR_QUERY, variables)
        if (
            result.get("data", {}).get("sensorOrError", {}).get("__typename")
            == "SensorNotFoundError"
        ):
            raise Exception(f"Sensor not found: {sensor_name}")
        return process_sensor_response(result)
    except Exception:
        raise


def get_sensor_by_name_via_graphql(client: IGraphQLClient, sensor_name: str) -> "DgApiSensor":
    """Get sensor by name, searching across all repositories."""
    result = client.execute(LIST_REPOSITORIES_QUERY)
    all_sensors = process_repositories_response(result)

    matching_sensors = [sensor for sensor in all_sensors.items if sensor.name == sensor_name]

    if not matching_sensors:
        raise Exception(f"Sensor not found: {sensor_name}")

    if len(matching_sensors) > 1:
        repo_origins = [sensor.repository_origin or "unknown" for sensor in matching_sensors]
        raise Exception(
            f"Multiple sensors found with name '{sensor_name}' in repositories: {', '.join(repo_origins)}"
        )

    return matching_sensors[0]
