import asyncio
from unittest import mock
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dagster import (
    AssetsDefinition,
    DagsterEventType,
    _check as check,
    materialize,
)
from dagster.components.testing import create_defs_folder_sandbox
from dagster_databricks.components.databricks_asset_bundle.component import (
    DatabricksAssetBundleComponent,
)
from dagster_databricks.components.databricks_asset_bundle.resource import (
    JOBS_LIST_PAGE_SIZE,
    RATE_LIMIT_STATUS_CODE,
    DatabricksWorkspace,
)
from databricks.sdk.service.jobs import Run, RunResultState, RunState, RunTask

from dagster_databricks_tests.components.databricks_asset_bundle.conftest import (
    EXISTING_CLUSTER_CONFIG,
    NEW_CLUSTER_CONFIG,
    TEST_DATABRICKS_WORKSPACE_HOST,
    TEST_DATABRICKS_WORKSPACE_TOKEN,
)

# ---------------------------------------------------------------------------
# Helpers for fetch_jobs tests
# ---------------------------------------------------------------------------


def make_workspace() -> DatabricksWorkspace:
    return DatabricksWorkspace(host="https://fake.databricks.com", token="fake-token")


def make_list_payload(job_ids: list[int], has_more: bool, next_token: str | None = None) -> dict:
    payload: dict = {"jobs": [{"job_id": jid} for jid in job_ids], "has_more": has_more}
    if next_token:
        payload["next_page_token"] = next_token
    return payload


def make_job_detail(job_id: int, name: str = "Job") -> dict:
    return {"job_id": job_id, "settings": {"name": name, "tasks": []}}


def mock_resp(status: int, json_data: dict, retry_after: str | None = None) -> MagicMock:
    resp = MagicMock()
    resp.status = status
    resp.raise_for_status = MagicMock(
        side_effect=Exception(f"HTTP {status}") if status >= 400 else None
    )
    resp.json = AsyncMock(return_value=json_data)
    resp.headers = {"Retry-After": retry_after} if retry_after else {}
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=False)
    return resp


def build_mock_session(list_pages: list[dict], detail_map: dict[int, dict]) -> MagicMock:
    pages = iter([mock_resp(200, p) for p in list_pages])

    def side_effect(url, **kwargs):
        if "list" in str(url):
            return next(pages)
        job_id = int(str(url).split("job_id=")[-1])
        return mock_resp(200, detail_map[job_id])

    session = MagicMock()
    session.get = MagicMock(side_effect=side_effect)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)
    return session


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_jobs_single_page():
    """Workspace with <100 jobs — one list request, no pagination."""
    session = build_mock_session(
        list_pages=[make_list_payload([1, 2, 3], has_more=False)],
        detail_map={i: make_job_detail(i) for i in [1, 2, 3]},
    )
    with patch("aiohttp.ClientSession", return_value=session):
        jobs = await make_workspace().fetch_jobs(None)

    assert {j.job_id for j in jobs} == {1, 2, 3}
    list_calls = [c for c in session.get.call_args_list if "list" in str(c)]
    assert len(list_calls) == 1


@pytest.mark.asyncio
async def test_fetch_jobs_multi_page():
    """Jobs spread across 3 pages — all 5 returned."""
    session = build_mock_session(
        list_pages=[
            make_list_payload([1, 2], has_more=True, next_token="tok1"),
            make_list_payload([3, 4], has_more=True, next_token="tok2"),
            make_list_payload([5], has_more=False),
        ],
        detail_map={i: make_job_detail(i) for i in range(1, 6)},
    )
    with patch("aiohttp.ClientSession", return_value=session):
        jobs = await make_workspace().fetch_jobs(None)

    assert {j.job_id for j in jobs} == {1, 2, 3, 4, 5}
    list_calls = [c for c in session.get.call_args_list if "list" in str(c)]
    assert len(list_calls) == 3


