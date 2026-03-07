"""Integration tests: load SodaScanComponent from a fixture defs.yaml and verify Definitions."""

import textwrap

import pytest
from dagster import AssetKey
from dagster._utils.test.definitions import scoped_definitions_load_context
from dagster.components.testing import create_defs_folder_sandbox
from dagster_soda import SodaScanComponent

# Fixture defs.yaml content for SodaScanComponent (paths relative to project root)
SODA_SCAN_DEFS_YAML = {
    "type": "dagster_soda.SodaScanComponent",
    "attributes": {
        "checks_paths": ["checks.yml"],
        "configuration_path": "configuration.yml",
        "data_source_name": "test_datasource",
        "asset_key_map": {"my_table": "my_table"},
    },
}


@pytest.fixture
def soda_fixture_files():
    """Create minimal SodaCL and configuration YAML contents for tests."""
    return {
        "checks_yml": textwrap.dedent("""
            checks for my_table:
              - row_count > 0
              - schema:
                  name: schema_check
                  fail:
                    when required column missing: [id]
        """),
        "configuration_yml": textwrap.dedent("""
            data_source test_datasource:
              type: sqlite
              connection:
                database: ":memory:"
        """),
    }


def test_load_soda_scan_component_from_defs_yaml(soda_fixture_files: dict) -> None:
    """Load SodaScanComponent from a fixture defs.yaml; verify Definitions has expected asset checks."""
    with create_defs_folder_sandbox() as sandbox:
        # Write fixture files under project root so the component can find them
        (sandbox.project_root / "checks.yml").write_text(soda_fixture_files["checks_yml"])
        (sandbox.project_root / "configuration.yml").write_text(
            soda_fixture_files["configuration_yml"]
        )

        defs_path = sandbox.scaffold_component(
            component_cls=SodaScanComponent,
            defs_yaml_contents=SODA_SCAN_DEFS_YAML,
        )

        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
        ):
            assert isinstance(component, SodaScanComponent)
            assert component.checks_paths == ["checks.yml"]
            assert component.configuration_path == "configuration.yml"
            assert component.data_source_name == "test_datasource"
            assert component.asset_key_map == {"my_table": "my_table"}

            # Definitions should contain asset checks built from SodaCL
            asset_checks = list(defs.asset_checks) if defs.asset_checks else []
            assert len(asset_checks) == 1
            checks_def = asset_checks[0]
            specs = list(checks_def.check_specs)
            assert len(specs) == 2
            spec_names = {s.name for s in specs}
            assert "row_count___0" in spec_names
            assert "schema_check" in spec_names
            for s in specs:
                assert s.asset_key == AssetKey("my_table")


def test_load_soda_scan_component_scaffold_default_defs(soda_fixture_files: dict) -> None:
    """Load component using scaffold-generated defs (no defs_yaml_contents); defs.yaml has scaffold defaults."""
    with create_defs_folder_sandbox() as sandbox:
        # Scaffolder writes checks.yml under defs_path; we need configuration at project root
        (sandbox.project_root / "configuration.yml").write_text(
            soda_fixture_files["configuration_yml"]
        )

        defs_path = sandbox.scaffold_component(component_cls=SodaScanComponent)
        # Scaffolder wrote checks.yml at defs_path / "checks.yml"
        # and defs.yaml with attributes pointing to relative path from project_root
        checks_relative = defs_path / "checks.yml"
        assert checks_relative.exists()

        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
        ):
            assert isinstance(component, SodaScanComponent)
            # Default scaffold uses "my_table" in checks and asset_key_map
            asset_checks = list(defs.asset_checks) if defs.asset_checks else []
            assert len(asset_checks) >= 1
            checks_def = asset_checks[0]
            specs = list(checks_def.check_specs)
            assert len(specs) >= 1
            assert all(s.asset_key == AssetKey("my_table") for s in specs)
