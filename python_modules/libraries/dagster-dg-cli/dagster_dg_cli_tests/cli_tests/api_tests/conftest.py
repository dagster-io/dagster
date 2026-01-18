"""Shared test utilities for API testing."""

from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest
from dagster_shared.plus.config import DagsterPlusCliConfig
from syrupy.extensions.amber import AmberSnapshotExtension

if TYPE_CHECKING:
    from syrupy.location import PyTestLocation
    from syrupy.types import SnapshotIndex


class ApiSnapshotExtension(AmberSnapshotExtension):
    """Custom snapshot extension for API tests.

    This extension ensures consistent snapshot naming by:
    1. Removing any existing parameterized test suffixes to avoid duplicate snapshots
    2. Applying a standardized index format that ensures all snapshots follow the pattern test_name[index]

    Without this extension, Syrupy's default naming might create inconsistent snapshot names
    or fail to handle indexing properly for these API tests.
    """

    @classmethod
    def get_snapshot_name(  # pyright: ignore[reportIncompatibleMethodOverride]
        cls,
        *,
        index: "SnapshotIndex",
        test_location: "PyTestLocation",
    ) -> str:
        snapshot_name = test_location.snapshot_name

        # Remove parameterized test suffixes to avoid duplicate snapshots
        variant_start_index = snapshot_name.find("[")
        if variant_start_index != -1:
            snapshot_name = snapshot_name[:variant_start_index]

        return f"{snapshot_name}[{index}]"


@pytest.fixture
def mock_dagster_plus_config():
    """Mock DagsterPlusCliConfig for testing."""
    config = Mock(spec=DagsterPlusCliConfig)
    config.org_name = "test-org"
    config.api_token = "test-token"
    config.endpoint = "https://test.dagster.cloud/graphql"
    return config


@pytest.fixture(autouse=True)
def disable_telemetry(monkeypatch, tmp_path):
    """Disable Dagster telemetry for API tests to prevent output interference."""
    # Set up a temporary DAGSTER_HOME with telemetry disabled
    dagster_home = tmp_path / "dagster_home"
    dagster_home.mkdir()

    # Create dagster.yaml with telemetry disabled
    dagster_yaml = dagster_home / "dagster.yaml"
    dagster_yaml.write_text("telemetry:\n  enabled: false\n")

    # Set the DAGSTER_HOME environment variable
    monkeypatch.setenv("DAGSTER_HOME", str(dagster_home))


@pytest.fixture
def snapshot(snapshot):
    """Configure snapshot fixture for API tests."""
    return snapshot.use_extension(ApiSnapshotExtension)