@pytest.mark.asyncio
async def test_fetch_jobs_uses_limit_param():
    """List requests include limit=JOBS_LIST_PAGE_SIZE."""
    session = build_mock_session(
        list_pages=[make_list_payload([1], has_more=False)],
        detail_map={1: make_job_detail(1)},
    )
    with patch("aiohttp.ClientSession", return_value=session):
        await make_workspace().fetch_jobs(None)

    list_call = next(c for c in session.get.call_args_list if "list" in str(c))
    assert list_call.kwargs.get("params", {}).get("limit") == JOBS_LIST_PAGE_SIZE


# ---------------------------------------------------------------------------
# next_page_token guard
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_jobs_missing_next_page_token_raises():
    """has_more=True but no next_page_token → descriptive ValueError."""
    bad_resp = mock_resp(200, {"jobs": [{"job_id": 1}], "has_more": True})
    session = MagicMock()
    session.get = MagicMock(return_value=bad_resp)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)

    with patch("aiohttp.ClientSession", return_value=session):
        with pytest.raises(ValueError, match="next_page_token"):
            await make_workspace().fetch_jobs(None)


# ---------------------------------------------------------------------------
# Rate-limit retry
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_single_job_retries_on_429_then_succeeds():
    """First detail request returns 429, second returns 200."""
    call_count = {"n": 0}

    def detail_side(url, **kw):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return mock_resp(RATE_LIMIT_STATUS_CODE, {})
        return mock_resp(200, make_job_detail(42, "MyJob"))

    session = MagicMock()
    session.get = MagicMock(
        side_effect=lambda url, **kw: (
            mock_resp(200, make_list_payload([42], has_more=False))
            if "list" in str(url)
            else detail_side(url, **kw)
        )
    )
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)

    with patch("aiohttp.ClientSession", return_value=session):
        with patch(
            "dagster_databricks.components.databricks_asset_bundle.resource.asyncio.sleep",
            new_callable=AsyncMock,
        ) as mock_sleep:
            jobs = await make_workspace().fetch_jobs(None)

    assert len(jobs) == 1
    assert jobs[0].job_id == 42
    mock_sleep.assert_called_once_with(1)  # min(2**0, 30) = 1


@pytest.mark.asyncio
async def test_fetch_single_job_respects_retry_after_header():
    """429 with Retry-After: 5 — sleeps for 5s, not the backoff formula."""
    call_count = {"n": 0}

    def detail_side(url, **kw):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return mock_resp(RATE_LIMIT_STATUS_CODE, {}, retry_after="5")
        return mock_resp(200, make_job_detail(7, "RetryJob"))

    session = MagicMock()
    session.get = MagicMock(
        side_effect=lambda url, **kw: (
            mock_resp(200, make_list_payload([7], has_more=False))
            if "list" in str(url)
            else detail_side(url, **kw)
        )
    )
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)

    with patch("aiohttp.ClientSession", return_value=session):
        with patch(
            "dagster_databricks.components.databricks_asset_bundle.resource.asyncio.sleep",
            new_callable=AsyncMock,
        ) as mock_sleep:
            jobs = await make_workspace().fetch_jobs(None)

    assert len(jobs) == 1
    assert jobs[0].job_id == 7
    mock_sleep.assert_called_once_with(5)  # Retry-After header value, not min(2**0, 30)=1


@pytest.mark.asyncio
async def test_fetch_single_job_exhausts_retries_and_raises():
    """All MAX_RETRIES+1 attempts return 429 — raises on final attempt."""
    rl_resp = mock_resp(RATE_LIMIT_STATUS_CODE, {})

    session = MagicMock()
    session.get = MagicMock(
        side_effect=lambda url, **kw: (
            mock_resp(200, make_list_payload([1], has_more=False))
            if "list" in str(url)
            else rl_resp
        )
    )
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)

    with patch("aiohttp.ClientSession", return_value=session):
        with patch(
            "dagster_databricks.components.databricks_asset_bundle.resource.asyncio.sleep",
            new_callable=AsyncMock,
        ):
            with pytest.raises(Exception, match=f"HTTP {RATE_LIMIT_STATUS_CODE}"):
                await make_workspace().fetch_jobs(None)


