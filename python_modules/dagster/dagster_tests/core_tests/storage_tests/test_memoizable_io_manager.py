from tempfile import TemporaryDirectory

from dagster import Any
from dagster.core.execution.build_resources import initialize_console_manager
from dagster.core.execution.context.input import InputContext
from dagster.core.execution.context.output import OutputContext
from dagster.core.storage.memoizable_io_manager import VersionedPickledObjectFilesystemIOManager


def test_versioned_pickled_object_filesystem_io_manager():
    console_manager = initialize_console_manager(None)
    with TemporaryDirectory() as temp_dir:
        store = VersionedPickledObjectFilesystemIOManager(temp_dir)
        context = OutputContext(
            step_key="foo",
            name="bar",
            mapping_key=None,
            log_manager=console_manager,
            metadata={},
            pipeline_name="fake",
            solid_def=None,
            dagster_type=Any,
            run_id=None,
            version="version1",
        )
        store.handle_output(context, "cat")
        assert store.has_output(context)
        assert (
            store.load_input(
                InputContext(
                    upstream_output=context, pipeline_name="abc", log_manager=console_manager
                )
            )
            == "cat"
        )
        context_diff_version = OutputContext(
            step_key="foo",
            name="bar",
            mapping_key=None,
            log_manager=console_manager,
            metadata={},
            pipeline_name="fake",
            solid_def=None,
            dagster_type=Any,
            run_id=None,
            version="version2",
        )
        assert not store.has_output(context_diff_version)
