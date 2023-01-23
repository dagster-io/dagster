import pytest
from dagster_postgres.partitions_storage.partitions_storage import PostgresPartitionsStorage


class TestPartitionsStorage:
    __test__ = False

    @pytest.fixture(name="storage", params=[])
    def partitions_storage(self, request):
        with request.param() as s:
            yield s

    def test_add_partitions(self, storage):
        assert storage

        storage.add_partitions(partitions_def_name="foo", partition_keys=["foo", "bar", "baz"])
        assert set(storage.get_partitions("foo")) == {"foo", "bar", "baz"}

        # Test for idempotency
        storage.add_partitions(partitions_def_name="foo", partition_keys=["foo"])
        assert set(storage.get_partitions("foo")) == {"foo", "bar", "baz"}

        assert set(storage.get_partitions("baz")) == set()

    def test_delete_partitions(self, storage):
        assert storage

        storage.add_partitions(partitions_def_name="foo", partition_keys=["foo", "bar", "baz"])
        assert set(storage.get_partitions("foo")) == {"foo", "bar", "baz"}

        storage.delete_partition(partitions_def_name="foo", partition_key="foo")
        assert set(storage.get_partitions("foo")) == {"bar", "baz"}

        # Test for idempotency
        storage.delete_partition(partitions_def_name="foo", partition_key="foo")
        assert set(storage.get_partitions("foo")) == {"bar", "baz"}

        storage.delete_partition(partitions_def_name="bar", partition_key="foo")
        assert set(storage.get_partitions("baz")) == set()

    def test_has_partition(self, storage):
        assert storage

        storage.add_partitions(partitions_def_name="foo", partition_keys=["foo", "bar", "baz"])
        assert storage.has_partition(partitions_def_name="foo", partition_key="foo")
        assert not storage.has_partition(partitions_def_name="foo", partition_key="qux")
        assert not storage.has_partition(partitions_def_name="bar", partition_key="foo")


class TestPostgresPartitionsStorage(TestPartitionsStorage):
    __test__ = True

    @pytest.fixture(scope="function", name="storage")
    def partitions_storage(self, conn_string):  # pylint: disable=arguments-renamed
        storage = PostgresPartitionsStorage.create_clean_storage(conn_string)
        assert storage
        return storage
