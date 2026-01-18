"""Tests for selector file generation when selection exceeds threshold."""

import textwrap
from pathlib import Path
from unittest import mock

import pytest
from dagster_dbt import DbtCliResource
from dagster_dbt.asset_utils import _parse_selection_args


class TestParseSelectionArgs:
    """Unit tests for _parse_selection_args helper function."""

    def test_select_only(self):
        """Test parsing args with only --select."""
        args = ["--select", "model1 model2 model3"]
        select, exclude = _parse_selection_args(args)
        assert select == ["model1", "model2", "model3"]
        assert exclude is None

    def test_exclude_only(self):
        """Test parsing args with only --exclude."""
        args = ["--exclude", "model1 model2"]
        select, exclude = _parse_selection_args(args)
        assert select is None
        assert exclude == ["model1", "model2"]

    def test_select_and_exclude(self):
        """Test parsing args with both --select and --exclude."""
        args = ["--select", "model1 model2 model3", "--exclude", "model2"]
        select, exclude = _parse_selection_args(args)
        assert select == ["model1", "model2", "model3"]
        assert exclude == ["model2"]

    def test_empty_args(self):
        """Test parsing empty args."""
        args: list[str] = []
        select, exclude = _parse_selection_args(args)
        assert select is None
        assert exclude is None

    def test_selector_arg_ignored(self):
        """Test that --selector args are ignored (not parsed as select/exclude)."""
        args = ["--selector", "my_selector"]
        select, exclude = _parse_selection_args(args)
        assert select is None
        assert exclude is None


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


def test_temp_selector_file_includes_exclude(large_dbt_project: tuple[Path, dict]):
    """Test that --exclude arguments are incorporated into the generated selectors.yml.

    This test verifies that when both --select and --exclude are present and exceed
    the threshold, the exclude is properly included in the selectors.yml definition,
    and that the excluded model is not actually materialized.
    """
    import yaml
    from dagster import AssetExecutionContext, AssetKey, materialize
    from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

    project_dir, manifest = large_dbt_project

    # Create DbtProject for metadata
    dbt_project = DbtProject(project_dir=str(project_dir))

    # Track the selectors.yml content that gets written
    captured_selectors: list[dict] = []
    original_write_text = Path.write_text

    def intercepting_write_text(self, content, *args, **kwargs):
        if self.name == "selectors.yml":
            captured_selectors.append(yaml.safe_load(content))
        return original_write_text(self, content, *args, **kwargs)

    # Create a large select expression that exceeds the threshold when combined with exclude
    # This simulates a user providing a large --select with --exclude
    model_names = [f"model_{i}" for i in range(_NUM_MODELS)]
    large_select = " ".join(model_names)

    @dbt_assets(manifest=manifest, project=dbt_project, select=large_select, exclude="model_0")
    def my_dbt_assets_with_exclude(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["run"], context=context).stream()

    # Materialize all assets (not a subset) - this uses default_dbt_selection
    # which includes both --select and --exclude from the decorator
    # Patch selection args threshold to a low value for testing
    with (
        mock.patch("dagster_dbt.asset_utils._SELECTION_ARGS_THRESHOLD", 5),
        mock.patch.object(Path, "write_text", intercepting_write_text),
    ):
        result = materialize(
            [my_dbt_assets_with_exclude],
            resources={"dbt": DbtCliResource(project_dir=str(project_dir))},
            raise_on_error=False,
        )

    assert result.success, "Dbt run with exclude should succeed."

    # Verify that selectors.yml was written with exclude
    assert len(captured_selectors) > 0, "selectors.yml should have been written"
    selector_content = captured_selectors[0]

    # Verify structure of generated selectors.yml
    assert "selectors" in selector_content
    assert len(selector_content["selectors"]) == 1
    selector_def = selector_content["selectors"][0]["definition"]

    # Verify union is present (from --select)
    assert "union" in selector_def, "Selector should have union key"
    union_items = selector_def["union"]

    # The union should contain all model names plus an exclude dict
    # _NUM_MODELS items + 1 exclude dict = _NUM_MODELS + 1
    assert len(union_items) == _NUM_MODELS + 1

    # Verify exclude is present as an item in the union (dbt requires this structure)
    exclude_item = union_items[-1]
    assert isinstance(exclude_item, dict), "Last union item should be exclude dict"
    assert "exclude" in exclude_item, "Should have exclude key"
    assert exclude_item["exclude"] == ["model_0"]

    # Verify the excluded model was not actually materialized
    materialized_keys = result.get_asset_materialization_events()
    materialized_asset_keys = {
        event.asset_key for event in materialized_keys if event.asset_key is not None
    }
    excluded_key = AssetKey(["large_project", "model_0"])
    assert excluded_key not in materialized_asset_keys, "model_0 should not be materialized"

    # Verify other models were materialized
    assert len(materialized_asset_keys) == _NUM_MODELS - 1, (
        f"Expected {_NUM_MODELS - 1} models to be materialized, got {len(materialized_asset_keys)}"
    )
