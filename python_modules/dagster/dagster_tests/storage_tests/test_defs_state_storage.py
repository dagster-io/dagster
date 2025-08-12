import tempfile
from collections.abc import Iterator

import pytest
from dagster._core.instance_for_test import instance_for_test
from dagster._core.storage.defs_state.base import DefsStateStorage
from dagster._core.storage.defs_state.blob_storage_state_storage import BlobStorageStateStorage
from dagster_shared import check
from upath import UPath

from dagster_tests.storage_tests.utils.defs_state_storage import TestDefsStateStorage


class TestDefaultDefsStateStorage(TestDefsStateStorage):
    """Tests the default state storage implementation."""

    __test__ = True

    @pytest.fixture(name="storage", scope="function")
    def state_storage(self) -> Iterator[DefsStateStorage]:
        with instance_for_test() as instance:
            yield check.not_none(instance.defs_state_storage)


class TestExplicitUPathDefsStateStorage(TestDefsStateStorage):
    """Tests the blob storage state storage implementation."""

    __test__ = True

    @pytest.fixture(name="storage", scope="function")
    def state_storage(self) -> Iterator[DefsStateStorage]:
        with tempfile.TemporaryDirectory() as temp_dir:
            with instance_for_test(
                overrides={
                    "defs_state_storage": {
                        "module": "dagster._core.storage.defs_state.blob_storage_state_storage",
                        "class": "BlobStorageStateStorage",
                        "config": {"base_dir": temp_dir},
                    }
                }
            ) as instance:
                state_storage = check.inst(instance.defs_state_storage, BlobStorageStateStorage)

                assert state_storage.base_dir == UPath(temp_dir)
                yield state_storage
