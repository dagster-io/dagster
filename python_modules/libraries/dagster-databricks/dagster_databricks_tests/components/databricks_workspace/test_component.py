import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dagster import AssetKey, AssetsDefinition, AssetSpec, materialize
from dagster_databricks.components.databricks_asset_bundle.configs import (
    DatabricksBaseTask,
    DatabricksJob,
)
from dagster_databricks.components.databricks_asset_bundle.resource import DatabricksWorkspace
from dagster_databricks.components.databricks_workspace.component import (
    DatabricksWorkspaceComponent,
)
from dagster_databricks.components.databricks_workspace.schema import DatabricksFilter
from databricks.sdk.service.jobs import RunResultState

# --- Helpers ---


def make_obj_task(key):
    """Creates a mock task that passes type checking for DatabricksBaseTask."""
    task = MagicMock(spec=DatabricksBaseTask)
    task.task_key = key
    return task


def make_hybrid_job(job_id, name, tasks):
    """Creates a REAL DatabricksJob to pass runtime type checks,
    but injects SimpleNamespace tasks to satisfy component logic logic.
    """
    return DatabricksJob(job_id=job_id, name=name, tasks=tasks)


MOCK_JOBS_HYBRID = [
    make_hybrid_job(
        job_id=101,
        name="Data Ingestion Job",
        tasks=[make_obj_task("ingest_task"), make_obj_task("process_task")],
    ),
    make_hybrid_job(job_id=102, name="ML Training Job", tasks=[make_obj_task("train_model")]),
    make_hybrid_job(job_id=103, name="Filtered Out Job", tasks=[make_obj_task("secret_task")]),
]

# --- Fixtures ---


@pytest.fixture
def mock_workspace():
    workspace = MagicMock(spec=DatabricksWorkspace)
    workspace.host = "https://fake-workspace.com"
    workspace.token = "fake-token"
    workspace.get_client.return_value = MagicMock()
    workspace.fetch_jobs = AsyncMock(return_value=MOCK_JOBS_HYBRID)
    return workspace


@pytest.fixture
def mock_serializer():
    """Prevents write_state_to_path from crashing when trying to serialize our hybrid objects."""
    with patch(
        "dagster_databricks.components.databricks_workspace.component.serialize_value"
    ) as mock:
        mock.return_value = "{}"
        yield mock


@pytest.fixture
def mock_deserializer():
    """Mocks reading from disk to return our objects directly."""
    with patch(
        "dagster_databricks.components.databricks_workspace.component.deserialize_value"
    ) as mock:
        mock.return_value = SimpleNamespace(jobs=MOCK_JOBS_HYBRID)
        yield mock


# --- Tests ---


def test_databricks_workspace_loading(mock_workspace, mock_serializer, mock_deserializer, tmp_path):
    """Test that the component correctly loads jobs and converts them to assets."""
    component = DatabricksWorkspaceComponent(workspace=mock_workspace)

    state_path = tmp_path / "state.json"
    asyncio.run(component.write_state_to_path(state_path))
    mock_workspace.fetch_jobs.assert_called_once()
    defs = component.build_defs_from_state(context=None, state_path=state_path)
    assert defs.assets is not None
    asset_keys = defs.resolve_asset_graph().get_all_asset_keys()

    assert AssetKey(["data_ingestion_job", "ingest_task"]) in asset_keys
    assert AssetKey(["data_ingestion_job", "process_task"]) in asset_keys
    assert AssetKey(["ml_training_job", "train_model"]) in asset_keys

    assert len(list(defs.assets)) == 3


def test_databricks_filtering(mock_workspace, mock_serializer, mock_deserializer, tmp_path):
    """Test that jobs are correctly filtered based on config."""
    db_filter = MagicMock(spec=DatabricksFilter)

    filtered_jobs = [j for j in MOCK_JOBS_HYBRID if j.job_id == 101]
    mock_workspace.fetch_jobs.return_value = filtered_jobs
    mock_deserializer.return_value = SimpleNamespace(jobs=filtered_jobs)

    component = DatabricksWorkspaceComponent(workspace=mock_workspace, databricks_filter=db_filter)

    state_path = tmp_path / "filtered_state.json"
    asyncio.run(component.write_state_to_path(state_path))

    defs = component.build_defs_from_state(context=None, state_path=state_path)
    assert defs.assets is not None
    asset_keys = defs.resolve_asset_graph().get_all_asset_keys()

    assert AssetKey(["data_ingestion_job", "ingest_task"]) in asset_keys
    assert AssetKey(["ml_training_job", "train_model"]) not in asset_keys