# ---------------------------------------------------------------------------
# Deadlock safety
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_deadlock_when_all_slots_rate_limited():
    """10 concurrent jobs all hit 429 on attempt 1 — all succeed on attempt 2."""
    job_ids = list(range(1, 11))
    call_counts: dict[int, int] = {jid: 0 for jid in job_ids}

    def detail_side(url, **kw):
        job_id = int(str(url).split("job_id=")[-1])
        call_counts[job_id] += 1
        if call_counts[job_id] == 1:
            return mock_resp(RATE_LIMIT_STATUS_CODE, {})
        return mock_resp(200, make_job_detail(job_id))

    session = MagicMock()
    session.get = MagicMock(
        side_effect=lambda url, **kw: (
            mock_resp(200, make_list_payload(job_ids, has_more=False))
            if "list" in str(url)
            else detail_side(url, **kw)
        )
    )
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)

    with patch("aiohttp.ClientSession", return_value=session):
        with patch(
            "dagster_databricks.components.databricks_asset_bundle.resource.asyncio.sleep",
            new_callable=AsyncMock,
        ):
            jobs = await asyncio.wait_for(make_workspace().fetch_jobs(None), timeout=5.0)

    assert len(jobs) == 10


# ---------------------------------------------------------------------------
# Session reuse
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_single_session_used_for_all_requests():
    """Only one aiohttp.ClientSession is created for the full fetch_jobs call."""
    session = build_mock_session(
        list_pages=[make_list_payload([1, 2], has_more=False)],
        detail_map={i: make_job_detail(i) for i in [1, 2]},
    )
    with patch("aiohttp.ClientSession", return_value=session) as mock_cls:
        await make_workspace().fetch_jobs(None)

    mock_cls.assert_called_once()


# ---------------------------------------------------------------------------
# _parse_raw_jobs static method
# ---------------------------------------------------------------------------


def test_parse_raw_jobs_empty_list():
    assert DatabricksWorkspace._parse_raw_jobs([]) == []  # noqa: SLF001


def test_parse_raw_jobs_empty_tasks():
    jobs = DatabricksWorkspace._parse_raw_jobs(  # noqa: SLF001
        [{"job_id": 7, "settings": {"name": "Empty", "tasks": []}}]
    )
    assert len(jobs) == 1
    assert jobs[0].job_id == 7
    assert jobs[0].tasks == []


def test_parse_raw_jobs_defaults_name():
    jobs = DatabricksWorkspace._parse_raw_jobs([{"job_id": 99, "settings": {}}])  # noqa: SLF001
    assert jobs[0].name == "Unnamed Job"


# ---------------------------------------------------------------------------
# List-phase 429 retry
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_phase_retries_on_429_with_retry_after():
    """List API returns 429 with Retry-After: 3 on first attempt, 200 on second."""
    list_call_count = {"n": 0}

    def list_side(url, **kw):
        if "list" not in str(url):
            job_id = int(str(url).split("job_id=")[-1])
            return mock_resp(200, make_job_detail(job_id))
        list_call_count["n"] += 1
        if list_call_count["n"] == 1:
            return mock_resp(RATE_LIMIT_STATUS_CODE, {}, retry_after="3")
        return mock_resp(200, make_list_payload([10], has_more=False))

    session = MagicMock()
    session.get = MagicMock(side_effect=list_side)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)

    with patch("aiohttp.ClientSession", return_value=session):
        with patch(
            "dagster_databricks.components.databricks_asset_bundle.resource.asyncio.sleep",
            new_callable=AsyncMock,
        ) as mock_sleep:
            jobs = await make_workspace().fetch_jobs(None)

    assert len(jobs) == 1
    assert jobs[0].job_id == 10
    mock_sleep.assert_any_call(3)  # Retry-After header respected on list phase


