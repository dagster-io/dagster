from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from typing_extensions import assert_never

from dagster_rest_resources.__generated__.enums import InstigationTickStatus
from dagster_rest_resources.__generated__.input_types import ScheduleSelector, SensorSelector
from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.exception import (
    DagsterPlusGraphqlError,
    DagsterPlusUnauthorizedError,
)
from dagster_rest_resources.schemas.tick import DgApiTick, DgApiTickList

if TYPE_CHECKING:
    from dagster_rest_resources.__generated__.get_schedule_ticks import (
        GetScheduleTicksScheduleOrErrorScheduleScheduleStateTicks,
    )
    from dagster_rest_resources.__generated__.get_sensor_ticks import (
        GetSensorTicksSensorOrErrorSensorSensorStateTicks,
    )


@dataclass(frozen=True)
class DgApiTickApi:
    _client: IGraphQLClient

    def get_sensor_ticks(
        self,
        *,
        sensor_name: str,
        limit: int = 25,
        cursor: str | None = None,
        statuses: list[InstigationTickStatus] | None = None,
        before_timestamp: float | None = None,
        after_timestamp: float | None = None,
    ) -> DgApiTickList:
        location_name, repo_name = self._find_repo_info(sensor_name, "sensor")
        result = self._client.get_sensor_ticks(
            sensor_selector=SensorSelector(
                repositoryLocationName=location_name,
                repositoryName=repo_name,
                sensorName=sensor_name,
            ),
            limit=limit,
            cursor=cursor,
            statuses=statuses,
            before_timestamp=before_timestamp,
            after_timestamp=after_timestamp,
        ).sensor_or_error

        match result.typename__:
            case "Sensor":
                return self._build_tick_list(result.sensor_state.ticks)  # ty: ignore[unresolved-attribute]
            case "SensorNotFoundError":
                raise DagsterPlusGraphqlError(f"Sensor not found: {result.message}")  # ty: ignore[unresolved-attribute]
            case "UnauthorizedError":
                raise DagsterPlusUnauthorizedError(f"Error fetching sensor ticks: {result.message}")  # ty: ignore[unresolved-attribute]
            case "PythonError":
                raise DagsterPlusGraphqlError(f"Error fetching sensor ticks: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)

    def get_schedule_ticks(
        self,
        *,
        schedule_name: str,
        limit: int = 25,
        cursor: str | None = None,
        statuses: list[InstigationTickStatus] | None = None,
        before_timestamp: float | None = None,
        after_timestamp: float | None = None,
    ) -> DgApiTickList:
        location_name, repo_name = self._find_repo_info(schedule_name, "schedule")
        result = self._client.get_schedule_ticks(
            schedule_selector=ScheduleSelector(
                repositoryLocationName=location_name,
                repositoryName=repo_name,
                scheduleName=schedule_name,
            ),
            limit=limit,
            cursor=cursor,
            statuses=statuses,
            before_timestamp=before_timestamp,
            after_timestamp=after_timestamp,
        ).schedule_or_error

        match result.typename__:
            case "Schedule":
                return self._build_tick_list(result.schedule_state.ticks)  # ty: ignore[unresolved-attribute]
            case "ScheduleNotFoundError":
                raise DagsterPlusGraphqlError(f"Error fetching schedule ticks: {result.message}")  # ty: ignore[unresolved-attribute]
            case "PythonError":
                raise DagsterPlusGraphqlError(f"Error fetching schedule ticks: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)

    def _find_repo_info(
        self, name: str, entity_type: Literal["sensor", "schedule"]
    ) -> tuple[str, str]:
        result = self._client.list_repositories_for_ticks().repositories_or_error
        match result.typename__:
            case "RepositoryConnection":
                matches: list[tuple[str, str]] = []
                for repo in result.nodes:  # ty: ignore[unresolved-attribute]
                    entities = repo.sensors if entity_type == "sensor" else repo.schedules
                    for entity in entities:
                        if entity.name == name:
                            matches.append((repo.location.name, repo.name))
                if not matches:
                    raise DagsterPlusGraphqlError(f"{entity_type.capitalize()} not found: {name}")
                if len(matches) > 1:
                    origins = [f"{loc}@{rn}" for loc, rn in matches]
                    raise DagsterPlusGraphqlError(
                        f"Multiple {entity_type}s with name '{name}': {', '.join(origins)}"
                    )

                return matches[0]
            case "RepositoryNotFoundError":
                raise DagsterPlusGraphqlError(f"Error listing repositories: {result.message}")  # ty: ignore[unresolved-attribute]
            case "PythonError":
                raise DagsterPlusGraphqlError(f"Error listing repositories: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)

    def _build_tick_list(
        self,
        raw_ticks: """list[GetSensorTicksSensorOrErrorSensorSensorStateTicks]
        | list[GetScheduleTicksScheduleOrErrorScheduleScheduleStateTicks]""",
    ) -> DgApiTickList:
        items = [DgApiTick.model_validate(t, from_attributes=True) for t in raw_ticks]
        return DgApiTickList(
            items=items,
            total=len(items),
            cursor=items[-1].id if items else None,
        )
