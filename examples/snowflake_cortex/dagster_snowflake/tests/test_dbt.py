"""Test dbt component integration."""


class TestDbtComponent:
    """Test dbt component loading and configuration."""

    def test_dbt_module_exists(self):
        """Test that dbt module exists."""
        from pathlib import Path

        dbt_path = (
            Path(__file__).parent.parent
            / "src"
            / "dagster_snowflake_ai"
            / "defs"
            / "dbt"
            / "dbt.py"
        )
        assert dbt_path.exists(), "dbt.py should exist"

    def test_dbt_resource_in_resources(self):
        """Test that DbtCliResource is configured in resources."""
        from dagster_snowflake_ai.defs.resources import resources

        assert "dbt" in resources, "DbtCliResource should be in resources"
        assert resources["dbt"] is not None

    def test_dbt_job_exists(self):
        """Test that dbt job is defined."""
        from dagster_snowflake_ai.defs.jobs import dbt_transform_job

        assert dbt_transform_job is not None
        assert dbt_transform_job.name == "dbt_transform"
