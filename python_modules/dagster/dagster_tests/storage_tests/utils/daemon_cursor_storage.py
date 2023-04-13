import pytest


class TestDaemonCursorStorage:
    """You can extend this class to easily run these set of tests on any daemon cursor storage. When extending,
    you simply need to override the `cursor_storage` fixture.
    """

    __test__ = False

    @pytest.fixture(name="storage", params=[])
    def cursor_storage(self, request):
        with request.param() as s:
            yield s

    def test_kvs(self, storage):
        storage.kvs_set({"key": "value"})
        assert storage.kvs_get({"key"}) == {"key": "value"}

        storage.kvs_set({"key": "new-value"})
        assert storage.kvs_get({"key"}) == {"key": "new-value"}

        storage.kvs_set({"foo": "foo", "bar": "bar"})
        assert storage.kvs_get({"foo", "bar", "key"}) == {
            "key": "new-value",
            "foo": "foo",
            "bar": "bar",
        }

        storage.kvs_set({"foo": "1", "bar": "2", "key": "3"})
        assert storage.kvs_get({"foo", "bar", "key"}) == {"foo": "1", "bar": "2", "key": "3"}
