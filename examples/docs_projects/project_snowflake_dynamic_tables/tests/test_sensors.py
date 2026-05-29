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


class TestDynamicTableFreshnessSensorTrigger:
    """The sensor triggers the dashboard AFTER a refresh lands, not on source change."""

    _BOTH_REFRESHED = [
        ("CUSTOMER_LIFETIME_VALUE", "RUNNING", "2026-05-07 10:00:00", 30),
        ("DAILY_REVENUE_ROLLUP", "RUNNING", "2026-05-07 09:00:00", 3600),
    ]

    def test_fires_run_request_on_advance(self, snowflake_resource, mock_cursor):
        mock_cursor.fetchall.return_value = self._BOTH_REFRESHED
        context = dg.build_sensor_context()

        result = dynamic_table_freshness_sensor(context, snowflake=snowflake_resource)

        assert isinstance(result, dg.SensorResult)
        assert result.run_requests is not None
        assert len(result.run_requests) == 1
        # Composite run key over both tables' last_completed_refresh timestamps.
        assert result.run_requests[0].run_key == "2026-05-07 10:00:00-2026-05-07 09:00:00"
        # Observations are still emitted alongside the run request.
        assert len(result.asset_events) == 2

    def test_cursor_written_on_fire(self, snowflake_resource, mock_cursor):
        mock_cursor.fetchall.return_value = self._BOTH_REFRESHED
        context = dg.build_sensor_context()

        result = dynamic_table_freshness_sensor(context, snowflake=snowflake_resource)

        assert isinstance(result, dg.SensorResult)
        assert result.cursor == "2026-05-07 10:00:00-2026-05-07 09:00:00"

    def test_no_double_fire_when_cursor_matches(self, snowflake_resource, mock_cursor):
        mock_cursor.fetchall.return_value = self._BOTH_REFRESHED
        context = dg.build_sensor_context(cursor="2026-05-07 10:00:00-2026-05-07 09:00:00")

        result = dynamic_table_freshness_sensor(context, snowflake=snowflake_resource)

        assert isinstance(result, dg.SensorResult)
        assert not result.run_requests
        # Observations still flow even when no run is requested.
        assert len(result.asset_events) == 2

    def test_cold_start_no_fire_when_null_refresh(self, snowflake_resource, mock_cursor):
        mock_cursor.fetchall.return_value = [
            ("CUSTOMER_LIFETIME_VALUE", "RUNNING", "2026-05-07 10:00:00", 30),
            ("DAILY_REVENUE_ROLLUP", "RUNNING", None, None),
        ]
        context = dg.build_sensor_context()

        result = dynamic_table_freshness_sensor(context, snowflake=snowflake_resource)

        assert isinstance(result, dg.SensorResult)
        assert not result.run_requests
        # Observations are emitted even before the first refresh completes.
        assert len(result.asset_events) == 2

    def test_fires_when_one_table_advances(self, snowflake_resource, mock_cursor):
        # CLV advanced (10:00 -> 10:01); rollup unchanged from the cursor state.
        mock_cursor.fetchall.return_value = [
            ("CUSTOMER_LIFETIME_VALUE", "RUNNING", "2026-05-07 10:01:00", 30),
            ("DAILY_REVENUE_ROLLUP", "RUNNING", "2026-05-07 09:00:00", 3600),
        ]
        context = dg.build_sensor_context(cursor="2026-05-07 10:00:00-2026-05-07 09:00:00")

        result = dynamic_table_freshness_sensor(context, snowflake=snowflake_resource)

        assert isinstance(result, dg.SensorResult)
        assert result.run_requests is not None
        assert len(result.run_requests) == 1
        assert result.run_requests[0].run_key == "2026-05-07 10:01:00-2026-05-07 09:00:00"
