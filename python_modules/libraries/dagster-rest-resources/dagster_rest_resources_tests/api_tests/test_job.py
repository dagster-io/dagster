from unittest.mock import Mock

import pytest
from dagster_rest_resources.__generated__.enums import InstigationStatus
from dagster_rest_resources.__generated__.list_repositories import (
    ListRepositories,
    ListRepositoriesRepositoriesOrErrorPythonError,
    ListRepositoriesRepositoriesOrErrorRepositoryConnection,
    ListRepositoriesRepositoriesOrErrorRepositoryConnectionNodes,
    ListRepositoriesRepositoriesOrErrorRepositoryConnectionNodesJobs,
    ListRepositoriesRepositoriesOrErrorRepositoryConnectionNodesJobsSchedules,
    ListRepositoriesRepositoriesOrErrorRepositoryConnectionNodesJobsSchedulesScheduleState,
    ListRepositoriesRepositoriesOrErrorRepositoryConnectionNodesJobsSensors,
    ListRepositoriesRepositoriesOrErrorRepositoryConnectionNodesJobsSensorsSensorState,
    ListRepositoriesRepositoriesOrErrorRepositoryConnectionNodesJobsTags,
    ListRepositoriesRepositoriesOrErrorRepositoryConnectionNodesLocation,
    ListRepositoriesRepositoriesOrErrorRepositoryNotFoundError,
)
from dagster_rest_resources.api.job import (
    DgApiJob,
    DgApiJobApi,
    DgApiJobList,
    DgApiJobScheduleSummary,
    DgApiJobSensorSummary,
    DgApiJobTag,
)
from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.exception import DagsterPlusGraphqlError


def _make_repo(
    name: str = "repo",
    location: str = "loc",
    jobs: list | None = None,
) -> ListRepositoriesRepositoriesOrErrorRepositoryConnectionNodes:
    return ListRepositoriesRepositoriesOrErrorRepositoryConnectionNodes(
        name=name,
        location=ListRepositoriesRepositoriesOrErrorRepositoryConnectionNodesLocation(
            name=location
        ),
        jobs=jobs or [],
    )


def _make_job(
    id: str = "test-job-id",
    name: str = "test-job-name",
    description: str | None = None,
    is_asset_job: bool = False,
    tags: list | None = None,
    schedules: list | None = None,
    sensors: list | None = None,
) -> ListRepositoriesRepositoriesOrErrorRepositoryConnectionNodesJobs:
    return ListRepositoriesRepositoriesOrErrorRepositoryConnectionNodesJobs(
        id=id,
        name=name,
        description=description,
        isAssetJob=is_asset_job,
        tags=tags or [],
        schedules=schedules or [],
        sensors=sensors or [],
    )


def _make_tag(
    key: str = "test-tag-key", value: str = "test-tag-value"
) -> ListRepositoriesRepositoriesOrErrorRepositoryConnectionNodesJobsTags:
    return ListRepositoriesRepositoriesOrErrorRepositoryConnectionNodesJobsTags(
        key=key,
        value=value,
    )


def _make_schedule(
    name: str = "test-schedule",
    cron_schedule: str = "0 * * * *",
    status: InstigationStatus = InstigationStatus.RUNNING,
) -> ListRepositoriesRepositoriesOrErrorRepositoryConnectionNodesJobsSchedules:
    return ListRepositoriesRepositoriesOrErrorRepositoryConnectionNodesJobsSchedules(
        name=name,
        cronSchedule=cron_schedule,
        scheduleState=ListRepositoriesRepositoriesOrErrorRepositoryConnectionNodesJobsSchedulesScheduleState(
            status=status
        ),
    )


def _make_sensor(
    name: str = "test-sensor",
    status: InstigationStatus = InstigationStatus.RUNNING,
) -> ListRepositoriesRepositoriesOrErrorRepositoryConnectionNodesJobsSensors:
    return ListRepositoriesRepositoriesOrErrorRepositoryConnectionNodesJobsSensors(
        name=name,
        sensorState=ListRepositoriesRepositoriesOrErrorRepositoryConnectionNodesJobsSensorsSensorState(
            status=status
        ),
    )


