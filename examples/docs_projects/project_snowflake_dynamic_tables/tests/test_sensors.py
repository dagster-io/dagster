"""Tests for the dynamic_table_freshness_sensor."""

import dagster as dg
from project_snowflake_dynamic_tables.defs.sensors import dynamic_table_freshness_sensor


class TestDynamicTableFreshnessSensor:
    def test_sensor_name(self):
        assert dynamic_table_freshness_sensor.name == "dynamic_table_freshness_sensor"

    def test_sensor_minimum_interval(self):
        assert dynamic_table_freshness_sensor.minimum_interval_seconds == 60

    def test_returns_skip_when_no_tables_found(self, snowflake_resource, mock_cursor):
        mock_cursor.fetchall.return_value = []
        context = dg.build_sensor_context()

        result = dynamic_table_freshness_sensor(context, snowflake=snowflake_resource)

        assert isinstance(result, dg.SkipReason)
        assert "No dynamic tables found" in str(result.skip_message)

    def test_emits_observations(self, snowflake_resource, mock_cursor):
        mock_cursor.fetchall.return_value = [
            ("CUSTOMER_LIFETIME_VALUE", "RUNNING", "2026-05-07 10:00:00", 30),
            ("DAILY_REVENUE_ROLLUP", "RUNNING", "2026-05-07 09:00:00", 3600),
        ]
        context = dg.build_sensor_context()

        result = dynamic_table_freshness_sensor(context, snowflake=snowflake_resource)

        assert isinstance(result, dg.SensorResult)
        assert len(result.asset_events) == 2

        obs_keys = {event.asset_key for event in result.asset_events}
        assert dg.AssetKey("customer_lifetime_value") in obs_keys
        assert dg.AssetKey("daily_revenue_rollup") in obs_keys

    def test_observation_metadata_keys(self, snowflake_resource, mock_cursor):
        mock_cursor.fetchall.return_value = [
            ("CUSTOMER_LIFETIME_VALUE", "RUNNING", "2026-05-07 10:00:00", 30),
        ]
        context = dg.build_sensor_context()

        result = dynamic_table_freshness_sensor(context, snowflake=snowflake_resource)

        assert isinstance(result, dg.SensorResult)
        obs = result.asset_events[0]
        assert "scheduling_state" in obs.metadata
        assert "last_completed_refresh" in obs.metadata
        assert "seconds_since_refresh" in obs.metadata

    def test_returns_skip_on_snowflake_error(self):
        from contextlib import contextmanager

        class _FailingResource:
            @contextmanager
            def get_connection(self):
                raise Exception("Connection refused")
                yield  # unreachable, required by @contextmanager

        context = dg.build_sensor_context()
        result = dynamic_table_freshness_sensor(context, snowflake=_FailingResource())

        assert isinstance(result, dg.SkipReason)
        assert "Snowflake query failed" in str(result.skip_message)
