from tempfile import TemporaryDirectory

from dagster import Any, seven
from dagster.core.execution.context.system import InputContext, OutputContext
from dagster.core.storage.memoizable_io_manager import VersionedPickledObjectFilesystemIOManager


def test_versioned_pickled_object_filesystem_io_manager():
    with TemporaryDirectory() as temp_dir:
        store = VersionedPickledObjectFilesystemIOManager(temp_dir)
        context = OutputContext(
            step_key="foo",
            name="bar",
            mapping_key=None,
            metadata={},
            pipeline_name="fake",
            solid_def=None,
            dagster_type=Any,
            run_id=None,
            version="version1",
        )
        store.handle_output(context, "cat")
        assert store.has_output(context)
        assert store.load_input(InputContext(upstream_output=context, pipeline_name="abc")) == "cat"
        context_diff_version = OutputContext(
            step_key="foo",
            name="bar",
            mapping_key=None,
            metadata={},
            pipeline_name="fake",
            solid_def=None,
            dagster_type=Any,
            run_id=None,
            version="version2",
        )
        assert not store.has_output(context_diff_version)
