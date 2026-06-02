from unittest.mock import Mock

import pytest
from dagster_rest_resources.__generated__.enums import InstigationStatus
from dagster_rest_resources.__generated__.get_schedule import (
    GetSchedule,
    GetScheduleScheduleOrErrorPythonError,
    GetScheduleScheduleOrErrorSchedule,
    GetScheduleScheduleOrErrorScheduleNotFoundError,
    GetScheduleScheduleOrErrorScheduleScheduleState,
)
from dagster_rest_resources.__generated__.input_types import RepositorySelector, ScheduleSelector
from dagster_rest_resources.__generated__.list_repositories_with_schedules import (
    ListRepositoriesWithSchedules,
    ListRepositoriesWithSchedulesRepositoriesOrErrorPythonError,
    ListRepositoriesWithSchedulesRepositoriesOrErrorRepositoryConnection,
    ListRepositoriesWithSchedulesRepositoriesOrErrorRepositoryConnectionNodes,
    ListRepositoriesWithSchedulesRepositoriesOrErrorRepositoryConnectionNodesLocation,
    ListRepositoriesWithSchedulesRepositoriesOrErrorRepositoryConnectionNodesSchedules,
    ListRepositoriesWithSchedulesRepositoriesOrErrorRepositoryConnectionNodesSchedulesScheduleState,
    ListRepositoriesWithSchedulesRepositoriesOrErrorRepositoryNotFoundError,
)
from dagster_rest_resources.__generated__.list_schedules import (
    ListSchedules,
    ListSchedulesSchedulesOrErrorPythonError,
    ListSchedulesSchedulesOrErrorRepositoryNotFoundError,
    ListSchedulesSchedulesOrErrorSchedules,
    ListSchedulesSchedulesOrErrorSchedulesResults,
    ListSchedulesSchedulesOrErrorSchedulesResultsScheduleState,
)
from dagster_rest_resources.api.schedule import DgApiScheduleApi
from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.exception import DagsterPlusGraphqlError
from dagster_rest_resources.schemas.schedule import DgApiScheduleList


def _make_schedule_result(
    name: str = "test_schedule",
    schedule_id: str = "test-schedule-id",
    status: InstigationStatus = InstigationStatus.RUNNING,
    cron_schedule: str = "0 0 * * *",
    pipeline_name: str = "test_pipeline",
    description: str | None = None,
    execution_timezone: str | None = None,
) -> ListSchedulesSchedulesOrErrorSchedulesResults:
    return ListSchedulesSchedulesOrErrorSchedulesResults(
        id=schedule_id,
        name=name,
        cronSchedule=cron_schedule,
        pipelineName=pipeline_name,
        description=description,
        executionTimezone=execution_timezone,
        scheduleState=ListSchedulesSchedulesOrErrorSchedulesResultsScheduleState(
            status=status,
        ),
    )


def _make_repos_with_schedules(
    schedules: list[tuple[str, str]] | None = None,
) -> ListRepositoriesWithSchedules:
    """schedules: list of (schedule_name, schedule_id) tuples."""
    return ListRepositoriesWithSchedules(
        repositoriesOrError=ListRepositoriesWithSchedulesRepositoriesOrErrorRepositoryConnection(
            __typename="RepositoryConnection",
            nodes=[
                ListRepositoriesWithSchedulesRepositoriesOrErrorRepositoryConnectionNodes(
                    name="__repository__",
                    location=ListRepositoriesWithSchedulesRepositoriesOrErrorRepositoryConnectionNodesLocation(
                        name="test_location"
                    ),
                    schedules=[
                        ListRepositoriesWithSchedulesRepositoriesOrErrorRepositoryConnectionNodesSchedules(
                            id=sid,
                            name=sname,
                            cronSchedule="0 0 * * *",
                            pipelineName="test_pipeline",
                            description=None,
                            executionTimezone=None,
                            scheduleState=ListRepositoriesWithSchedulesRepositoriesOrErrorRepositoryConnectionNodesSchedulesScheduleState(
                                status=InstigationStatus.RUNNING,
                            ),
                        )
                        for sname, sid in (schedules or [])
                    ],
                )
            ],
        )
    )


