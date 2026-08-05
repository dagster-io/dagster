import unittest.mock

import pytest
import responses
from dagster import AssetCheckEvaluation, AssetExecutionContext, AssetMaterialization, Failure
from dagster._core.definitions.materialize import materialize
from dagster._core.errors import DagsterExecutionInterruptedError
from dagster._core.test_utils import environ
from dagster_dbt.asset_utils import DBT_INDIRECT_SELECTION_ENV
from dagster_dbt.cloud_v2.asset_decorator import dbt_cloud_assets
from dagster_dbt.cloud_v2.client import DbtCloudWorkspaceClient
from dagster_dbt.cloud_v2.resources import DbtCloudCredentials, DbtCloudWorkspace
from dagster_dbt.cloud_v2.types import DbtCloudJobRunStatusType, DbtCloudRun

from dagster_dbt_tests.cloud_v2.conftest import (
    SAMPLE_CUSTOM_CREATE_JOB_RESPONSE,
    SAMPLE_LIST_JOBS_RESPONSE,
    TEST_ACCOUNT_ID,
    TEST_ADHOC_JOB_ID,
    TEST_CUSTOM_ADHOC_JOB_NAME,
    TEST_DEFAULT_ADHOC_JOB_NAME,
    TEST_ENVIRONMENT_ID,
    TEST_FINISHED_AT_LOWER_BOUND,
    TEST_FINISHED_AT_UPPER_BOUND,
    TEST_PROJECT_ID,
    TEST_REST_API_BASE_URL,
    TEST_RUN_ID,
    TEST_RUN_URL,
    TEST_TOKEN,
    get_sample_job_data,
    get_sample_list_runs_sample,
    get_sample_run_data,
    get_sample_run_response,
)


def assert_rest_api_call(
    call: responses.Call,
    endpoint: str | None,
    method: str | None = None,
):
    rest_api_url = call.request.url.split("?")[0]
    test_url = f"{TEST_REST_API_BASE_URL}/{endpoint}" if endpoint else TEST_REST_API_BASE_URL
    assert rest_api_url == test_url
    if method:
        assert method == call.request.method
    assert call.request.headers["Authorization"] == f"Token {TEST_TOKEN}"


def test_basic_resource_request(
    workspace: DbtCloudWorkspace,
    all_api_mocks: responses.RequestsMock,
) -> None:
    client = workspace.get_client()

    # jobs data calls
    client.list_jobs(project_id=TEST_PROJECT_ID, environment_id=TEST_ENVIRONMENT_ID)
    client.create_job(
        project_id=TEST_PROJECT_ID,
        environment_id=TEST_ENVIRONMENT_ID,
        job_name=TEST_DEFAULT_ADHOC_JOB_NAME,
    )
    client.trigger_job_run(job_id=TEST_ADHOC_JOB_ID)
    client.get_run_details(run_id=TEST_RUN_ID)
    client.get_run_manifest_json(run_id=TEST_RUN_ID)
    client.get_run_results_json(run_id=TEST_RUN_ID)
    client.get_runs_batch(
        project_id=TEST_PROJECT_ID,
        environment_id=TEST_ENVIRONMENT_ID,
        finished_at_lower_bound=TEST_FINISHED_AT_LOWER_BOUND,
        finished_at_upper_bound=TEST_FINISHED_AT_UPPER_BOUND,
    )
    client.list_run_artifacts(run_id=TEST_RUN_ID)

    assert len(all_api_mocks.calls) == 8
    assert_rest_api_call(call=all_api_mocks.calls[0], endpoint="jobs", method="GET")
    assert_rest_api_call(call=all_api_mocks.calls[1], endpoint="jobs", method="POST")
    assert_rest_api_call(
        call=all_api_mocks.calls[2], endpoint=f"jobs/{TEST_ADHOC_JOB_ID}/run", method="POST"
    )
    assert_rest_api_call(call=all_api_mocks.calls[3], endpoint=f"runs/{TEST_RUN_ID}", method="GET")
    assert_rest_api_call(
        call=all_api_mocks.calls[4],
        endpoint=f"runs/{TEST_RUN_ID}/artifacts/manifest.json",
        method="GET",
    )
    assert_rest_api_call(
        call=all_api_mocks.calls[5],
        endpoint=f"runs/{TEST_RUN_ID}/artifacts/run_results.json",
        method="GET",
    )
    assert_rest_api_call(call=all_api_mocks.calls[6], endpoint="runs", method="GET")
    assert_rest_api_call(
        call=all_api_mocks.calls[7], endpoint=f"runs/{TEST_RUN_ID}/artifacts", method="GET"
    )


