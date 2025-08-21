import dagster as dg
import pytest

from dagster_tests.storage_tests.utils.partition_status_cache import TestPartitionStatusCache


class TestSqlPartitionStatusCache(TestPartitionStatusCache):
    @pytest.fixture
    def instance(self):
        with dg.instance_for_test() as the_instance:
            yield the_instance
