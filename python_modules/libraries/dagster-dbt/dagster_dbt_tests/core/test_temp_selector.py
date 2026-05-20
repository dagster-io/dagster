"""Tests for selector file generation when selection exceeds threshold."""

import textwrap
from pathlib import Path
from typing import cast
from unittest import mock

import pytest
from dagster_dbt import DbtCliResource
from dagster_dbt.asset_utils import _parse_selection_args, extract_runtime_selection_from_args


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


class TestExtractRuntimeSelectionFromArgs:
    """Unit tests for extract_runtime_selection_from_args helper."""

    def test_space_separated_exclude(self):
        cleaned, selects, excludes = extract_runtime_selection_from_args(
            ["build", "--exclude", "resource_type:test"]
        )
        assert cleaned == ["build"]
        assert selects == []
        assert excludes == ["resource_type:test"]

    def test_equals_form_exclude(self):
        cleaned, _, excludes = extract_runtime_selection_from_args(
            ["build", "--exclude=resource_type:test"]
        )
        assert cleaned == ["build"]
        assert excludes == ["resource_type:test"]

    def test_multiple_exclude_flags_aggregate(self):
        cleaned, _, excludes = extract_runtime_selection_from_args(
            ["build", "--exclude", "resource_type:test", "--exclude", "tag:slow"]
        )
        assert cleaned == ["build"]
        assert excludes == ["resource_type:test", "tag:slow"]

    def test_space_separated_values_in_single_flag(self):
        cleaned, _, excludes = extract_runtime_selection_from_args(
            ["build", "--exclude", "resource_type:test tag:slow"]
        )
        assert cleaned == ["build"]
        assert excludes == ["resource_type:test", "tag:slow"]

    def test_select_short_and_long_flags(self):
        cleaned, selects, _ = extract_runtime_selection_from_args(
            ["build", "-s", "model_a", "--models", "model_b"]
        )
        assert cleaned == ["build"]
        assert selects == ["model_a", "model_b"]

    def test_select_and_exclude_together(self):
        cleaned, selects, excludes = extract_runtime_selection_from_args(
            ["build", "--select", "model_a", "--exclude", "resource_type:test"]
        )
        assert cleaned == ["build"]
        assert selects == ["model_a"]
        assert excludes == ["resource_type:test"]

    def test_vars_payload_containing_flag_string_is_preserved(self):
        # A --vars JSON payload that happens to contain "--exclude" as a string value
        # must not be mis-stripped; parsing is token-indexed so the JSON argv is opaque.
        vars_payload = '{"key": "--exclude resource_type:test"}'
        cleaned, selects, excludes = extract_runtime_selection_from_args(
            ["build", "--vars", vars_payload]
        )
        assert cleaned == ["build", "--vars", vars_payload]
        assert selects == []
        assert excludes == []

    def test_unrelated_args_untouched(self):
        cleaned, selects, excludes = extract_runtime_selection_from_args(
            ["run-operation", "my_macro", "--args", '{"k": "v"}']
        )
        assert cleaned == ["run-operation", "my_macro", "--args", '{"k": "v"}']
        assert selects == []
        assert excludes == []

    def test_empty_args(self):
        cleaned, selects, excludes = extract_runtime_selection_from_args([])
        assert cleaned == []
        assert selects == []
        assert excludes == []