def test_get_or_create_dagster_adhoc_jobs(
    workspace: DbtCloudWorkspace,
    job_api_mocks: responses.RequestsMock,
) -> None:
    # The expected job name is not in the initial list of jobs so a job is created
    jobs = workspace._get_or_create_dagster_adhoc_jobs()  # noqa

    assert len(job_api_mocks.calls) == 2
    assert_rest_api_call(call=job_api_mocks.calls[0], endpoint="jobs", method="GET")
    assert_rest_api_call(call=job_api_mocks.calls[1], endpoint="jobs", method="POST")

    assert len(jobs) == 1
    job = jobs[0]
    assert job.id == TEST_ADHOC_JOB_ID
    assert job.name == TEST_DEFAULT_ADHOC_JOB_NAME
    assert job.account_id == TEST_ACCOUNT_ID
    assert job.project_id == TEST_PROJECT_ID
    assert job.environment_id == TEST_ENVIRONMENT_ID


def test_custom_adhoc_job_name(
    credentials: DbtCloudCredentials,
    job_api_mocks: responses.RequestsMock,
) -> None:
    # Create a workspace with custom ad hoc job name
    workspace = DbtCloudWorkspace(
        credentials=credentials,
        project_id=TEST_PROJECT_ID,
        environment_id=TEST_ENVIRONMENT_ID,
        adhoc_job_name="test_adhoc_job_name",
    )

    job_api_mocks.replace(
        method_or_response=responses.POST,
        url=f"{TEST_REST_API_BASE_URL}/jobs",
        json=SAMPLE_CUSTOM_CREATE_JOB_RESPONSE,
        status=201,
    )

    # The expected job name is not in the initial list of jobs so a job is created
    jobs = workspace._get_or_create_dagster_adhoc_jobs()  # noqa

    assert len(job_api_mocks.calls) == 2
    assert_rest_api_call(call=job_api_mocks.calls[0], endpoint="jobs", method="GET")
    assert_rest_api_call(call=job_api_mocks.calls[1], endpoint="jobs", method="POST")

    assert len(jobs) == 1
    job = jobs[0]
    assert job.id == TEST_ADHOC_JOB_ID
    assert job.name == TEST_CUSTOM_ADHOC_JOB_NAME
    assert job.account_id == TEST_ACCOUNT_ID
    assert job.project_id == TEST_PROJECT_ID
    assert job.environment_id == TEST_ENVIRONMENT_ID


def test_cli_invocation(
    workspace: DbtCloudWorkspace,
    cli_invocation_api_mocks: responses.RequestsMock,
) -> None:
    invocation = workspace.cli(args=["run"])
    events = list(invocation.wait())

    asset_materializations = [event for event in events if isinstance(event, AssetMaterialization)]
    asset_check_evaluations = [event for event in events if isinstance(event, AssetCheckEvaluation)]

    # 8 asset materializations
    assert len(asset_materializations) == 8
    # 20 asset check evaluations
    assert len(asset_check_evaluations) == 20

    # Sanity check
    first_mat = next(mat for mat in sorted(asset_materializations))
    assert first_mat.asset_key.path == ["customers"]
    assert first_mat.metadata["run_url"].value == TEST_RUN_URL

    first_check_eval = next(check_eval for check_eval in sorted(asset_check_evaluations))
    assert first_check_eval.check_name == "not_null_customers_customer_id"
    assert first_check_eval.asset_key.path == ["customers"]