def test_databricks_custom_asset_mapping(
    mock_workspace, mock_serializer, mock_deserializer, tmp_path
):
    """Test that assets can be renamed and customized via YAML.

    assets_by_job_task_key requires both job name and task key to uniquely identify a task.
    """
    custom_spec = AssetSpec(
        key=AssetKey("my_custom_ingestion"),
        group_name="etl_group",
        description="Overridden description",
    )

    mock_deserializer.return_value = SimpleNamespace(jobs=MOCK_JOBS_HYBRID)

    # New structure: {job_name: {task_key: [specs]}}
    component = DatabricksWorkspaceComponent(
        workspace=mock_workspace,
        assets_by_job_task_key={"Data Ingestion Job": {"ingest_task": [custom_spec]}},
    )

    state_path = tmp_path / "custom_state.json"
    asyncio.run(component.write_state_to_path(state_path))

    defs = component.build_defs_from_state(context=None, state_path=state_path)
    assert defs.assets is not None
    asset_graph = defs.resolve_asset_graph()

    # Asset key is as specified by user (no automatic namespacing)
    custom_key = AssetKey("my_custom_ingestion")
    assert custom_key in asset_graph.get_all_asset_keys()

    spec = asset_graph.get(custom_key)
    assert spec.group_name == "etl_group"
    assert spec.description == "Overridden description"


def test_malformed_job_data(mock_workspace, mock_serializer, mock_deserializer, tmp_path):
    # Prepare malformed objects using hybrid approach
    malformed_objects = [
        make_hybrid_job(1, "Good", [make_obj_task("valid")]),
        make_hybrid_job(2, "Empty", []),
        make_hybrid_job(3, "Survival", [make_obj_task("survival")]),
    ]
    mock_workspace.fetch_jobs.return_value = malformed_objects
    mock_deserializer.return_value = SimpleNamespace(jobs=malformed_objects)

    component = DatabricksWorkspaceComponent(workspace=mock_workspace)
    state_path = tmp_path / "malformed_state.json"
    asyncio.run(component.write_state_to_path(state_path))

    defs = component.build_defs_from_state(context=None, state_path=state_path)
    assert defs.assets is not None
    asset_keys = defs.resolve_asset_graph().get_all_asset_keys()

    assert AssetKey(["good", "valid"]) in asset_keys
    assert AssetKey(["survival", "survival"]) in asset_keys


def test_databricks_asset_execution(mock_workspace, mock_serializer, mock_deserializer, tmp_path):
    """Test that materializing the asset actually calls the Databricks Client."""
    # Setup mocks to return a valid Run object when run_now is called
    mock_client = mock_workspace.get_client.return_value
    mock_run = MagicMock()
    mock_run.run_id = 999
    mock_run.run_page_url = "https://fake-url.com"

    mock_client.jobs.run_now.return_value = mock_run

    mock_run_info = MagicMock()
    mock_run_info.state.result_state = RunResultState.SUCCESS
    mock_client.jobs.get_run.return_value = mock_run_info

    mock_deserializer.return_value = SimpleNamespace(jobs=MOCK_JOBS_HYBRID)
    component = DatabricksWorkspaceComponent(workspace=mock_workspace)

    state_path = tmp_path / "state.json"
    asyncio.run(component.write_state_to_path(state_path))
    defs = component.build_defs_from_state(context=None, state_path=state_path)
    assert defs.assets is not None
    assets_to_run = [a for a in defs.assets if isinstance(a, (AssetsDefinition, AssetSpec))]

    result = materialize(assets=assets_to_run)
    assert result.success

    calls_for_101 = [
        call for call in mock_client.jobs.run_now.call_args_list if call.kwargs.get("job_id") == 101
    ]
    assert len(calls_for_101) == 1, "Job 101 should execute exactly once for all its tasks"

    calls_for_102 = [
        call for call in mock_client.jobs.run_now.call_args_list if call.kwargs.get("job_id") == 102
    ]
    assert len(calls_for_102) == 1

    mock_client.jobs.wait_get_run_job_terminated_or_skipped.assert_called_with(999)


def test_databricks_execution_failure(mock_workspace, mock_serializer, mock_deserializer, tmp_path):
    """Test that a failed Databricks job raises an exception in Dagster."""
    mock_client = mock_workspace.get_client.return_value
    mock_run = MagicMock()
    mock_run.run_id = 666
    mock_run.run_page_url = "https://failure-url.com"
    mock_client.jobs.run_now.return_value = mock_run

    mock_run_info = MagicMock()
    mock_run_info.state.result_state = RunResultState.FAILED
    mock_client.jobs.get_run.return_value = mock_run_info

    mock_deserializer.return_value = SimpleNamespace(jobs=MOCK_JOBS_HYBRID)
    component = DatabricksWorkspaceComponent(workspace=mock_workspace)

    state_path = tmp_path / "state.json"
    asyncio.run(component.write_state_to_path(state_path))

    defs = component.build_defs_from_state(context=None, state_path=state_path)

    assert defs.assets is not None

    target_key = AssetKey(["data_ingestion_job", "ingest_task"])

    job_assets = [
        a for a in defs.assets if isinstance(a, AssetsDefinition) and target_key in a.keys
    ]

    with pytest.raises(Exception) as excinfo:
        materialize(assets=job_assets)

    assert "Job 101 failed: FAILED" in str(excinfo.value)
    mock_client.jobs.wait_get_run_job_terminated_or_skipped.assert_called_with(666)