# ---------------------------------------------------------------------------
# Non-429 error on detail fetch
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_single_job_raises_on_500():
    """500 on detail fetch raises immediately without retry."""
    session = MagicMock()
    session.get = MagicMock(
        side_effect=lambda url, **kw: (
            mock_resp(200, make_list_payload([5], has_more=False))
            if "list" in str(url)
            else mock_resp(500, {})
        )
    )
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)

    with patch("aiohttp.ClientSession", return_value=session):
        with pytest.raises(Exception, match="HTTP 500"):
            await make_workspace().fetch_jobs(None)


# ---------------------------------------------------------------------------
# Filter exclusion
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_jobs_filter_excludes_jobs():
    """databricks_filter.include_job() returning False excludes those jobs."""
    session = build_mock_session(
        list_pages=[make_list_payload([1, 2, 3], has_more=False)],
        detail_map={i: make_job_detail(i) for i in [2]},  # only job 2 fetched
    )

    class _Filter:
        def include_job(self, j: dict) -> bool:
            return j["job_id"] == 2  # only include job 2

    with patch("aiohttp.ClientSession", return_value=session):
        jobs = await make_workspace().fetch_jobs(_Filter())

    assert len(jobs) == 1
    assert jobs[0].job_id == 2


ALL_TASK_KEYS = [
    "data_processing_notebook",
    "hello_world_spark_task",
    "stage_documents",
    "spark_processing_jar",
    "existing_job_with_references",
    "check_data_quality",
]


