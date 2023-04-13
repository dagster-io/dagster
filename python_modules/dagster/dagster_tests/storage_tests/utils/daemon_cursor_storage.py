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
        storage.set_cursor_values({"key": "value"})
        assert storage.get_cursor_values({"key"}) == {"key": "value"}

        storage.set_cursor_values({"key": "new-value"})
        assert storage.get_cursor_values({"key"}) == {"key": "new-value"}

        storage.set_cursor_values({"foo": "foo", "bar": "bar"})
        assert storage.get_cursor_values({"foo", "bar", "key"}) == {
            "key": "new-value",
            "foo": "foo",
            "bar": "bar",
        }

        storage.set_cursor_values({"foo": "1", "bar": "2", "key": "3"})
        assert storage.get_cursor_values({"foo", "bar", "key"}) == {
            "foo": "1",
            "bar": "2",
            "key": "3",
        }