def test_cli_invocation_in_asset_decorator(
    workspace: DbtCloudWorkspace, cli_invocation_api_mocks: responses.RequestsMock
):
    @dbt_cloud_assets(workspace=workspace)
    def my_dbt_cloud_assets(context: AssetExecutionContext, dbt_cloud: DbtCloudWorkspace):
        cli_invocation = dbt_cloud.cli(args=["build"], context=context)
        # The cli invocation args are updated with the context
        assert cli_invocation.args == ["build", "--select", "fqn:*"]
        yield from cli_invocation.wait()

    result = materialize(
        [my_dbt_cloud_assets],
        resources={"dbt_cloud": workspace},
    )
    assert result.success

    asset_materialization_events = result.get_asset_materialization_events()
    asset_check_evaluation = result.get_asset_check_evaluations()

    # materializations and check results are successful outputs
    outputs = [event for event in result.all_events if event.is_successful_output]
    assert len(outputs) == 28

    # materialization outputs have metadata, asset check outputs don't
    outputs_with_metadata = [output for output in outputs if output.step_output_data.metadata]
    assert len(outputs_with_metadata) == 8

    # 8 asset materializations
    assert len(asset_materialization_events) == 8
    # 20 asset check evaluations
    assert len(asset_check_evaluation) == 20

    # Sanity check
    first_output_with_metadata = next(output for output in sorted(outputs_with_metadata))
    assert first_output_with_metadata.step_output_data.output_name == "customers"
    assert first_output_with_metadata.step_output_data.metadata["run_url"].value == TEST_RUN_URL

    first_mat = next(event.materialization for event in sorted(asset_materialization_events))
    assert first_mat.asset_key.path == ["customers"]
    assert first_mat.metadata["run_url"].value == TEST_RUN_URL

    first_check_eval = next(check_eval for check_eval in sorted(asset_check_evaluation))
    assert first_check_eval.check_name == "not_null_customers_customer_id"
    assert first_check_eval.asset_key.path == ["customers"]


def test_cli_invocation_with_custom_indirect_selection(
    workspace: DbtCloudWorkspace, cli_invocation_api_mocks: responses.RequestsMock
):
    with environ({DBT_INDIRECT_SELECTION_ENV: "eager"}):

        @dbt_cloud_assets(workspace=workspace)
        def my_dbt_cloud_assets(context: AssetExecutionContext, dbt_cloud: DbtCloudWorkspace):
            cli_invocation = dbt_cloud.cli(args=["build"], context=context)
            # The cli invocation args are updated with the context
            assert cli_invocation.args == [
                "build",
                "--select",
                "fqn:*",
                "--indirect-selection eager",
            ]
            yield from cli_invocation.wait()

        result = materialize(
            [my_dbt_cloud_assets],
            resources={"dbt_cloud": workspace},
        )
        assert result.success


def test_cli_invocation_wait_timeout(
    workspace: DbtCloudWorkspace,
    cli_invocation_wait_timeout_mocks: responses.RequestsMock,
) -> None:
    timeout = 0.1
    with pytest.raises(
        Exception, match=f"Run {TEST_RUN_ID} did not complete within {timeout} seconds."
    ):
        list(workspace.cli(args=["run"]).wait(timeout=timeout))


@pytest.mark.parametrize(
    "n_polls, last_status, succeed_at_end",
    [
        (0, int(DbtCloudJobRunStatusType.SUCCESS), True),
        (0, int(DbtCloudJobRunStatusType.ERROR), False),
        (0, int(DbtCloudJobRunStatusType.CANCELLED), False),
        (4, int(DbtCloudJobRunStatusType.SUCCESS), True),
        (4, int(DbtCloudJobRunStatusType.ERROR), False),
        (4, int(DbtCloudJobRunStatusType.CANCELLED), False),
        (30, int(DbtCloudJobRunStatusType.SUCCESS), True),
    ],
    ids=[
        "poll_short_success",
        "poll_short_error",
        "poll_short_cancelled",
        "poll_medium_success",
        "poll_medium_error",
        "poll_medium_cancelled",
        "poll_long_success",
    ],
)
def test_poll_run(n_polls, last_status, succeed_at_end, workspace: DbtCloudWorkspace):
    client = workspace.get_client()

    # Create mock responses to mock full poll behavior, used only in this test
    def _mock_interaction():
        with responses.RequestsMock() as response:
            # n polls before updating
            for _ in range(n_polls):
                # TODO parametrize status
                response.add(
                    method=responses.GET,
                    url=f"{TEST_REST_API_BASE_URL}/runs/{TEST_RUN_ID}",
                    json=get_sample_run_response(run_status=int(DbtCloudJobRunStatusType.RUNNING)),
                    status=200,
                )
            # final state will be updated
            response.add(
                method=responses.GET,
                url=f"{TEST_REST_API_BASE_URL}/runs/{TEST_RUN_ID}",
                json=get_sample_run_response(run_status=last_status),
                status=200,
            )

            run_data = client.poll_run(TEST_RUN_ID, poll_interval=0.1)
            run = DbtCloudRun.from_run_details(run_details=run_data)
            run.raise_for_status()
            return run_data

    if succeed_at_end:
        assert (
            _mock_interaction()
            == get_sample_run_response(run_status=int(DbtCloudJobRunStatusType.SUCCESS))["data"]
        )
    else:
        with pytest.raises(Failure, match="failed!"):
            _mock_interaction()


