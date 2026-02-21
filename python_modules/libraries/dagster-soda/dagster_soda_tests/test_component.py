"""Unit tests for SodaScanComponent: SodaCL parsing, component construction, and result mapping."""

import textwrap
from collections.abc import Iterable  # noqa: TC003
from pathlib import Path
from typing import cast
from unittest import mock

import pytest
from dagster import AssetCheckResult, AssetKey, build_op_context
from dagster._core.definitions.definitions_class import Definitions
from dagster.components.core.component_tree import TestComponentTree
from dagster_soda.component import (
    SodaScanComponent,
    _collect_check_identifiers_for_dataset,
    _filter_results_for_dataset,
    _get_check_name,
    _get_outcome,
    _get_severity,
    _parse_check_identifiers_from_yaml,
    _sanitize_check_name,
    _to_dagster_severity,
)

# ----- SodaCL parsing (definition-time) -----


@pytest.mark.parametrize(
    "name,expected",
    [
        ("row_count", "row_count"),
        ("row_count > 0", "row_count___0"),
        ("my-check", "my_check"),
        ("schema:", "schema"),
        ("a" * 150, "a" * 100),
        ("  leading_trailing  ", "leading_trailing"),
        ("", "check"),
    ],
)
def test_sanitize_check_name(name: str, expected: str) -> None:
    assert _sanitize_check_name(name) == expected


def test_parse_check_identifiers_from_yaml_simple(tmp_path: Path) -> None:
    """Parse a simple 'checks for <dataset>' YAML with string list items."""
    yaml_path = tmp_path / "checks.yml"
    yaml_path.write_text(
        textwrap.dedent("""
            checks for my_table:
              - row_count > 0
              - freshness(updated_at) < 1d
        """)
    )
    identifiers = _parse_check_identifiers_from_yaml(yaml_path, "my_table")
    # "<" and spaces become "_"; "freshness(updated_at) < 1d" -> freshness_updated_at____1d
    assert identifiers == ["row_count___0", "freshness_updated_at____1d"]


def test_parse_check_identifiers_from_yaml_named_checks(tmp_path: Path) -> None:
    """Parse YAML with named check config (name in config dict)."""
    yaml_path = tmp_path / "checks.yml"
    yaml_path.write_text(
        textwrap.dedent("""
            checks for my_table:
              - row_count > 0:
                  name: custom_row_count_check
              - schema:
                  name: schema_check
                  fail:
                    when required column missing: [id]
        """)
    )
    identifiers = _parse_check_identifiers_from_yaml(yaml_path, "my_table")
    assert "custom_row_count_check" in identifiers
    assert "schema_check" in identifiers


def test_parse_check_identifiers_from_yaml_wrong_dataset(tmp_path: Path) -> None:
    """No 'checks for <other_dataset>' key returns empty list."""
    yaml_path = tmp_path / "checks.yml"
    yaml_path.write_text(
        textwrap.dedent("""
            checks for my_table:
              - row_count > 0
        """)
    )
    assert _parse_check_identifiers_from_yaml(yaml_path, "other_table") == []


def test_parse_check_identifiers_from_yaml_empty_file(tmp_path: Path) -> None:
    yaml_path = tmp_path / "checks.yml"
    yaml_path.write_text("")
    assert _parse_check_identifiers_from_yaml(yaml_path, "my_table") == []


def test_collect_check_identifiers_for_dataset_multiple_files(tmp_path: Path) -> None:
    """Collect identifiers from multiple YAML files with same dataset."""
    (tmp_path / "checks1.yml").write_text(
        textwrap.dedent("""
            checks for my_table:
              - row_count > 0
        """)
    )
    (tmp_path / "checks2.yml").write_text(
        textwrap.dedent("""
            checks for my_table:
              - freshness(updated_at) < 1d
        """)
    )
    identifiers = _collect_check_identifiers_for_dataset(
        checks_paths=[str(tmp_path / "checks1.yml"), str(tmp_path / "checks2.yml")],
        project_root=tmp_path,
        dataset="my_table",
    )
    assert "row_count___0" in identifiers
    assert "freshness_updated_at____1d" in identifiers


# ----- Component construction (AssetCheckSpecs from YAML) -----


def test_build_defs_produces_expected_asset_check_specs(tmp_path: Path) -> None:
    """Definition-time: build_defs produces Definitions with correct AssetCheckSpecs from YAML."""
    checks_path = tmp_path / "checks.yml"
    checks_path.write_text(
        textwrap.dedent("""
            checks for my_table:
              - row_count > 0
              - schema:
                  name: schema_id
                  fail:
                    when required column missing: [id]
        """)
    )
    config_path = tmp_path / "configuration.yml"
    config_path.write_text(
        textwrap.dedent("""
            data_source my_ds:
              type: sqlite
              connection:
                database: ":memory:"
        """)
    )

    component = SodaScanComponent(
        checks_paths=[str(checks_path)],
        configuration_path=str(config_path),
        data_source_name="my_ds",
        asset_key_map={"my_table": "my_table"},
    )
    tree = TestComponentTree(defs_module=mock.Mock(), project_root=tmp_path)
    defs = component.build_defs(tree.load_context)

    assert isinstance(defs, Definitions)
    asset_checks = list(defs.asset_checks) if defs.asset_checks else []
    assert len(asset_checks) == 1
    checks_def = asset_checks[0]
    specs = list(checks_def.check_specs)
    assert len(specs) == 2
    spec_names = {s.name for s in specs}
    assert "row_count___0" in spec_names
    assert "schema_id" in spec_names
    for s in specs:
        assert s.asset_key == AssetKey("my_table")