class TestListJobs:
    def test_returns_jobs_from_repositories(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories.return_value = ListRepositories(
            repositoriesOrError=ListRepositoriesRepositoriesOrErrorRepositoryConnection(
                __typename="RepositoryConnection",
                nodes=[
                    _make_repo(
                        name="repo-a",
                        location="loc-1",
                        jobs=[
                            _make_job(
                                id="j1",
                                name="job-one",
                                tags=[_make_tag()],
                            ),
                            _make_job(
                                id="j2",
                                name="job-two",
                                schedules=[_make_schedule()],
                            ),
                        ],
                    ),
                    _make_repo(
                        name="repo-b",
                        location="loc-2",
                        jobs=[
                            _make_job(
                                id="j3",
                                name="job-three",
                                sensors=[_make_sensor()],
                            )
                        ],
                    ),
                ],
            )
        )
        result = DgApiJobApi(client).list_jobs()

        assert result.total == 3
        assert [j.name for j in result.items] == [
            "job-one",
            "job-two",
            "job-three",
        ]
        assert [j.repository_origin for j in result.items] == [
            "loc-1@repo-a",
            "loc-1@repo-a",
            "loc-2@repo-b",
        ]
        assert [j.tags for j in result.items] == [
            [
                DgApiJobTag(
                    key="test-tag-key",
                    value="test-tag-value",
                )
            ],
            [],
            [],
        ]
        assert [j.schedules for j in result.items] == [
            [],
            [
                DgApiJobScheduleSummary(
                    name="test-schedule",
                    cron_schedule="0 * * * *",
                    status=InstigationStatus.RUNNING,
                )
            ],
            [],
        ]
        assert [j.sensors for j in result.items] == [
            [],
            [],
            [
                DgApiJobSensorSummary(
                    name="test-sensor",
                    status=InstigationStatus.RUNNING,
                )
            ],
        ]

    def test_returns_empty_list_when_no_repositories(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories.return_value = ListRepositories(
            repositoriesOrError=ListRepositoriesRepositoriesOrErrorRepositoryConnection(
                __typename="RepositoryConnection",
                nodes=[],
            )
        )
        result = DgApiJobApi(client).list_jobs()

        assert result == DgApiJobList(items=[], total=0)

    def test_repository_not_found_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories.return_value = ListRepositories(
            repositoriesOrError=ListRepositoriesRepositoriesOrErrorRepositoryNotFoundError(
                __typename="RepositoryNotFoundError", message=""
            )
        )
        with pytest.raises(DagsterPlusGraphqlError, match="Repository not found"):
            DgApiJobApi(client).list_jobs()

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories.return_value = ListRepositories(
            repositoriesOrError=ListRepositoriesRepositoriesOrErrorPythonError(
                __typename="PythonError", message=""
            )
        )
        with pytest.raises(DagsterPlusGraphqlError, match="Error fetching jobs"):
            DgApiJobApi(client).list_jobs()


class TestGetJobByName:
    def test_returns_matching_job(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories.return_value = ListRepositories(
            repositoriesOrError=ListRepositoriesRepositoriesOrErrorRepositoryConnection(
                __typename="RepositoryConnection",
                nodes=[
                    _make_repo(
                        jobs=[
                            _make_job(id="j1", name="job_one"),
                            _make_job(id="j2", name="job_two"),
                        ]
                    )
                ],
            )
        )
        result = DgApiJobApi(client).get_job_by_name("job_two")

        assert result == DgApiJob(id="j2", name="job_two", repository_origin="loc@repo")

    def test_raises_when_job_not_found(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories.return_value = ListRepositories(
            repositoriesOrError=ListRepositoriesRepositoriesOrErrorRepositoryConnection(
                __typename="RepositoryConnection",
                nodes=[_make_repo(jobs=[_make_job(name="test-job")])],
            )
        )
        with pytest.raises(DagsterPlusGraphqlError, match="Job not found: missing-job"):
            DgApiJobApi(client).get_job_by_name("missing-job")

    def test_raises_when_multiple_jobs_found(self):
        client = Mock(spec=IGraphQLClient)
        client.list_repositories.return_value = ListRepositories(
            repositoriesOrError=ListRepositoriesRepositoriesOrErrorRepositoryConnection(
                __typename="RepositoryConnection",
                nodes=[
                    _make_repo(name="repo-a", location="loc-1", jobs=[_make_job(name="dup_job")]),
                    _make_repo(name="repo-b", location="loc-2", jobs=[_make_job(name="dup_job")]),
                ],
            )
        )
        with pytest.raises(
            DagsterPlusGraphqlError, match="Multiple jobs found with name 'dup_job'"
        ):
            DgApiJobApi(client).get_job_by_name("dup_job")
