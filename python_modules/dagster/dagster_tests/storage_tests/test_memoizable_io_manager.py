import os
from tempfile import TemporaryDirectory

from dagster import (
    ResourceDefinition,
    build_init_resource_context,
    build_input_context,
    build_output_context,
    io_manager,
    job,
    op,
)
from dagster._core.storage.memoizable_io_manager import (
    MemoizableIOManager,
    VersionedPickledObjectFilesystemIOManager,
    versioned_filesystem_io_manager,
)
from dagster._core.storage.tags import MEMOIZED_RUN_TAG
from dagster._core.test_utils import instance_for_test


def test_versioned_pickled_object_filesystem_io_manager():
    with TemporaryDirectory() as temp_dir:
        store = VersionedPickledObjectFilesystemIOManager(temp_dir)
        context = build_output_context(step_key="foo", name="bar", version="version1")
        store.handle_output(context, "cat")
        assert store.has_output(context)
        assert store.load_input(build_input_context(upstream_output=context)) == "cat"
        context_diff_version = build_output_context(step_key="foo", name="bar", version="version2")
        assert not store.has_output(context_diff_version)


def test_versioned_io_manager_with_resources():
    occurrence_log = []

    @io_manager(required_resource_keys={"foo"})
    def construct_memoizable_io_manager(_):
        class FakeIOManager(MemoizableIOManager):
            def handle_output(self, context, _obj):
                occurrence_log.append("handle")
                assert context.resources.foo == "bar"

            def load_input(self, context):
                occurrence_log.append("load")
                assert context.resources.foo == "bar"

            def has_output(self, context):
                occurrence_log.append("has")
                assert context.resources.foo == "bar"

        return FakeIOManager()

    @op(version="baz")
    def basic_op():
        pass

    @job(
        resource_defs={
            "io_manager": construct_memoizable_io_manager,
            "foo": ResourceDefinition.hardcoded_resource("bar"),
        },
        tags={MEMOIZED_RUN_TAG: "true"},
    )
    def basic_job():
        basic_op()

    with instance_for_test() as instance:
        basic_job.execute_in_process(instance=instance)

    assert occurrence_log == ["has", "handle"]


def test_versioned_filesystem_io_manager_default_base_dir():
    with TemporaryDirectory() as temp_dir:
        with instance_for_test(temp_dir=temp_dir) as instance:
            my_io_manager = versioned_filesystem_io_manager(
                build_init_resource_context(instance=instance)
            )
            assert my_io_manager.base_dir == os.path.join(
                instance.storage_directory(), "versioned_outputs"
            )
