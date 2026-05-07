from dataclasses import dataclass
from typing import TYPE_CHECKING

from typing_extensions import assert_never

from dagster_rest_resources.__generated__.input_types import RepositorySelector, ScheduleSelector
from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.exception import DagsterPlusGraphqlError
from dagster_rest_resources.schemas.schedule import DgApiSchedule, DgApiScheduleList

if TYPE_CHECKING:
    from dagster_rest_resources.__generated__.get_schedule import GetScheduleScheduleOrErrorSchedule
    from dagster_rest_resources.__generated__.list_repositories_with_schedules import (
        ListRepositoriesWithSchedulesRepositoriesOrErrorRepositoryConnectionNodesSchedules,
    )
    from dagster_rest_resources.__generated__.list_schedules import (
        ListSchedulesSchedulesOrErrorSchedulesResults,
    )


@dataclass(frozen=True)
class DgApiScheduleApi:
    _client: IGraphQLClient

    def list_schedules(
        self,
        repository_location_name: str | None = None,
        repository_name: str | None = None,
    ) -> DgApiScheduleList:
        if repository_location_name and repository_name:
            result = self._client.list_schedules(
                repository_selector=RepositorySelector(
                    repositoryLocationName=repository_location_name,
                    repositoryName=repository_name,
                )
            ).schedules_or_error

            match result.typename__:
                case "Schedules":
                    items = [
                        self._build_schedule(
                            s,
                            repo_location_name=repository_location_name,
                            repo_name=repository_name,
                        )
                        for s in result.results  # ty: ignore[unresolved-attribute]
                    ]
                    return DgApiScheduleList(items=items)
                case "RepositoryNotFoundError":
                    raise DagsterPlusGraphqlError(f"Error listing schedules: {result.message}")  # ty: ignore[unresolved-attribute]
                case "PythonError":
                    raise DagsterPlusGraphqlError(f"Error listing schedules: {result.message}")  # ty: ignore[unresolved-attribute]
                case _ as unreachable:
                    assert_never(unreachable)
        else:
            result = self._client.list_repositories_with_schedules().repositories_or_error

            match result.typename__:
                case "RepositoryConnection":
                    items = []
                    for repo in result.nodes:  # ty: ignore[unresolved-attribute]
                        for s in repo.schedules:
                            items.append(
                                self._build_schedule(
                                    s,
                                    repo_location_name=repo.location.name,
                                    repo_name=repo.name,
                                )
                            )
                    return DgApiScheduleList(items=items)
                case "RepositoryNotFoundError":
                    raise DagsterPlusGraphqlError(f"Error listing schedules: {result.message}")  # ty: ignore[unresolved-attribute]
                case "PythonError":
                    raise DagsterPlusGraphqlError(f"Error listing schedules: {result.message}")  # ty: ignore[unresolved-attribute]
                case _ as unreachable:
                    assert_never(unreachable)

    def get_schedule(
        self,
        schedule_name: str,
        repository_location_name: str,
        repository_name: str,
    ) -> DgApiSchedule:
        result = self._client.get_schedule(
            schedule_selector=ScheduleSelector(
                repositoryLocationName=repository_location_name,
                repositoryName=repository_name,
                scheduleName=schedule_name,
            )
        ).schedule_or_error

        match result.typename__:
            case "Schedule":
                return self._build_schedule(
                    result,  # ty: ignore[invalid-argument-type]
                    repo_location_name=repository_location_name,
                    repo_name=repository_name,
                )
            case "ScheduleNotFoundError":
                raise DagsterPlusGraphqlError(f"Error fetching schedule: {result.message}")  # ty: ignore[unresolved-attribute]
            case "PythonError":
                raise DagsterPlusGraphqlError(f"Error fetching schedule: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)

    def get_schedule_by_name(self, schedule_name: str) -> DgApiSchedule:
        result = self._client.list_repositories_with_schedules().repositories_or_error

        match result.typename__:
            case "RepositoryConnection":
                matches: list[DgApiSchedule] = []
                for repo in result.nodes:  # ty: ignore[unresolved-attribute]
                    for s in repo.schedules:
                        if s.name == schedule_name:
                            matches.append(
                                self._build_schedule(
                                    s,
                                    repo_location_name=repo.location.name,
                                    repo_name=repo.name,
                                )
                            )
                if not matches:
                    raise DagsterPlusGraphqlError(f"Schedule not found: {schedule_name}")
                if len(matches) > 1:
                    origins = [s.code_location_origin for s in matches]
                    raise DagsterPlusGraphqlError(
                        f"Multiple schedules found with name '{schedule_name}' in code locations: {', '.join(origins)}"
                    )

                return matches[0]
            case "RepositoryNotFoundError":
                raise DagsterPlusGraphqlError(f"Error listing repositories: {result.message}")  # ty: ignore[unresolved-attribute]
            case "PythonError":
                raise DagsterPlusGraphqlError(f"Error listing repositories: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)

    def _build_schedule(
        self,
        schedule: """GetScheduleScheduleOrErrorSchedule
        | ListRepositoriesWithSchedulesRepositoriesOrErrorRepositoryConnectionNodesSchedules
        | ListSchedulesSchedulesOrErrorSchedulesResults""",
        *,
        repo_location_name: str,
        repo_name: str,
    ) -> DgApiSchedule:
        return DgApiSchedule(
            id=schedule.id,
            name=schedule.name,
            status=schedule.schedule_state.status,
            cron_schedule=schedule.cron_schedule,
            pipeline_name=schedule.pipeline_name,
            code_location_origin=f"{repo_location_name}@{repo_name}",
            description=schedule.description,
            execution_timezone=schedule.execution_timezone,
            next_tick_timestamp=None,
        )