def test_runtime_exclude_folded_into_generated_selector(
    large_dbt_project: tuple[Path, dict],
):
    """Runtime --exclude on dbt.cli() is merged into the generated selector yaml's exclude
    list and stripped from the dbt CLI args, so dbt does not silently ignore it.
    """
    import yaml
    from dagster import AssetExecutionContext, AssetKey, materialize
    from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

    project_dir, manifest = large_dbt_project
    dbt_project = DbtProject(project_dir=str(project_dir))

    captured_selectors: list[dict] = []
    captured_argv: list[list[str]] = []
    original_write_text = Path.write_text

    def intercepting_write_text(self, content, *args, **kwargs):
        if self.name == "selectors.yml":
            captured_selectors.append(yaml.safe_load(content))
        return original_write_text(self, content, *args, **kwargs)

    @dbt_assets(manifest=manifest, project=dbt_project)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        invocation = dbt.cli(
            ["run", "--exclude", "model_0"],
            context=context,
        ).wait()
        captured_argv.append(cast("list[str]", invocation.process.args))
        yield from invocation.stream()

    # Materialize an explicit subset so get_subset_selection_for_context enumerates the
    # selected resources (triggering the selector-yaml branch under the patched threshold).
    subset = list(my_dbt_assets.keys)[: _NUM_MODELS - 2]

    with (
        mock.patch("dagster_dbt.asset_utils._SELECTION_ARGS_THRESHOLD", 5),
        mock.patch.object(Path, "write_text", intercepting_write_text),
    ):
        result = materialize(
            [my_dbt_assets],
            resources={"dbt": DbtCliResource(project_dir=str(project_dir))},
            selection=subset,
            raise_on_error=False,
        )

    assert result.success, "Dbt run with runtime --exclude should succeed."
    assert captured_selectors, "A selector yaml should have been written."

    selector_def = captured_selectors[0]["selectors"][0]["definition"]
    assert "union" in selector_def
    exclude_item = selector_def["union"][-1]
    assert isinstance(exclude_item, dict)
    assert "exclude" in exclude_item
    assert "model_0" in exclude_item["exclude"], (
        "runtime --exclude value should be folded into the selector yaml"
    )

    assert captured_argv, "The dbt CLI invocation should have been captured."
    argv = captured_argv[0]
    assert "--selector" in argv, "selector flag should have been injected"
    assert "--exclude" not in argv, (
        "runtime --exclude should be stripped from dbt argv so dbt does not silently ignore it"
    )

    # The excluded model should not be materialized.
    materialized_asset_keys = {
        event.asset_key
        for event in result.get_asset_materialization_events()
        if event.asset_key is not None
    }
    assert AssetKey(["large_project", "model_0"]) not in materialized_asset_keys


def test_runtime_select_folded_into_generated_selector(
    large_dbt_project: tuple[Path, dict],
):
    """Runtime --select on dbt.cli() is merged into the generated selector yaml's union
    list and stripped from the dbt CLI args, so dbt does not silently ignore it.
    """
    import yaml
    from dagster import AssetExecutionContext, materialize
    from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

    project_dir, manifest = large_dbt_project
    dbt_project = DbtProject(project_dir=str(project_dir))

    captured_selectors: list[dict] = []
    captured_argv: list[list[str]] = []
    original_write_text = Path.write_text

    def intercepting_write_text(self, content, *args, **kwargs):
        if self.name == "selectors.yml":
            captured_selectors.append(yaml.safe_load(content))
        return original_write_text(self, content, *args, **kwargs)

    @dbt_assets(manifest=manifest, project=dbt_project)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        invocation = dbt.cli(
            ["run", "--select", "model_0"],
            context=context,
        ).wait()
        captured_argv.append(cast("list[str]", invocation.process.args))
        yield from invocation.stream()

    subset = list(my_dbt_assets.keys)[: _NUM_MODELS - 2]

    with (
        mock.patch("dagster_dbt.asset_utils._SELECTION_ARGS_THRESHOLD", 5),
        mock.patch.object(Path, "write_text", intercepting_write_text),
    ):
        result = materialize(
            [my_dbt_assets],
            resources={"dbt": DbtCliResource(project_dir=str(project_dir))},
            selection=subset,
            raise_on_error=False,
        )

    assert result.success, "Dbt run with runtime --select should succeed."
    assert captured_selectors, "A selector yaml should have been written."

    selector_def = captured_selectors[0]["selectors"][0]["definition"]
    assert "union" in selector_def
    assert "model_0" in selector_def["union"], (
        "runtime --select value should be folded into the selector yaml union"
    )

    assert captured_argv, "The dbt CLI invocation should have been captured."
    argv = captured_argv[0]
    assert "--selector" in argv, "selector flag should have been injected"
    assert "--select" not in argv, (
        "runtime --select should be stripped from dbt argv so dbt does not silently ignore it"
    )


