import io
import os

from dagster import LocalFileHandle
from dagster.core.storage.file_cache import FSFileCache
from dagster.utils.temp_file import get_temp_dir


def test_fs_file_cache_write_data():
    bytes_object = io.BytesIO(b"bar")
    with get_temp_dir() as temp_dir:
        file_cache = FSFileCache(temp_dir)
        assert not file_cache.has_file_object("foo")
        assert file_cache.write_file_object("foo", bytes_object)
        file_handle = file_cache.get_file_handle("foo")
        assert isinstance(file_handle, LocalFileHandle)
        assert file_handle.path_desc == os.path.join(temp_dir, "foo")


def test_fs_file_cache_write_binary_data():
    with get_temp_dir() as temp_dir:
        file_store = FSFileCache(temp_dir)
        assert not file_store.has_file_object("foo")
        assert file_store.write_binary_data("foo", b"bar")
        file_handle = file_store.get_file_handle("foo")
        assert isinstance(file_handle, LocalFileHandle)
        assert file_handle.path_desc == os.path.join(temp_dir, "foo")


def test_empty_file_cache():
    with get_temp_dir() as temp_dir:
        file_cache = FSFileCache(temp_dir)
        assert not file_cache.has_file_object("kjdfkd")
