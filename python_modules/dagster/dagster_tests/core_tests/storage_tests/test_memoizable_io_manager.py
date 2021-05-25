from tempfile import TemporaryDirectory

from dagster import build_input_context, build_output_context
from dagster.core.storage.memoizable_io_manager import VersionedPickledObjectFilesystemIOManager


def test_versioned_pickled_object_filesystem_io_manager():
    with TemporaryDirectory() as temp_dir:
        store = VersionedPickledObjectFilesystemIOManager(temp_dir)
        context = build_output_context(step_key="foo", name="bar", version="version1")
        store.handle_output(context, "cat")
        assert store.has_output(context)
        assert store.load_input(build_input_context(upstream_output=context)) == "cat"
        context_diff_version = build_output_context(step_key="foo", name="bar", version="version2")
        assert not store.has_output(context_diff_version)