# ----------------------------------------------------------------------------
# Ad hoc job pool + greedy selection
# ----------------------------------------------------------------------------


POOL_JOB_ID_0 = TEST_ADHOC_JOB_ID
POOL_JOB_ID_1 = TEST_ADHOC_JOB_ID + 1
POOL_JOB_ID_2 = TEST_ADHOC_JOB_ID + 2


def _empty_list_jobs_response() -> dict:
    return {
        "data": [],
        "extra": {
            "filters": {},
            "order_by": "string",
            "pagination": {"count": 0, "total_count": 0},
        },
        "status": {
            "code": 200,
            "is_success": True,
            "user_message": "",
            "developer_message": "",
        },
    }


def _create_job_response(job_name: str, job_id: int) -> dict:
    return {
        "data": get_sample_job_data(job_name=job_name, job_id=job_id),
        "status": {
            "code": 201,
            "is_success": True,
            "user_message": "",
            "developer_message": "",
        },
    }


def test_get_or_create_dagster_adhoc_jobs_pool_creates_all(
    credentials: DbtCloudCredentials,
) -> None:
    """pool_size=3 with no pre-existing jobs creates three jobs with the expected names."""
    workspace = DbtCloudWorkspace(
        credentials=credentials,
        project_id=TEST_PROJECT_ID,
        environment_id=TEST_ENVIRONMENT_ID,
        adhoc_job_pool_size=3,
    )
    expected_names = [
        TEST_DEFAULT_ADHOC_JOB_NAME,
        f"{TEST_DEFAULT_ADHOC_JOB_NAME}__1",
        f"{TEST_DEFAULT_ADHOC_JOB_NAME}__2",
    ]
    expected_ids = [POOL_JOB_ID_0, POOL_JOB_ID_1, POOL_JOB_ID_2]
    with responses.RequestsMock() as mock:
        mock.add(
            method=responses.GET,
            url=f"{TEST_REST_API_BASE_URL}/jobs",
            json=_empty_list_jobs_response(),
            status=200,
        )
        for name, job_id in zip(expected_names, expected_ids):
            mock.add(
                method=responses.POST,
                url=f"{TEST_REST_API_BASE_URL}/jobs",
                json=_create_job_response(job_name=name, job_id=job_id),
                status=201,
            )

        jobs = workspace._get_or_create_dagster_adhoc_jobs()  # noqa
        assert [job.id for job in jobs] == expected_ids
        assert [job.name for job in jobs] == expected_names


def test_get_or_create_dagster_adhoc_jobs_pool_reuses_existing(
    credentials: DbtCloudCredentials,
) -> None:
    """pool_size=3 with the index-0 job already present reuses it and creates the rest."""
    workspace = DbtCloudWorkspace(
        credentials=credentials,
        project_id=TEST_PROJECT_ID,
        environment_id=TEST_ENVIRONMENT_ID,
        adhoc_job_pool_size=3,
    )
    list_jobs_with_existing = {
        **SAMPLE_LIST_JOBS_RESPONSE,
        "data": [get_sample_job_data(job_name=TEST_DEFAULT_ADHOC_JOB_NAME, job_id=POOL_JOB_ID_0)],
    }
    with responses.RequestsMock() as mock:
        mock.add(
            method=responses.GET,
            url=f"{TEST_REST_API_BASE_URL}/jobs",
            json=list_jobs_with_existing,
            status=200,
        )
        # Only indices 1 and 2 are created; index 0 is reused.
        for name, job_id in [
            (f"{TEST_DEFAULT_ADHOC_JOB_NAME}__1", POOL_JOB_ID_1),
            (f"{TEST_DEFAULT_ADHOC_JOB_NAME}__2", POOL_JOB_ID_2),
        ]:
            mock.add(
                method=responses.POST,
                url=f"{TEST_REST_API_BASE_URL}/jobs",
                json=_create_job_response(job_name=name, job_id=job_id),
                status=201,
            )

        jobs = workspace._get_or_create_dagster_adhoc_jobs()  # noqa

        # Exactly one GET (list_jobs) and two POSTs (create_job for indices 1 and 2).
        post_calls = [call for call in mock.calls if call.request.method == "POST"]
        assert len(post_calls) == 2
        assert [job.id for job in jobs] == [POOL_JOB_ID_0, POOL_JOB_ID_1, POOL_JOB_ID_2]