def test_build_defs_respects_asset_key_map(tmp_path: Path) -> None:
    """Asset keys come from asset_key_map when provided."""
    (tmp_path / "checks.yml").write_text(
        textwrap.dedent("""
            checks for soda_dataset:
              - row_count > 0
        """)
    )
    (tmp_path / "configuration.yml").write_text("data_source ds: {}")

    component = SodaScanComponent(
        checks_paths=[str(tmp_path / "checks.yml")],
        configuration_path=str(tmp_path / "configuration.yml"),
        data_source_name="ds",
        asset_key_map={"soda_dataset": "dagster/asset/key"},
    )
    tree = TestComponentTree(defs_module=mock.Mock(), project_root=tmp_path)
    defs = component.build_defs(tree.load_context)

    asset_checks = list(defs.asset_checks) if defs.asset_checks else []
    assert len(asset_checks) == 1
    checks_def = asset_checks[0]
    specs = list(checks_def.check_specs)
    assert len(specs) == 1
    assert specs[0].asset_key == AssetKey(["dagster", "asset", "key"])


# ----- Result mapping (execution-time: outcome -> AssetCheckResult) -----


def test_get_outcome() -> None:
    for outcome in ("pass", "warn", "fail"):
        obj = mock.Mock(outcome=outcome)
        assert _get_outcome(obj) == outcome
    obj = mock.Mock(spec=[], result="fail")
    del obj.outcome
    obj.result = "fail"
    assert _get_outcome(obj) == "fail"


def test_get_check_name() -> None:
    obj = mock.Mock()
    obj.name = "my_check"
    assert _get_check_name(obj) == "my_check"
    obj2 = mock.Mock(spec=["check_name"])
    obj2.check_name = "other"
    assert _get_check_name(obj2) == "other"


def test_get_severity() -> None:
    obj = mock.Mock(severity="error")
    assert _get_severity(obj) == "error"
    obj = mock.Mock(spec=[])
    del obj.severity
    assert _get_severity(obj) == "warn"


def test_to_dagster_severity() -> None:
    from dagster import AssetCheckSeverity

    assert _to_dagster_severity("error") == AssetCheckSeverity.ERROR
    assert _to_dagster_severity("fail") == AssetCheckSeverity.ERROR
    assert _to_dagster_severity("warn") == AssetCheckSeverity.WARN
    assert _to_dagster_severity("pass") == AssetCheckSeverity.WARN


def test_filter_results_for_dataset() -> None:
    """Filter extracts checks for the given dataset (table/table_name or dataset/dataset_name)."""
    c1 = mock.Mock(spec=["table"])
    c1.table = "my_table"
    c2 = mock.Mock(spec=["table_name"])
    c2.table_name = "my_table"
    c3 = mock.Mock(spec=["table"])
    c3.table = "other"
    scan_results = mock.Mock(checks=[c1, c2, c3])
    filtered = _filter_results_for_dataset(scan_results, "my_table")
    assert len(filtered) == 2
    assert c1 in filtered and c2 in filtered and c3 not in filtered


# ----- Execution-time: mock Scan and verify AssetCheckResults -----


def test_execution_yields_asset_check_results_pass_and_fail(tmp_path: Path) -> None:
    """Run the multi_asset_check with mocked Scan; verify pass/fail mapping to AssetCheckResults."""
    (tmp_path / "checks.yml").write_text(
        textwrap.dedent("""
            checks for my_table:
              - row_count > 0
              - freshness(updated_at) < 1d
        """)
    )
    (tmp_path / "configuration.yml").write_text("data_source ds: {}")

    # Mock Soda check results: first passes, second fails
    mock_check_pass = mock.Mock(
        table="my_table",
        outcome="pass",
        name="row_count___0",
        severity="warn",
        definition="row_count > 0",
    )
    mock_check_fail = mock.Mock(
        table="my_table",
        outcome="fail",
        name="freshness_updated_at____1d",
        severity="error",
        definition="freshness(updated_at) < 1d",
    )
    mock_scan_results = mock.Mock(checks=[mock_check_pass, mock_check_fail])

    component = SodaScanComponent(
        checks_paths=[str(tmp_path / "checks.yml")],
        configuration_path=str(tmp_path / "configuration.yml"),
        data_source_name="ds",
        asset_key_map={"my_table": "my_table"},
    )
    tree = TestComponentTree(defs_module=mock.Mock(), project_root=tmp_path)
    defs = component.build_defs(tree.load_context)

    asset_checks = list(defs.asset_checks) if defs.asset_checks else []
    assert len(asset_checks) == 1
    check_def = asset_checks[0]

    with mock.patch("dagster_soda.component.Scan") as MockScan:
        mock_scan = mock.Mock()
        MockScan.return_value = mock_scan
        mock_scan.get_scan_results.return_value = mock_scan_results
        mock_scan.build_scan_results.return_value = mock_scan_results

        # Invoke the check op with context (multi_asset_check expects AssetCheckExecutionContext)
        results = list(cast("Iterable[AssetCheckResult]", check_def(build_op_context())))

    assert len(results) == 2
    by_name = {r.check_name: r for r in results}
    assert by_name["row_count___0"].passed is True
    assert by_name["freshness_updated_at____1d"].passed is False
    assert all(r.asset_key == AssetKey("my_table") for r in results)


