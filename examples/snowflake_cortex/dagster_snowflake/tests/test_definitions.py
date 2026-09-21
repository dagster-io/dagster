"""Test Dagster definitions load correctly."""

import dagster as dg

from dagster_snowflake_ai.definitions import defs


class TestDagsterDefinitions:
    """Test that all Dagster definitions load without errors."""

    def test_definitions_load(self):
        """Verify all definitions can be loaded without errors."""
        assert defs is not None
        assets = list(defs.assets or [])
        assert len(assets) > 0

    def test_assets_exist(self):
        """Verify expected assets are present."""
        assets = list(defs.assets or [])
        asset_keys = [
            asset.key for asset in assets if isinstance(asset, dg.AssetsDefinition)
        ]

        expected_assets = [
            "raw_stories",
            "story_sentiment_analysis",
            "entity_extraction",
            "daily_story_summary",
        ]

        asset_key_strings = [str(key) for key in asset_keys]

        for asset_name in expected_assets:
            assert any(asset_name in key for key in asset_key_strings), (
                f"Missing expected asset: {asset_name}"
            )

    def test_resources_exist(self):
        """Verify resources are configured."""
        assert defs.resources is not None
        assert len(defs.resources) > 0
        assert "snowflake" in defs.resources

    def test_jobs_exist(self):
        """Verify jobs are defined."""
        jobs = list(defs.jobs or [])
        assert len(jobs) > 0

        job_names = [job.name for job in jobs]
        assert "daily_intelligence" in job_names
        assert "weekly_reports" in job_names

    def test_schedules_exist(self):
        """Verify schedules are defined."""
        schedules = list(defs.schedules or [])
        assert len(schedules) > 0

        schedule_names = [schedule.name for schedule in schedules]
        assert "daily_intelligence_schedule" in schedule_names
        assert "weekly_reports_schedule" in schedule_names

    def test_sensors_exist(self):
        """Verify sensors are defined."""
        sensors = list(defs.sensors or [])
        assert len(sensors) > 0

        sensor_names = [sensor.name for sensor in sensors]
        assert "dynamic_table_freshness_sensor" in sensor_names
