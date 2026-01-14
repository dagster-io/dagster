"""Test Dagster resources."""

import os

from dagster_snowflake_ai.defs.snowflake.resources import (
    SnowflakeConfig,
    make_snowflake_resource,
)


class TestSnowflakeConfig:
    """Test Snowflake configuration resource."""

    def test_initialization_with_env_var(self):
        """Test resource initialization with environment variable for password."""
        config = SnowflakeConfig(
            account="test_account",
            user="test_user",
            password=os.getenv("SNOWFLAKE_PASSWORD", "test_password"),
            database="test_db",
            warehouse="test_wh",
            schema_name="PUBLIC",
        )

        assert config.account == "test_account"
        assert config.user == "test_user"
        assert config.database == "test_db"
        assert config.warehouse == "test_wh"
        assert config.schema_name == "PUBLIC"

    def test_initialization_with_role(self):
        """Test resource initialization with role specified."""
        config = SnowflakeConfig(
            account="test_account",
            user="test_user",
            password="test_password",
            database="test_db",
            warehouse="test_wh",
            role="TEST_ROLE",
        )

        assert config.role == "TEST_ROLE"

    def test_make_snowflake_resource(self):
        """Test creating SnowflakeResource from config."""
        config = SnowflakeConfig(
            account="test_account",
            user="test_user",
            password="test_password",
            database="test_db",
            warehouse="test_wh",
        )

        resource = make_snowflake_resource(config)
        assert resource is not None
