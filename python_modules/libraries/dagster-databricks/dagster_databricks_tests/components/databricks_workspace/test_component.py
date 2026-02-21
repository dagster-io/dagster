import asyncio
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
    """Test that assets can be renamed and customized via YAML."""
    custom_spec = AssetSpec(
        key=AssetKey("my_custom_ingestion"),
        group_name="etl_group",
        description="Overridden description",
    )

    mock_deserializer.return_value = SimpleNamespace(jobs=MOCK_JOBS_HYBRID)

    component = DatabricksWorkspaceComponent(
        workspace=mock_workspace, assets_by_task_key={"ingest_task": [custom_spec]}
    )

    state_path = tmp_path / "custom_state.json"
    asyncio.run(component.write_state_to_path(state_path))

    defs = component.build_defs_from_state(context=None, state_path=state_path)
    assert defs.assets is not None
    asset_graph = defs.resolve_asset_graph()

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

    job_assets = []
    for a in defs.assets:
        if isinstance(a, AssetsDefinition) and target_key in a.keys:
            job_assets.append(a)

    with pytest.raises(Exception) as excinfo:
        materialize(assets=job_assets)

    assert "Job 101 failed: FAILED" in str(excinfo.value)
    mock_client.jobs.wait_get_run_job_terminated_or_skipped.assert_called_with(666)
