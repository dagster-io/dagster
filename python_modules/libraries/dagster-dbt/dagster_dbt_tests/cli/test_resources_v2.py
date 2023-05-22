from typing import List

import pytest
from dagster import AssetObservation, Output
from dagster_dbt.cli import DbtCli, DbtCliEventMessage, DbtManifest

from ..conftest import TEST_PROJECT_DIR

pytest.importorskip("dbt.version", minversion="1.4")


manifest_path = f"{TEST_PROJECT_DIR}/manifest.json"
manifest = DbtManifest.read(path=manifest_path)


@pytest.mark.parametrize("global_config", [[], ["--debug"]])
@pytest.mark.parametrize("command", ["run", "parse"])
def test_dbt_cli(global_config: List[str], command: str) -> None:
    dbt = DbtCli(project_dir=TEST_PROJECT_DIR, global_config=global_config)
    dbt_cli_task = dbt.cli([command], manifest=manifest)

    list(dbt_cli_task.stream())

    assert dbt_cli_task.process.args == ["dbt", *global_config, command]
    assert dbt_cli_task.process.returncode == 0


@pytest.mark.parametrize(
    "data",
    [
        {},
        {
            "node_info": {
                "unique_id": "a.b.c",
                "resource_type": "model",
                "node_status": "failure",
                "node_finished_at": "2024-01-01T00:00:00Z",
            }
        },
        {
            "node_info": {
                "unique_id": "a.b.c",
                "resource_type": "macro",
                "node_status": "success",
                "node_finished_at": "2024-01-01T00:00:00Z",
            }
        },
        {
            "node_info": {
                "unique_id": "a.b.c",
                "resource_type": "model",
                "node_status": "failure",
            }
        },
        {
            "node_info": {
                "unique_id": "a.b.c",
                "resource_type": "test",
                "node_status": "success",
            }
        },
    ],
    ids=[
        "node info missing",
        "node status failure",
        "not refable",
        "not successful execution",
        "not finished test execution",
    ],
)
def test_no_default_asset_events_emitted(data: dict) -> None:
    manifest = DbtManifest(raw_manifest={})
    asset_events = DbtCliEventMessage(event={"data": data}).to_default_asset_events(
        manifest=manifest
    )

    assert list(asset_events) == []


def test_to_default_asset_output_events() -> None:
    manifest = DbtManifest(raw_manifest={})
    event = {
        "data": {
            "node_info": {
                "unique_id": "a.b.c",
                "resource_type": "model",
                "node_status": "success",
                "node_finished_at": "2024-01-01T00:00:00Z",
            }
        }
    }
    asset_events = list(DbtCliEventMessage(event=event).to_default_asset_events(manifest=manifest))

    assert len(asset_events) == 1
    assert all(isinstance(e, Output) for e in asset_events)


def test_to_default_asset_observation_events() -> None:
    manifest = DbtManifest(
        raw_manifest={
            "nodes": {
                "a.b.c.d": {
                    "resource_type": "model",
                    "config": {},
                    "name": "model",
                }
            },
            "sources": {
                "a.b.c.d.e": {
                    "resource_type": "source",
                    "source_name": "test",
                    "name": "source",
                }
            },
            "parent_map": {
                "a.b.c": [
                    "a.b.c.d",
                    "a.b.c.d.e",
                ]
            },
        }
    )
    event = {
        "data": {
            "node_info": {
                "unique_id": "a.b.c",
                "resource_type": "test",
                "node_status": "success",
                "node_finished_at": "2024-01-01T00:00:00Z",
            }
        }
    }
    asset_events = list(DbtCliEventMessage(event=event).to_default_asset_events(manifest=manifest))

    assert len(asset_events) == 2
    assert all(isinstance(e, AssetObservation) for e in asset_events)
