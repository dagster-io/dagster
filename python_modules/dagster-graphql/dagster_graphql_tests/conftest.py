import os
from typing import TYPE_CHECKING

import pytest
from dagster._core.definitions.decorators.op_decorator import (
    do_not_attach_code_origin,
)
from syrupy.extensions.amber import AmberSnapshotExtension

if TYPE_CHECKING:
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
    def get_snapshot_name(self, *, index: "SnapshotIndex") -> str:
        snapshot_name = self.test_location.snapshot_name

        # Exclude any of the GraphQLContextVariant suffixes from the snapshot name
        # so that we don't have to re-generate an identical snapshot for each one
        variant_start_index = snapshot_name.find("[")
        if variant_start_index != -1:
            snapshot_name = snapshot_name[:variant_start_index]

        return f"{snapshot_name}[{index}]"


@pytest.fixture
def snapshot(snapshot):
    return snapshot.use_extension(SharedSnapshotExtension)


@pytest.fixture
def ignore_code_origin():
    # avoid attaching code origin metadata to ops/assets, because this can change from environment
    # to environment and break snapshot tests
    with do_not_attach_code_origin():
        yield
