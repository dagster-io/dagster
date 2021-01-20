import io
import os

from dagster import LocalFileHandle, ModeDefinition, execute_solid, solid
from dagster.core.storage.file_cache import FSFileCache, fs_file_cache
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


def test_file_cache_overwrite():
    """Test changing overwrite config from default (False) value is propogated"""

    @solid(
        required_resource_keys={"file_cache"},
    )
    def file_cache_overwrite(context):
        return context.resources.file_cache.overwrite

    result = execute_solid(
        file_cache_overwrite,
        ModeDefinition(resource_defs={"file_cache": fs_file_cache}),
        run_config={
            "solids": {"file_cache_overwrite": {}},
            "resources": {
                "file_cache": {
                    "config": {
                        "overwrite": True,
                        "target_folder": "test_folder",
                    }
                }
            },
        },
    )

    assert result.success
    assert result.output_value()
