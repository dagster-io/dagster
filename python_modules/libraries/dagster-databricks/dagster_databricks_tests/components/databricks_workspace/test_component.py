from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from dagster import AssetKey, Definitions
from dagster._utils.test.definitions import scoped_definitions_load_context
from dagster.components.testing import create_defs_folder_sandbox
from dagster_databricks.components.databricks_asset_bundle.configs import Job
from dagster_databricks.components.databricks_workspace.component import (
    DatabricksWorkspaceComponent,
)
from dagster_shared.serdes.serdes import deserialize_value, serialize_value

MOCK_JOBS_DATA = [
    Job(
        job_id=101,
        settings={"name": "Data Ingestion Job"},
        tasks=[{"task_key": "ingest_task", "description": "Ingests data"}],
    ),
    Job(
        job_id=102,
        settings={"name": "ML Training Job"},
        tasks=[
            {"task_key": "prepare_data", "description": "Prep"},
            {"task_key": "train_model", "description": "Train"},
        ],
    ),
]

COMPONENT_YAML = {
    "type": "dagster_databricks.DatabricksWorkspaceComponent",
    "attributes": {
        "workspace": {"host": "https://fake-workspace.cloud.databricks.com", "token": "fake-token"},
        "databricks_filter": {"include_jobs": {"job_ids": [101, 102]}},
    },
}

# --- Fixtures & Helpers ---


@pytest.fixture
def mock_fetcher():
    with patch(
        "dagster_databricks.components.databricks_workspace.component.fetch_databricks_workspace_data",
        new_callable=AsyncMock,
    ) as mock:
        mock.return_value = MOCK_JOBS_DATA
        yield mock


@contextmanager
def setup_databricks_component(
    defs_yaml_contents: dict[str, Any],
) -> Iterator[tuple[DatabricksWorkspaceComponent, Definitions]]:
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=DatabricksWorkspaceComponent,
            defs_yaml_contents=defs_yaml_contents,
        )
        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
        ):
            yield component, defs


# --- Tests ---
def test_databricks_workspace_loading(mock_fetcher):
    """Test that the component correctly loads jobs and converts them to assets."""
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=DatabricksWorkspaceComponent,
            defs_yaml_contents=COMPONENT_YAML,
        )

        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
        ):
            assert isinstance(component, DatabricksWorkspaceComponent)

            mock_fetcher.assert_called_once()

            asset_keys = defs.resolve_asset_graph().get_all_asset_keys()

            assert AssetKey(["ingest_task"]) in asset_keys

            assert AssetKey(["prepare_data"]) in asset_keys

            assert AssetKey(["train_model"]) in asset_keys

            assert len(asset_keys) == 3


def test_databricks_filtering(mock_fetcher):
    """Test that jobs are correctly filtered based on config."""

    def side_effect(client, databricks_filter):
        filtered_results = []
        for job in MOCK_JOBS_DATA:
            job_as_dict = {"job_id": job.job_id}

            if databricks_filter.include_job(job_as_dict):
                filtered_results.append(job)
        return filtered_results

    mock_fetcher.side_effect = side_effect
    filter_yaml = {
        "type": "dagster_databricks.DatabricksWorkspaceComponent",
        "attributes": {
            "workspace": {"host": "https://fake.com", "token": "fake"},
            "databricks_filter": {"include_jobs": {"job_ids": [101]}},
        },
    }

    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=DatabricksWorkspaceComponent,
            defs_yaml_contents=filter_yaml,
        )

        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
        ):
            asset_keys = defs.resolve_asset_graph().get_all_asset_keys()

            assert AssetKey(["ingest_task"]) in asset_keys

            assert AssetKey(["prepare_data"]) not in asset_keys
            assert AssetKey(["train_model"]) not in asset_keys

            assert len(asset_keys) == 1


def test_databricks_custom_asset_mapping(mock_fetcher):
    """Test that assets can be renamed and customized via YAML."""
    custom_yaml = {
        "type": "dagster_databricks.DatabricksWorkspaceComponent",
        "attributes": {
            "workspace": {"host": "https://fake.com", "token": "fake"},
            "databricks_filter": {"include_jobs": {"job_ids": [101]}},
            "assets_by_task_key": {
                "ingest_task": {
                    "key": "my_custom_ingestion",
                    "group": "etl_group",
                    "description": "Overridden description",
                }
            },
        },
    }

    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=DatabricksWorkspaceComponent,
            defs_yaml_contents=custom_yaml,
        )

        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
        ):
            asset_graph = defs.resolve_asset_graph()
            all_keys = asset_graph.get_all_asset_keys()

            assert AssetKey(["ingest_task"]) not in all_keys

            custom_key = AssetKey(["my_custom_ingestion"])
            assert custom_key in all_keys

            spec = asset_graph.get(custom_key)
            assert spec.group_name == "etl_group"
            assert spec.description == "Overridden description"
            assert "databricks" in spec.kinds


def test_databricks_workspace_custom_translation(mock_fetcher):
    """Test overriding asset specs via assets_by_task_key."""
    custom_yaml = {
        "type": "dagster_databricks.DatabricksWorkspaceComponent",
        "attributes": {
            "workspace": {
                "host": "https://fake-workspace.cloud.databricks.com",
                "token": "fake-token",
            },
            "databricks_filter": {"include_jobs": {"job_ids": [101]}},
            "assets_by_task_key": {
                "ingest_task": {
                    "key": "custom_ingestion_asset",
                    "group": "etl_pipeline",
                    "description": "Custom description override",
                }
            },
        },
    }

    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=DatabricksWorkspaceComponent,
            defs_yaml_contents=custom_yaml,
        )

        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
        ):
            asset_graph = defs.resolve_asset_graph()
            all_keys = asset_graph.get_all_asset_keys()

            assert AssetKey("ingest_task") not in all_keys

            custom_key = AssetKey("custom_ingestion_asset")
            assert custom_key in all_keys

            spec = asset_graph.get(custom_key)
            assert spec.group_name == "etl_pipeline"
            assert spec.description == "Custom description override"
            assert "databricks" in spec.kinds


def test_state_serialization():
    """Test that the Job model can be serialized and deserialized correctly."""
    original_jobs = [
        Job(
            job_id=123,
            settings={"name": "Complex Job"},
            tasks=[
                {"task_key": "task_a", "notebook_task": {"source": "git"}},
                {"task_key": "task_b", "spark_python_task": {"parameters": ["--foo", "bar"]}},
            ],
        )
    ]

    serialized = serialize_value(original_jobs)

    deserialized = deserialize_value(serialized, list[Job])

    assert len(deserialized) == 1
    assert deserialized[0].job_id == 123
    assert len(deserialized[0].tasks) == 2
    assert deserialized[0].tasks[0]["task_key"] == "task_a"


def test_malformed_job_data(mock_fetcher):
    """Test that the component handles jobs with missing data gracefully."""
    mock_fetcher.return_value = [
        Job(job_id=1, settings={"name": "Good"}, tasks=[{"task_key": "valid"}]),
        Job(job_id=2, settings={"name": "Empty"}, tasks=[]),
        Job(job_id=3, settings=None, tasks=[{"task_key": "survival"}]),
    ]

    with setup_databricks_component(defs_yaml_contents=COMPONENT_YAML) as (component, defs):
        asset_keys = defs.resolve_asset_graph().get_all_asset_keys()
        assert AssetKey(["valid"]) in asset_keys
        assert AssetKey(["survival"]) in asset_keys
