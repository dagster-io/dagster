"""Tests for snowflake_dynamic_tables assets and checks."""

import dagster as dg
import pytest
from project_snowflake_dynamic_tables.defs.assets.analytics import executive_dashboard_report
from project_snowflake_dynamic_tables.defs.assets.dynamic_tables import (
    customer_lifetime_value,
    customer_lifetime_value_is_fresh,
    daily_revenue_rollup,
    daily_revenue_rollup_is_fresh,
)
from project_snowflake_dynamic_tables.defs.assets.sources import raw_customers, raw_orders


class TestSourceSpecs:
    def test_raw_orders_key(self):
        assert raw_orders.key == dg.AssetKey("raw_orders")

    def test_raw_customers_key(self):
        assert raw_customers.key == dg.AssetKey("raw_customers")

    def test_sources_not_virtual(self):
        for spec in [raw_orders, raw_customers]:
            assert not spec.is_virtual, f"{spec.key} should not be virtual"

    def test_sources_group(self):
        for spec in [raw_orders, raw_customers]:
            assert spec.group_name == "sources"


class TestDynamicTableSpecs:
    def test_customer_lifetime_value_is_virtual(self):
        assert customer_lifetime_value.is_virtual is True

    def test_daily_revenue_rollup_is_virtual(self):
        assert daily_revenue_rollup.is_virtual is True

    def test_customer_lifetime_value_deps(self):
        dep_keys = {dep.asset_key for dep in customer_lifetime_value.deps}
        assert dg.AssetKey("raw_orders") in dep_keys
        assert dg.AssetKey("raw_customers") in dep_keys

    def test_daily_revenue_rollup_deps(self):
        dep_keys = {dep.asset_key for dep in daily_revenue_rollup.deps}
        assert dg.AssetKey("raw_orders") in dep_keys

    def test_dynamic_table_metadata_keys(self):
        for spec in [customer_lifetime_value, daily_revenue_rollup]:
            assert "target_lag" in spec.metadata
            assert "refresh_mode" in spec.metadata
            assert "snowflake_object_type" in spec.metadata

    def test_dynamic_table_group(self):
        for spec in [customer_lifetime_value, daily_revenue_rollup]:
            assert spec.group_name == "dynamic_tables"

    def test_virtual_specs_are_unexecutable(self):
        defs = dg.Definitions(assets=[customer_lifetime_value, daily_revenue_rollup])
        all_specs = defs.resolve_all_asset_specs()
        assert len([s for s in all_specs if s.is_virtual]) == 2


class TestAutomationConditionResolvesThrough:
    """Verify that resolve_through_virtual() makes the dashboard asset respond to source changes.

    Graph:
        raw_orders ──────────────────────────> daily_revenue_rollup (virtual)
                                                         ↓
        raw_orders ──> customer_lifetime_value (virtual) ──> executive_dashboard_report
        raw_customers /                                      (eager + resolve_through_virtual)
    """

    def _make_defs(self, snowflake_resource):
        return dg.Definitions(
            assets=[
                raw_orders,
                raw_customers,
                customer_lifetime_value,
                daily_revenue_rollup,
                executive_dashboard_report,
            ],
            resources={"snowflake": snowflake_resource},
        )

    def test_dashboard_not_requested_without_source_data(self, snowflake_resource):
        instance = dg.DagsterInstance.ephemeral()
        result = dg.evaluate_automation_conditions(
            defs=self._make_defs(snowflake_resource), instance=instance
        )
        assert result.total_requested == 0

    def test_dashboard_requested_after_sources_materialized(self, snowflake_resource):
        instance = dg.DagsterInstance.ephemeral()
        defs = self._make_defs(snowflake_resource)

        result = dg.evaluate_automation_conditions(defs=defs, instance=instance)

        instance.report_runless_asset_event(dg.AssetMaterialization("raw_orders"))
        instance.report_runless_asset_event(dg.AssetMaterialization("raw_customers"))

        result = dg.evaluate_automation_conditions(
            defs=defs,
            instance=instance,
            cursor=result.cursor,
        )
        assert result.total_requested == 1


class TestExecutiveDashboardReport:
    def test_returns_materialization(self, snowflake_resource, mock_cursor):
        mock_cursor.fetchone.return_value = (1500, 42350.0)

        context = dg.build_asset_context(resources={"snowflake": snowflake_resource})
        result = executive_dashboard_report(context)

        assert isinstance(result, dg.MaterializeResult)
        assert result.metadata["total_customers"].value == 1500
        assert result.metadata["total_revenue_30d"].value == pytest.approx(42350.0)

    def test_handles_empty_tables(self, snowflake_resource, mock_cursor):
        mock_cursor.fetchone.return_value = (None, None)

        context = dg.build_asset_context(resources={"snowflake": snowflake_resource})
        result = executive_dashboard_report(context)

        assert result.metadata["total_customers"].value == 0
        assert result.metadata["total_revenue_30d"].value == pytest.approx(0.0)

    def test_deps(self):
        all_deps: set[dg.AssetKey] = set()
        for dep_set in executive_dashboard_report.asset_deps.values():
            all_deps.update(dep_set)
        assert dg.AssetKey("customer_lifetime_value") in all_deps
        assert dg.AssetKey("daily_revenue_rollup") in all_deps

    def test_has_automation_condition(self):
        conditions = executive_dashboard_report.automation_conditions_by_key
        assert len(conditions) > 0
        assert all(c is not None for c in conditions.values())


class TestDynamicTableFreshnessChecks:
    def test_clv_passes_when_running(self, snowflake_resource, mock_cursor):
        mock_cursor.fetchone.return_value = ("RUNNING", "2026-05-07 10:00:00")
        result = customer_lifetime_value_is_fresh(snowflake=snowflake_resource)
        assert result.passed is True

    def test_clv_fails_when_not_found(self, snowflake_resource, mock_cursor):
        mock_cursor.fetchone.return_value = None
        result = customer_lifetime_value_is_fresh(snowflake=snowflake_resource)
        assert result.passed is False

    def test_clv_fails_when_failed_state(self, snowflake_resource, mock_cursor):
        mock_cursor.fetchone.return_value = ("FAILED", None)
        result = customer_lifetime_value_is_fresh(snowflake=snowflake_resource)
        assert result.passed is False

    def test_revenue_passes_when_suspended(self, snowflake_resource, mock_cursor):
        mock_cursor.fetchone.return_value = ("SUSPENDED", "2026-05-07 09:00:00")
        result = daily_revenue_rollup_is_fresh(snowflake=snowflake_resource)
        assert result.passed is True