@pytest.mark.parametrize(
    "use_existing_cluster, use_new_cluster",
    [
        (False, False),
        (True, False),
        (False, True),
    ],
    ids=[
        "serverless_compute_config",
        "new_cluster_compute_config",
        "existing_cluster_compute_config",
    ],
)
@mock.patch(
    "databricks.sdk.service.jobs.JobsAPI.wait_get_run_job_terminated_or_skipped", autospec=True
)
@mock.patch("databricks.sdk.mixins.jobs.JobsExt.get_run", autospec=True)
@mock.patch("databricks.sdk.service.jobs.JobsAPI.submit", autospec=True)
@mock.patch("databricks.sdk.service.jobs.SubmitTask", autospec=True)
def test_load_component(
    mock_submit_task: mock.MagicMock,
    mock_submit_fn: mock.MagicMock,
    mock_get_run_fn: mock.MagicMock,
    mock_wait_fn: mock.MagicMock,
    use_existing_cluster: bool,
    use_new_cluster: bool,
    databricks_config_path: str,
):
    # With job-level grouping, all tasks are submitted in a single job run.
    # get_run is called twice: once after _submit_job, once after _poll_run.
    mock_get_run_fn.side_effect = [
        # First call: after _submit_job (initial state)
        Run(
            run_id=11111,
            job_id=22222,
            state=RunState(result_state=None),
            tasks=[RunTask(task_key=tk, state=RunState(result_state=None)) for tk in ALL_TASK_KEYS],
        ),
        # Second call: after _poll_run (final state)
        Run(
            run_id=11111,
            job_id=22222,
            state=RunState(result_state=RunResultState.SUCCESS),
            tasks=[
                RunTask(task_key=tk, state=RunState(result_state=RunResultState.SUCCESS))
                for tk in ALL_TASK_KEYS
            ],
        ),
    ]

    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=DatabricksAssetBundleComponent,
            scaffold_params={
                "databricks_config_path": databricks_config_path,
                "databricks_workspace_host": TEST_DATABRICKS_WORKSPACE_HOST,
                "databricks_workspace_token": TEST_DATABRICKS_WORKSPACE_TOKEN,
            },
            defs_yaml_contents={
                "type": "dagster_databricks.components.databricks_asset_bundle.component.DatabricksAssetBundleComponent",
                "attributes": {
                    "databricks_config_path": databricks_config_path,
                    "compute_config": {
                        **(EXISTING_CLUSTER_CONFIG if use_existing_cluster else {}),
                        **(NEW_CLUSTER_CONFIG if use_new_cluster else {}),
                    },
                    "workspace": {
                        "host": TEST_DATABRICKS_WORKSPACE_HOST,
                        "token": TEST_DATABRICKS_WORKSPACE_TOKEN,
                    },
                },
            },
        )

        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (
            component,
            defs,
        ):
            assert isinstance(component, DatabricksAssetBundleComponent)

            databricks_assets = list(defs.assets or [])
            databricks_assets = check.is_list(databricks_assets, of_type=AssetsDefinition)
            # All tasks in 1 job → 1 multi_asset with can_subset=True
            assert len(databricks_assets) == 1
            databricks_asset_keys_list = [
                databricks_asset_key
                for databricks_asset in databricks_assets
                for databricks_asset_key in databricks_asset.keys
            ]
            assert len(databricks_asset_keys_list) == 6
            databricks_asset_keys_set = set(databricks_asset_keys_list)
            assert len(databricks_asset_keys_list) == len(databricks_asset_keys_set)

            result = materialize(
                databricks_assets,
                resources={"databricks": component.workspace},
            )
            assert result.success
            asset_materializations = [
                event
                for event in result.all_events
                if event.event_type_value == DagsterEventType.ASSET_MATERIALIZATION
            ]
            assert len(asset_materializations) == 6
            materialized_asset_keys = {
                asset_materialization.asset_key for asset_materialization in asset_materializations
            }
            assert len(materialized_asset_keys) == 6
            assert databricks_asset_keys_set == materialized_asset_keys
            # All 6 tasks are submitted as SubmitTask objects in a single job
            assert mock_submit_task.call_count == 6

            # task_key is expected in every submit task
            assert all(call for call in mock_submit_task.mock_calls if "task_key" in call.kwargs)

            # Intra-job dependencies are preserved for tasks whose dependencies are selected
            depends_on_calls = [
                call for call in mock_submit_task.mock_calls if "depends_on" in call.kwargs
            ]
            assert len(depends_on_calls) > 0

            # libraries is expected in 4 of the 6 submit tasks we create
            assert (
                len([call for call in mock_submit_task.mock_calls if "libraries" in call.kwargs])
                == 4
            )

            # Serverless compute config is used by default
            # if no new cluster config or existing cluster config is passed.
            # Cluster config is expected in 4 of the 6 submit tasks we create if not using serverless compute,
            # otherwise not expected.
            expected_cluster_config_calls = 4 if use_existing_cluster or use_new_cluster else 0
            cluster_config_key = "existing_cluster_id" if use_existing_cluster else "new_cluster"
            assert (
                len(
                    [
                        call
                        for call in mock_submit_task.mock_calls
                        if cluster_config_key in call.kwargs
                    ]
                )
                == expected_cluster_config_calls
            )

            # 6 different types of submit task are created
            assert (
                len(
                    [call for call in mock_submit_task.mock_calls if "notebook_task" in call.kwargs]
                )
                == 1
            )
            assert (
                len(
                    [
                        call
                        for call in mock_submit_task.mock_calls
                        if "condition_task" in call.kwargs
                    ]
                )
                == 1
            )
            assert (
                len(
                    [
                        call
                        for call in mock_submit_task.mock_calls
                        if "spark_python_task" in call.kwargs
                    ]
                )
                == 1
            )
            assert (
                len(
                    [
                        call
                        for call in mock_submit_task.mock_calls
                        if "python_wheel_task" in call.kwargs
                    ]
                )
                == 1
            )
            assert (
                len(
                    [
                        call
                        for call in mock_submit_task.mock_calls
                        if "spark_jar_task" in call.kwargs
                    ]
                )
                == 1
            )
            assert (
                len([call for call in mock_submit_task.mock_calls if "run_job_task" in call.kwargs])
                == 1
            )
