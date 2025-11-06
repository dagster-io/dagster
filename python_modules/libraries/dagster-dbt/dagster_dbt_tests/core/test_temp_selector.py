"""Tests for selector file generation when selection exceeds threshold."""

import textwrap
from pathlib import Path
from unittest import mock

import pytest
from dagster_dbt import DbtCliResource

_EXISTING_SELECTORS_CONTENT = textwrap.dedent("""
selectors:
  - name: existing_selector
    definition:
      method: fqn
      value: ['model', 'large_project', 'models', 'model_0']

""").strip()

_NUM_MODELS = 20


@pytest.fixture(params=[True, False], ids=["with_existing_selectors", "without_existing_selectors"])
def large_dbt_project(tmp_path_factory, request):
    f"""Create a real dbt project with 260 models to test selector file logic.

    Creates #{_NUM_MODELS} total.
    """
    has_existing_selectors = request.param

    project_dir = tmp_path_factory.mktemp("large_dbt_project")

    # Create dbt_project.yml
    (project_dir / "dbt_project.yml").write_text(
        textwrap.dedent(
            """
        name: large_project
        config-version: 2
        version: "1.0"
        profile: large_project
        model-paths: ["models"]
        target-path: "target"
        """
        ).strip()
    )

    # Create profiles.yml
    (project_dir / "profiles.yml").write_text(
        textwrap.dedent(
            """
        large_project:
          target: dev
          outputs:
            dev:
              type: duckdb
              path: ':memory:'
              schema: main
        """
        ).strip()
    )

    if has_existing_selectors:
        (project_dir / "selectors.yml").write_text(_EXISTING_SELECTORS_CONTENT)

    # Create models directory and generate 260 simple SQL models
    models_dir = project_dir / "models"
    models_dir.mkdir()

    for i in range(_NUM_MODELS):
        model_file = models_dir / f"model_{i}.sql"
        # Each model is a simple select statement
        model_file.write_text(f"select {i} as id, 'model_{i}' as name")

    # Create empty dbt_packages directory
    (project_dir / "dbt_packages").mkdir()

    # Run dbt parse to generate manifest
    dbt = DbtCliResource(project_dir=str(project_dir), global_config_flags=["--quiet"])
    invocation = dbt.cli(["parse"]).wait()

    # Get the manifest from the invocation and return both project_dir and manifest
    manifest = invocation.get_artifact("manifest.json")

    return project_dir, manifest


def test_temp_selector_file_used_with_many_models(large_dbt_project: tuple[Path, dict], caplog):
    f"""Test that selector file is created and cleaned up when selecting models that exceed threshold.

    This test creates a real dbt project with {_NUM_MODELS} models, selects a subset of them,
    and verifies that:
    1. A selector file is created
    2. The selector file is cleaned up after the dbt invocation completes
    3. Appropriate log messages are emitted
    """
    from dagster import AssetExecutionContext, materialize
    from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

    project_dir, manifest = large_dbt_project
    has_existing_selectors = (project_dir / "selectors.yml").exists()

    # Create DbtProject for metadata
    dbt_project = DbtProject(project_dir=str(project_dir))

    @dbt_assets(manifest=manifest, project=dbt_project)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["run"], context=context).stream()

    subset_size = _NUM_MODELS - 5

    # Select 250 models (subset that exceeds threshold)
    all_keys = list(my_dbt_assets.keys)
    selected_keys = all_keys[:subset_size]

    # Materialize with subset selection - runs real dbt
    # Patch selection args threshold to 10 for testing
    with mock.patch("dagster_dbt.asset_utils._SELECTION_ARGS_THRESHOLD", 10):
        result = materialize(
            [my_dbt_assets],
            resources={"dbt": DbtCliResource(project_dir=str(project_dir))},
            selection=selected_keys,
            raise_on_error=False,
        )
    assert result.success, "Dbt run with large selection should succeed."

    # Verify logging: selector creation was logged
    creation_logged = any(
        "Executing materialization against temporary copy of DBT project" in record.message
        and f"{subset_size} resources" in record.message
        for record in caplog.records
    )
    assert creation_logged, "Should log selector creation with resource count"

    selectors_path = project_dir / "selectors.yml"
    if has_existing_selectors:
        # Verify existing selectors file was preserved
        assert selectors_path.exists(), "Existing selectors.yml should be restored."
        content = selectors_path.read_text().strip()
        assert content == _EXISTING_SELECTORS_CONTENT, (
            "Existing selectors.yml content should be unchanged."
        )
