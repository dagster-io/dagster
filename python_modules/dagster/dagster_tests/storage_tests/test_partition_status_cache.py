import pytest
from dagster._core.test_utils import instance_for_test

from dagster_tests.storage_tests.utils.partition_status_cache import TestPartitionStatusCache


class TestSqlPartitionStatusCache(TestPartitionStatusCache):
    @pytest.fixture
    def instance(self):
        with instance_for_test() as the_instance:
            yield the_instance
