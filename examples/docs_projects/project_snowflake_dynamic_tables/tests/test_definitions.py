"""Smoke tests: verify Definitions load and contain the expected components."""

import dagster as dg
from project_snowflake_dynamic_tables.definitions import defs as _raw_defs

defs: dg.Definitions = _raw_defs() if not isinstance(_raw_defs, dg.Definitions) else _raw_defs


class TestDefinitions:
    def test_defs_load(self):
        assert isinstance(defs, dg.Definitions)

    def test_all_asset_keys_present(self):
        all_specs = defs.resolve_all_asset_specs()
        keys = {spec.key for spec in all_specs}

        expected = {
            dg.AssetKey("raw_orders"),
            dg.AssetKey("raw_customers"),
            dg.AssetKey("customer_lifetime_value"),
            dg.AssetKey("daily_revenue_rollup"),
            dg.AssetKey("executive_dashboard_report"),
        }
        assert expected.issubset(keys)

    def test_dynamic_tables_are_virtual(self):
        all_specs = defs.resolve_all_asset_specs()
        spec_map = {spec.key: spec for spec in all_specs}

        assert spec_map[dg.AssetKey("customer_lifetime_value")].is_virtual
        assert spec_map[dg.AssetKey("daily_revenue_rollup")].is_virtual

    def test_sources_are_not_virtual(self):
        all_specs = defs.resolve_all_asset_specs()
        spec_map = {spec.key: spec for spec in all_specs}

        assert not spec_map[dg.AssetKey("raw_orders")].is_virtual
        assert not spec_map[dg.AssetKey("raw_customers")].is_virtual

    def test_sensor_registered(self):
        repo = defs.get_repository_def()
        sensor_names = [s.name for s in repo.sensor_defs]
        assert "dynamic_table_freshness_sensor" in sensor_names

    def test_snowflake_resource_registered(self):
        resource_keys = set(defs.resources or {})
        assert "snowflake" in resource_keys