def test_get_or_create_dagster_adhoc_jobs_pool_custom_prefix(
    credentials: DbtCloudCredentials,
) -> None:
    """A custom adhoc_job_name becomes the prefix when pool_size > 1."""
    custom = "my_prefix"
    workspace = DbtCloudWorkspace(
        credentials=credentials,
        project_id=TEST_PROJECT_ID,
        environment_id=TEST_ENVIRONMENT_ID,
        adhoc_job_name=custom,
        adhoc_job_pool_size=2,
    )
    with responses.RequestsMock() as mock:
        mock.add(
            method=responses.GET,
            url=f"{TEST_REST_API_BASE_URL}/jobs",
            json=_empty_list_jobs_response(),
            status=200,
        )
        for name, job_id in [(custom, POOL_JOB_ID_0), (f"{custom}__1", POOL_JOB_ID_1)]:
            mock.add(
                method=responses.POST,
                url=f"{TEST_REST_API_BASE_URL}/jobs",
                json=_create_job_response(job_name=name, job_id=job_id),
                status=201,
            )

        jobs = workspace._get_or_create_dagster_adhoc_jobs()  # noqa
        assert [job.name for job in jobs] == [custom, f"{custom}__1"]


def test_pick_available_adhoc_job_id_single_no_api_call(workspace: DbtCloudWorkspace) -> None:
    """pool_size=1 short-circuits without calling dbt Cloud."""
    # No responses mock active — any HTTP call would fail.
    assert workspace._pick_available_adhoc_job_id([POOL_JOB_ID_0]) == POOL_JOB_ID_0  # noqa


def _runs_response_for_job(job_id: int, is_active: bool) -> dict:
    """Mock response for `get_active_job_ids`' single-job-id query: one run if
    active, empty otherwise.
    """
    data = (
        [get_sample_run_data(run_status=int(DbtCloudJobRunStatusType.RUNNING), job_id=job_id)]
        if is_active
        else []
    )
    return get_sample_list_runs_sample(data=data, count=len(data), total_count=len(data))


def _add_active_job_id_mocks(
    mock: responses.RequestsMock, active_by_job_id: dict[int, bool]
) -> None:
    """Adds one `/runs` mock per entry, in iteration order."""
    for job_id, is_active in active_by_job_id.items():
        mock.add(
            method=responses.GET,
            url=f"{TEST_REST_API_BASE_URL}/runs",
            json=_runs_response_for_job(job_id, is_active),
            status=200,
        )


def test_pick_available_adhoc_job_id_picks_first_free(
    credentials: DbtCloudCredentials,
) -> None:
    """When job 0 is busy, the picker returns job 1."""
    workspace = DbtCloudWorkspace(
        credentials=credentials,
        project_id=TEST_PROJECT_ID,
        environment_id=TEST_ENVIRONMENT_ID,
        adhoc_job_pool_size=3,
    )
    pool = [POOL_JOB_ID_0, POOL_JOB_ID_1, POOL_JOB_ID_2]
    with responses.RequestsMock() as mock:
        _add_active_job_id_mocks(
            mock, {POOL_JOB_ID_0: True, POOL_JOB_ID_1: False, POOL_JOB_ID_2: False}
        )

        picked = workspace._pick_available_adhoc_job_id(pool)  # noqa
        assert picked == POOL_JOB_ID_1