def test_runtime_exclude_reinjected_below_threshold(
    large_dbt_project: tuple[Path, dict],
):
    """Below the selector threshold, runtime --exclude is extracted from user args and
    re-injected into the dagster-generated selection_args. dbt still sees --exclude
    exactly once with the user's value; the user-args portion no longer contains it.
    """
    from dagster import AssetExecutionContext, materialize
    from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

    project_dir, manifest = large_dbt_project
    dbt_project = DbtProject(project_dir=str(project_dir))

    captured_argv: list[list[str]] = []

    @dbt_assets(manifest=manifest, project=dbt_project)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        invocation = dbt.cli(
            ["run", "--exclude", "model_0"],
            context=context,
        ).wait()
        captured_argv.append(cast("list[str]", invocation.process.args))
        yield from invocation.stream()

    # Threshold high enough that we stay on the non-selector path even with an enumerated subset.
    subset = list(my_dbt_assets.keys)[: _NUM_MODELS - 2]
    with mock.patch("dagster_dbt.asset_utils._SELECTION_ARGS_THRESHOLD", 10_000):
        result = materialize(
            [my_dbt_assets],
            resources={"dbt": DbtCliResource(project_dir=str(project_dir))},
            selection=subset,
            raise_on_error=False,
        )

    assert result.success
    assert captured_argv
    argv = captured_argv[0]
    assert "--selector" not in argv, "selector branch should not fire below threshold"
    # --exclude is in argv exactly once, with the user's value. If extraction had failed,
    # the count would be 2 (user's original + dagster's injected one in selection_args).
    assert argv.count("--exclude") == 1
    exclude_idx = argv.index("--exclude")
    assert argv[exclude_idx + 1] == "model_0"


def test_runtime_select_reinjected_below_threshold(
    large_dbt_project: tuple[Path, dict],
):
    """Below the selector threshold, runtime --select is extracted from user args and
    re-injected into selection_args so dbt still sees it.
    """
    from dagster import AssetExecutionContext, materialize
    from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

    project_dir, manifest = large_dbt_project
    dbt_project = DbtProject(project_dir=str(project_dir))

    captured_argv: list[list[str]] = []

    @dbt_assets(manifest=manifest, project=dbt_project)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        invocation = dbt.cli(
            ["run", "--select", "model_1"],
            context=context,
        ).wait()
        captured_argv.append(cast("list[str]", invocation.process.args))
        yield from invocation.stream()

    subset = list(my_dbt_assets.keys)[: _NUM_MODELS - 2]
    with mock.patch("dagster_dbt.asset_utils._SELECTION_ARGS_THRESHOLD", 10_000):
        result = materialize(
            [my_dbt_assets],
            resources={"dbt": DbtCliResource(project_dir=str(project_dir))},
            selection=subset,
            raise_on_error=False,
        )

    assert result.success
    assert captured_argv
    argv = captured_argv[0]
    assert "--selector" not in argv, "selector branch should not fire below threshold"
    # The runtime --select value appears in the re-injected block that precedes dagster's.
    select_positions = [i for i, tok in enumerate(argv) if tok == "--select"]
    assert select_positions, "selection_args should include --select"
    assert any("model_1" in argv[i + 1] for i in select_positions), (
        "runtime --select value should appear in the final argv"
    )


def test_runtime_exclude_preserved_for_plain_op(
    large_dbt_project: tuple[Path, dict],
):
    """A plain @op (no @dbt_assets) that passes --exclude to dbt.cli must still see
    --exclude in the final dbt argv. extract_runtime_selection_from_args strips the
    flag at the resource boundary, so the re-injection has to happen even when there
    is no asset context — otherwise the flag is silently dropped.
    """
    from dagster import OpExecutionContext, job, op
    from dagster_dbt import DbtCliResource

    project_dir, manifest = large_dbt_project

    captured_argv: list[list[str]] = []

    @op
    def my_dbt_op(context: OpExecutionContext, dbt: DbtCliResource):
        invocation = dbt.cli(
            ["run", "--exclude", "model_0"],
            context=context,
            manifest=manifest,
        ).wait()
        captured_argv.append(cast("list[str]", invocation.process.args))

    @job
    def my_dbt_job():
        my_dbt_op()

    result = my_dbt_job.execute_in_process(
        resources={"dbt": DbtCliResource(project_dir=str(project_dir))},
    )

    assert result.success
    assert captured_argv
    argv = captured_argv[0]
    assert "--selector" not in argv, "plain-op path should not enter the selector branch"
    # --exclude appears exactly once with the user's value. Without the fix, extraction
    # strips it from user args and nothing re-injects it for the assets_def-is-None path,
    # so the count is 0.
    assert argv.count("--exclude") == 1
    exclude_idx = argv.index("--exclude")
    assert argv[exclude_idx + 1] == "model_0"