class TestListSchedulesFiltered:
    def test_returns_schedules_for_repo(self):
        client = Mock(spec=IGraphQLClient)
        client.list_schedules.return_value = ListSchedules(
            schedulesOrError=ListSchedulesSchedulesOrErrorSchedules(
                __typename="Schedules",
                results=[
                    _make_schedule_result("schedule-a", "id-a"),
                    _make_schedule_result("schedule-b", "id-b"),
                ],
            )
        )

        result = DgApiScheduleApi(_client=client).list_schedules(
            repository_location_name="loc",
            repository_name="repo",
        )

        client.list_schedules.assert_called_once_with(
            repository_selector=RepositorySelector(
                repositoryLocationName="loc",
                repositoryName="repo",
            )
        )

        assert result.total == 2
        assert result.items[0].id == "id-a"
        assert result.items[0].code_location_origin == "loc@repo"
        assert result.items[1].id == "id-b"
        assert result.items[1].code_location_origin == "loc@repo"

    def test_empty_results(self):
        client = Mock(spec=IGraphQLClient)
        client.list_schedules.return_value = ListSchedules(
            schedulesOrError=ListSchedulesSchedulesOrErrorSchedules(
                __typename="Schedules",
                results=[],
            )
        )

        result = DgApiScheduleApi(_client=client).list_schedules(
            repository_location_name="loc",
            repository_name="repo",
        )

        assert result == DgApiScheduleList(items=[])

    def test_repo_not_found_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_schedules.return_value = ListSchedules(
            schedulesOrError=ListSchedulesSchedulesOrErrorRepositoryNotFoundError(
                __typename="RepositoryNotFoundError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error listing schedules"):
            DgApiScheduleApi(_client=client).list_schedules(
                repository_location_name="loc",
                repository_name="repo",
            )

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_schedules.return_value = ListSchedules(
            schedulesOrError=ListSchedulesSchedulesOrErrorPythonError(
                __typename="PythonError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error listing schedules"):
            DgApiScheduleApi(_client=client).list_schedules(
                repository_location_name="loc",
                repository_name="repo",
            )


class TestListSchedulesAll:
    def test_returns_all_schedules_across_repos(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_with_schedules.return_value = _make_repos_with_schedules(
            schedules=[("schedule-a", "id-a"), ("schedule-b", "id-b")]
        )

        result = DgApiScheduleApi(_client=client).list_schedules()

        assert result.total == 2
        assert result.items[0].id == "id-a"
        assert result.items[0].code_location_origin == "test_location@__repository__"
        assert result.items[1].id == "id-b"
        assert result.items[1].code_location_origin == "test_location@__repository__"

    def test_empty_repos(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_with_schedules.return_value = _make_repos_with_schedules(
            schedules=[]
        )

        result = DgApiScheduleApi(_client=client).list_schedules()

        assert result == DgApiScheduleList(items=[])

    def test_repo_not_found_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_with_schedules.return_value = ListRepositoriesWithSchedules(
            repositoriesOrError=ListRepositoriesWithSchedulesRepositoriesOrErrorRepositoryNotFoundError(
                __typename="RepositoryNotFoundError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error listing schedules"):
            DgApiScheduleApi(_client=client).list_schedules()

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_with_schedules.return_value = ListRepositoriesWithSchedules(
            repositoriesOrError=ListRepositoriesWithSchedulesRepositoriesOrErrorPythonError(
                __typename="PythonError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error listing schedules"):
            DgApiScheduleApi(_client=client).list_schedules()


class TestGetSchedule:
    def test_returns_schedule(self):
        client = Mock(spec=IGraphQLClient)
        client.get_schedule.return_value = GetSchedule(
            scheduleOrError=GetScheduleScheduleOrErrorSchedule(
                __typename="Schedule",
                id="test-schedule-id",
                name="test-schedule-name",
                cronSchedule="0 0 * * *",
                pipelineName="test_pipeline",
                description="test-description",
                executionTimezone="UTC",
                scheduleState=GetScheduleScheduleOrErrorScheduleScheduleState(
                    status=InstigationStatus.RUNNING,
                ),
            )
        )

        result = DgApiScheduleApi(_client=client).get_schedule(
            schedule_name="test-schedule-name",
            repository_location_name="loc",
            repository_name="repo",
        )

        client.get_schedule.assert_called_once_with(
            schedule_selector=ScheduleSelector(
                repositoryLocationName="loc",
                repositoryName="repo",
                scheduleName="test-schedule-name",
            )
        )

        assert result.id == "test-schedule-id"
        assert result.name == "test-schedule-name"
        assert result.status == InstigationStatus.RUNNING
        assert result.cron_schedule == "0 0 * * *"
        assert result.pipeline_name == "test_pipeline"
        assert result.code_location_origin == "loc@repo"
        assert result.description == "test-description"
        assert result.execution_timezone == "UTC"
        assert result.next_tick_timestamp is None

    def test_schedule_not_found_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_schedule.return_value = GetSchedule(
            scheduleOrError=GetScheduleScheduleOrErrorScheduleNotFoundError(
                __typename="ScheduleNotFoundError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error fetching schedule"):
            DgApiScheduleApi(_client=client).get_schedule(
                schedule_name="missing",
                repository_location_name="loc",
                repository_name="repo",
            )

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_schedule.return_value = GetSchedule(
            scheduleOrError=GetScheduleScheduleOrErrorPythonError(
                __typename="PythonError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error fetching schedule"):
            DgApiScheduleApi(_client=client).get_schedule(
                schedule_name="test-schedule-name",
                repository_location_name="loc",
                repository_name="repo",
            )


class TestGetScheduleByName:
    def test_finds_schedule_by_name(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_with_schedules.return_value = _make_repos_with_schedules(
            schedules=[("target_schedule", "id-target"), ("other_schedule", "id-other")]
        )

        result = DgApiScheduleApi(_client=client).get_schedule_by_name("target_schedule")

        assert result.id == "id-target"
        assert result.code_location_origin == "test_location@__repository__"

    def test_schedule_not_found_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_with_schedules.return_value = _make_repos_with_schedules(
            schedules=[("other_schedule", "id-other")]
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Schedule not found: missing_schedule"):
            DgApiScheduleApi(_client=client).get_schedule_by_name("missing_schedule")

    def test_multiple_matching_schedules_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_with_schedules.return_value = ListRepositoriesWithSchedules(
            repositoriesOrError=ListRepositoriesWithSchedulesRepositoriesOrErrorRepositoryConnection(
                __typename="RepositoryConnection",
                nodes=[
                    ListRepositoriesWithSchedulesRepositoriesOrErrorRepositoryConnectionNodes(
                        name="repo_a",
                        location=ListRepositoriesWithSchedulesRepositoriesOrErrorRepositoryConnectionNodesLocation(
                            name="loc_a"
                        ),
                        schedules=[
                            ListRepositoriesWithSchedulesRepositoriesOrErrorRepositoryConnectionNodesSchedules(
                                id="id_1",
                                name="dup_schedule",
                                cronSchedule="0 0 * * *",
                                pipelineName="pipeline",
                                description=None,
                                executionTimezone=None,
                                scheduleState=ListRepositoriesWithSchedulesRepositoriesOrErrorRepositoryConnectionNodesSchedulesScheduleState(
                                    status=InstigationStatus.RUNNING,
                                ),
                            )
                        ],
                    ),
                    ListRepositoriesWithSchedulesRepositoriesOrErrorRepositoryConnectionNodes(
                        name="repo_b",
                        location=ListRepositoriesWithSchedulesRepositoriesOrErrorRepositoryConnectionNodesLocation(
                            name="loc_b"
                        ),
                        schedules=[
                            ListRepositoriesWithSchedulesRepositoriesOrErrorRepositoryConnectionNodesSchedules(
                                id="id_2",
                                name="dup_schedule",
                                cronSchedule="0 0 * * *",
                                pipelineName="pipeline",
                                description=None,
                                executionTimezone=None,
                                scheduleState=ListRepositoriesWithSchedulesRepositoriesOrErrorRepositoryConnectionNodesSchedulesScheduleState(
                                    status=InstigationStatus.STOPPED,
                                ),
                            )
                        ],
                    ),
                ],
            )
        )

        with pytest.raises(
            DagsterPlusGraphqlError,
            match="Multiple schedules found with name 'dup_schedule' in code locations: loc_a@repo_a, loc_b@repo_b",
        ):
            DgApiScheduleApi(_client=client).get_schedule_by_name("dup_schedule")

    def test_repo_not_found_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_with_schedules.return_value = ListRepositoriesWithSchedules(
            repositoriesOrError=ListRepositoriesWithSchedulesRepositoriesOrErrorRepositoryNotFoundError(
                __typename="RepositoryNotFoundError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error listing repositories"):
            DgApiScheduleApi(_client=client).get_schedule_by_name("test_schedule")

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories_with_schedules.return_value = ListRepositoriesWithSchedules(
            repositoriesOrError=ListRepositoriesWithSchedulesRepositoriesOrErrorPythonError(
                __typename="PythonError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error listing repositories"):
            DgApiScheduleApi(_client=client).get_schedule_by_name("test_schedule")