def test_pick_available_adhoc_job_id_overflow_returns_pool_member(
    credentials: DbtCloudCredentials,
) -> None:
    """When all jobs are busy, overflow returns *some* job from the pool (chosen
    randomly to avoid piling up on a single job).
    """
    workspace = DbtCloudWorkspace(
        credentials=credentials,
        project_id=TEST_PROJECT_ID,
        environment_id=TEST_ENVIRONMENT_ID,
        adhoc_job_pool_size=3,
        adhoc_job_pool_mode="overflow",
    )
    pool = [POOL_JOB_ID_0, POOL_JOB_ID_1, POOL_JOB_ID_2]
    with responses.RequestsMock() as mock:
        _add_active_job_id_mocks(mock, {jid: True for jid in pool})

        picked = workspace._pick_available_adhoc_job_id(pool)  # noqa
        assert picked in pool


def test_pick_available_adhoc_job_id_fail_raises(
    credentials: DbtCloudCredentials,
) -> None:
    """When all jobs are busy and behavior=fail, the picker raises."""
    workspace = DbtCloudWorkspace(
        credentials=credentials,
        project_id=TEST_PROJECT_ID,
        environment_id=TEST_ENVIRONMENT_ID,
        adhoc_job_pool_size=3,
        adhoc_job_pool_mode="fail",
    )
    pool = [POOL_JOB_ID_0, POOL_JOB_ID_1, POOL_JOB_ID_2]
    with responses.RequestsMock() as mock:
        _add_active_job_id_mocks(mock, {jid: True for jid in pool})

        with pytest.raises(Failure, match="ad hoc dbt Cloud jobs in the pool"):
            workspace._pick_available_adhoc_job_id(pool)  # noqa


def test_get_active_job_ids(workspace: DbtCloudWorkspace) -> None:
    """Client returns the subset of job IDs with at least one active run."""
    client = workspace.get_client()
    pool = [POOL_JOB_ID_0, POOL_JOB_ID_1, POOL_JOB_ID_2]
    with responses.RequestsMock() as mock:
        _add_active_job_id_mocks(
            mock, {POOL_JOB_ID_0: True, POOL_JOB_ID_1: False, POOL_JOB_ID_2: True}
        )

        active = client.get_active_job_ids(
            project_id=TEST_PROJECT_ID,
            environment_id=TEST_ENVIRONMENT_ID,
            job_ids=pool,
        )
        assert active == {POOL_JOB_ID_0, POOL_JOB_ID_2}
        # One request per job ID.
        assert len(mock.calls) == 3
        # Each request scopes by single job_definition_id with limit=1.
        for call in mock.calls:
            assert "job_definition_id=" in call.request.url
            assert "limit=1" in call.request.url


def test_get_active_job_ids_empty_input(workspace: DbtCloudWorkspace) -> None:
    """Empty job_ids returns an empty set without calling the API."""
    client = workspace.get_client()
    # No mock active — would fail if an HTTP call were attempted.
    assert (
        client.get_active_job_ids(
            project_id=TEST_PROJECT_ID,
            environment_id=TEST_ENVIRONMENT_ID,
            job_ids=[],
        )
        == set()
    )


def test_poll_run_cancels_on_dagster_interrupt(workspace: DbtCloudWorkspace) -> None:
    client = workspace.get_client()

    with responses.RequestsMock() as response:
        response.add(
            method=responses.POST,
            url=f"{TEST_REST_API_BASE_URL}/runs/{TEST_RUN_ID}/cancel",
            json=get_sample_run_response(run_status=int(DbtCloudJobRunStatusType.CANCELLED)),
            status=200,
        )

        # Patch at the class level since DbtCloudWorkspaceClient is a frozen pydantic model
        with unittest.mock.patch.object(
            DbtCloudWorkspaceClient,
            "get_run_details",
            side_effect=DagsterExecutionInterruptedError(),
        ):
            with pytest.raises(DagsterExecutionInterruptedError):
                client.poll_run(TEST_RUN_ID, poll_interval=0.01)

        assert len(response.calls) == 1
        assert_rest_api_call(
            call=response.calls[0], endpoint=f"runs/{TEST_RUN_ID}/cancel", method="POST"
        )
