from collections.abc import Iterator

import pytest
from dagster._core.instance_for_test import instance_for_test
from dagster._core.storage.defs_state.base import DefsStateStorage

from dagster_tests.storage_tests.utils.state_storage import TestStateStorage


class TestDefaultStateStorage(TestStateStorage):
    """Tests the default state storage implementation."""

    __test__ = True

    @pytest.fixture(name="storage", scope="function")
    def state_storage(self) -> Iterator[DefsStateStorage]:
        with instance_for_test() as instance:
            yield instance.defs_state_storage
