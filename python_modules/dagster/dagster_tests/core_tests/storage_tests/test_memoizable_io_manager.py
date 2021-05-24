from tempfile import TemporaryDirectory

from dagster import (
    ModeDefinition,
    ResourceDefinition,
    build_input_context,
    build_output_context,
    execute_pipeline,
    io_manager,
    pipeline,
    solid,
)
from dagster.core.storage.memoizable_io_manager import (
    MemoizableIOManager,
    VersionedPickledObjectFilesystemIOManager,
)
from dagster.core.storage.tags import MEMOIZED_RUN_TAG


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

    @solid(version="baz")
    def basic_solid():
        pass

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "io_manager": construct_memoizable_io_manager,
                    "foo": ResourceDefinition.hardcoded_resource("bar"),
                }
            )
        ],
        tags={MEMOIZED_RUN_TAG: "true"},
    )
    def basic_pipeline():
        basic_solid()

    execute_pipeline(basic_pipeline)

    assert occurrence_log == ["has", "has", "handle"]
