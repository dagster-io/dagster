import json
from pathlib import Path
from typing import Any

import pytest
from dagster import AssetMaterialization, TableColumn, TableSchema
from dagster._core.definitions.metadata import TableMetadataSet
from dagster_dbt import DbtCliResource

pytestmark = pytest.mark.derived_metadata


@pytest.mark.parametrize("path_type", ["omitted", "memory", "relative", "absolute"])
def test_duckdb_metadata_from_attached_database(tmp_path: Path, path_type: str) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "dbt_project.yml").write_text(
        json.dumps({"name": "test_metadata", "profile": "test_metadata", "config-version": 2})
    )
    profile: dict[str, Any] = {
        "type": "duckdb",
        "schema": "main",
        "attach": [{"path": str(tmp_path / "warehouse.duckdb"), "alias": "warehouse"}],
    }
    if path_type == "memory":
        profile["path"] = ":memory:"
    elif path_type == "relative":
        profile["path"] = "local.duckdb"
    elif path_type == "absolute":
        profile["path"] = str(tmp_path / "local.duckdb")
    (project_dir / "profiles.yml").write_text(
        json.dumps({"test_metadata": {"target": "dev", "outputs": {"dev": profile}}})
    )
    models_dir = project_dir / "models"
    models_dir.mkdir()
    (models_dir / "customers.sql").write_text(
        "{{ config(materialized='table', database='warehouse') }} "
        "select 1::integer as id, 2::integer as quantity"
    )

    dbt = DbtCliResource(project_dir=project_dir)
    manifest = dbt.cli(["parse"]).wait().get_artifact("manifest.json")
    invocation = dbt.cli(["build"], manifest=manifest)
    try:
        events = list(
            invocation.stream().fetch_column_metadata(with_column_lineage=False).fetch_row_counts()
        )
        materializations = [event for event in events if isinstance(event, AssetMaterialization)]
        assert len(materializations) == 1
        metadata = TableMetadataSet.extract(materializations[0].metadata)
        assert metadata.column_schema == TableSchema(
            columns=[TableColumn("id", type="INTEGER"), TableColumn("quantity", type="INTEGER")]
        )
        assert metadata.row_count == 1
    finally:
        if invocation.adapter:
            invocation.adapter.cleanup_connections()
