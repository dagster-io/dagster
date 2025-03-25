import os
from typing import TYPE_CHECKING

import pytest
from syrupy.extensions.amber import AmberSnapshotExtension

if TYPE_CHECKING:
    from syrupy.location import PyTestLocation
    from syrupy.types import SnapshotIndex


@pytest.fixture(scope="session", autouse=True)
def unset_dagster_home():
    old_env = os.getenv("DAGSTER_HOME")
    if old_env is not None:
        del os.environ["DAGSTER_HOME"]
    yield
    if old_env is not None:
        os.environ["DAGSTER_HOME"] = old_env


class SharedSnapshotExtension(AmberSnapshotExtension):
    @classmethod
    def get_snapshot_name(  # pyright: ignore[reportIncompatibleMethodOverride]
        cls,
        *,
        index: "SnapshotIndex",
        test_location: "PyTestLocation",
    ) -> str:
        snapshot_name = test_location.snapshot_name

        # Exclude any of the GraphQLContextVariant suffixes from the snapshot name
        # so that we don't have to re-generate an identical snapshot for each one
        variant_start_index = snapshot_name.find("[")
        if variant_start_index != -1:
            snapshot_name = snapshot_name[:variant_start_index]

        return f"{snapshot_name}[{index}]"


@pytest.fixture
def snapshot(snapshot):
    return snapshot.use_extension(SharedSnapshotExtension)