def test_databricks_fetch_jobs_pagination():
    """Test that fetch_jobs paginates through all pages of the Databricks Jobs API."""
    workspace = DatabricksWorkspace(host="https://fake.databricks.com", token="fake-token")

    page1_data = {
        "jobs": [
            {"job_id": 1, "settings": {"name": "Job1"}},
            {"job_id": 2, "settings": {"name": "Job2"}},
        ],
        "has_more": True,
        "next_page_token": "token1",
    }
    page2_data = {
        "jobs": [{"job_id": 3, "settings": {"name": "Job3"}}],
        "has_more": False,
    }

    call_count = 0
    captured_params: list[dict] = []

    @asynccontextmanager
    async def mock_get(url, params=None):
        nonlocal call_count
        captured_params.append(dict(params) if params else {})
        resp = AsyncMock()
        if call_count == 0:
            resp.json = AsyncMock(return_value=page1_data)
        else:
            resp.json = AsyncMock(return_value=page2_data)
        resp.raise_for_status = MagicMock()
        call_count += 1
        yield resp

    @asynccontextmanager
    async def mock_session_get_single(url):
        """Mock for individual job GET requests."""
        resp = AsyncMock()
        resp.status = 200
        resp.json = AsyncMock(
            return_value={
                "job_id": 1,
                "settings": {
                    "name": "Job1",
                    "tasks": [{"task_key": "t1", "notebook_task": {"notebook_path": "/test"}}],
                },
            }
        )
        resp.raise_for_status = MagicMock()
        yield resp

    @asynccontextmanager
    async def mock_client_session(headers=None):
        session = MagicMock()
        session.get = mock_get
        yield session

    @asynccontextmanager
    async def mock_client_session_single(headers=None):
        session = MagicMock()
        session.get = mock_session_get_single
        yield session

    session_call_count = 0
    original_mock_client_session = mock_client_session
    original_mock_client_session_single = mock_client_session_single

    @asynccontextmanager
    async def mock_client_session_dispatch(headers=None):
        nonlocal session_call_count
        if session_call_count == 0:
            session_call_count += 1
            async with original_mock_client_session(headers=headers) as s:
                yield s
        else:
            async with original_mock_client_session_single(headers=headers) as s:
                yield s

    with patch("aiohttp.ClientSession", side_effect=mock_client_session_dispatch):
        jobs = asyncio.run(workspace.fetch_jobs(databricks_filter=None))

    # All 3 jobs from both pages should be fetched
    assert len(jobs) == 3
    # First call should have no page_token
    assert captured_params[0] == {}
    # Second call should pass the page_token
    assert captured_params[1] == {"page_token": "token1"}


def test_databricks_fetch_jobs_rate_limit_retry():
    """Test that individual job fetches retry on HTTP 429."""
    workspace = DatabricksWorkspace(host="https://fake.databricks.com", token="fake-token")

    list_data = {
        "jobs": [{"job_id": 1, "settings": {"name": "Job1"}}],
        "has_more": False,
    }

    @asynccontextmanager
    async def mock_list_get(url, params=None):
        resp = AsyncMock()
        resp.json = AsyncMock(return_value=list_data)
        resp.raise_for_status = MagicMock()
        yield resp

    single_call_count = 0

    @asynccontextmanager
    async def mock_single_get(url):
        nonlocal single_call_count
        resp = AsyncMock()
        if single_call_count == 0:
            resp.status = 429
            single_call_count += 1
        else:
            resp.status = 200
            resp.json = AsyncMock(
                return_value={
                    "job_id": 1,
                    "settings": {
                        "name": "Job1",
                        "tasks": [{"task_key": "t1", "notebook_task": {"notebook_path": "/test"}}],
                    },
                }
            )
            resp.raise_for_status = MagicMock()
        yield resp

    session_idx = 0

    @asynccontextmanager
    async def mock_client_session(headers=None):
        nonlocal session_idx
        session = MagicMock()
        if session_idx == 0:
            session.get = mock_list_get
            session_idx += 1
        else:
            session.get = mock_single_get
        yield session

    with (
        patch("aiohttp.ClientSession", side_effect=mock_client_session),
        patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        jobs = asyncio.run(workspace.fetch_jobs(databricks_filter=None))

    assert len(jobs) == 1
    assert jobs[0].name == "Job1"
    # Verify sleep was called for the rate-limit retry
    mock_sleep.assert_called_once_with(1)