def test_execution_missing_check_yields_specific_failure(tmp_path: Path) -> None:
    """When Soda returns fewer results than specs, matched spec passes, missing spec fails with specific error."""
    (tmp_path / "checks.yml").write_text(
        textwrap.dedent("""
            checks for my_table:
              - row_count > 0
              - freshness(updated_at) < 1d
        """)
    )
    (tmp_path / "configuration.yml").write_text("data_source ds: {}")

    # One Soda result for two spec names -> one matched (pass), one missing (fail with specific message)
    mock_check = mock.Mock(
        table="my_table",
        outcome="pass",
        name="row_count___0",
        severity="warn",
        definition="row_count > 0",
    )
    mock_scan_results = mock.Mock(checks=[mock_check])

    component = SodaScanComponent(
        checks_paths=[str(tmp_path / "checks.yml")],
        configuration_path=str(tmp_path / "configuration.yml"),
        data_source_name="ds",
        asset_key_map={"my_table": "my_table"},
    )
    tree = TestComponentTree(defs_module=mock.Mock(), project_root=tmp_path)
    defs = component.build_defs(tree.load_context)

    asset_checks = list(defs.asset_checks) if defs.asset_checks else []
    assert len(asset_checks) == 1
    check_def = asset_checks[0]

    with mock.patch("dagster_soda.component.Scan") as MockScan:
        mock_scan = mock.Mock()
        MockScan.return_value = mock_scan
        mock_scan.get_scan_results.return_value = mock_scan_results
        mock_scan.build_scan_results.return_value = mock_scan_results

        results = list(cast("Iterable[AssetCheckResult]", check_def(build_op_context())))

    assert len(results) == 2
    by_name = {r.check_name: r for r in results}
    # Matched spec passes normally
    assert by_name["row_count___0"].passed is True
    assert by_name["row_count___0"].asset_key == AssetKey("my_table")
    # Missing spec fails with specific metadata error
    assert by_name["freshness_updated_at____1d"].passed is False
    assert by_name["freshness_updated_at____1d"].asset_key == AssetKey("my_table")
    err = by_name["freshness_updated_at____1d"].metadata.get("error")
    assert err is not None
    err_text = str(err.value) if hasattr(err, "value") else str(err)
    assert err_text == "No matching Soda result for check 'freshness_updated_at____1d'"


def test_execution_scan_exception_yields_failed_for_all(tmp_path: Path) -> None:
    """When scan.execute() raises (e.g. DB connection error), yield failed for all with error metadata."""
    (tmp_path / "checks.yml").write_text(
        textwrap.dedent("""
            checks for my_table:
              - row_count > 0
        """)
    )
    (tmp_path / "configuration.yml").write_text("data_source ds: {}")

    component = SodaScanComponent(
        checks_paths=[str(tmp_path / "checks.yml")],
        configuration_path=str(tmp_path / "configuration.yml"),
        data_source_name="ds",
        asset_key_map={"my_table": "my_table"},
    )
    tree = TestComponentTree(defs_module=mock.Mock(), project_root=tmp_path)
    defs = component.build_defs(tree.load_context)

    asset_checks = list(defs.asset_checks) if defs.asset_checks else []
    assert len(asset_checks) == 1
    check_def = asset_checks[0]

    with mock.patch("dagster_soda.component.Scan") as MockScan:
        mock_scan = mock.Mock()
        MockScan.return_value = mock_scan
        mock_scan.execute.side_effect = RuntimeError("Connection refused")

        results = list(cast("Iterable[AssetCheckResult]", check_def(build_op_context())))

    assert len(results) == 1
    r = results[0]
    assert r.passed is False
    assert r.asset_key == AssetKey("my_table")
    assert r.check_name == "row_count___0"
    err = r.metadata.get("error")
    assert err is not None
    err_text = str(err.value) if hasattr(err, "value") else str(err)
    assert "Soda scan failed" in err_text
    assert "Connection refused" in err_text
