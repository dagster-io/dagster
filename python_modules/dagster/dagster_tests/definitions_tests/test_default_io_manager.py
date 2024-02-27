import pytest
from dagster import (
    IOManagerDefinition,
    asset,
    define_asset_job,
    execute_job,
    job,
    op,
    reconstructable,
)
from dagster._core.definitions.internal_asset_graph import InternalAssetGraph
from dagster._core.errors import DagsterSubprocessError
from dagster._core.storage.fs_io_manager import PickledObjectFilesystemIOManager
from dagster._core.test_utils import environ, instance_for_test


@pytest.fixture
def instance():
    with instance_for_test() as instance:
        yield instance


@op
def fs_io_manager_op(context):
    assert type(context.resources.io_manager) == PickledObjectFilesystemIOManager


@job
def fs_io_manager_job():
    fs_io_manager_op()


def test_default_io_manager(instance):
    result = execute_job(reconstructable(fs_io_manager_job), instance)
    assert result.success


class FooIoManager(PickledObjectFilesystemIOManager):
    def __init__(self, ctx):
        super().__init__(base_dir="/tmp/dagster/foo-io-manager")
        assert ctx.instance


foo_io_manager_def = IOManagerDefinition(
    resource_fn=FooIoManager,
    config_schema={},
)


@op
def foo_io_manager_op(context):
    assert type(context.resources.io_manager) == FooIoManager


@job
def foo_io_manager_job():
    foo_io_manager_op()


def test_override_default_io_manager(instance):
    with environ(
        {
            "DAGSTER_DEFAULT_IO_MANAGER_MODULE": (
                "dagster_tests.definitions_tests.test_default_io_manager"
            ),
            "DAGSTER_DEFAULT_IO_MANAGER_ATTRIBUTE": "foo_io_manager_def",
        }
    ):
        result = execute_job(reconstructable(foo_io_manager_job), instance)
        assert result.success


@asset
def foo_io_manager_asset(context):
    assert type(context.resources.io_manager) == FooIoManager


def create_asset_job():
    return define_asset_job(name="foo_io_manager_asset_job").resolve(
        asset_graph=InternalAssetGraph.from_assets([foo_io_manager_asset])
    )


def test_asset_override_default_io_manager(instance):
    with environ(
        {
            "DAGSTER_DEFAULT_IO_MANAGER_MODULE": (
                "dagster_tests.definitions_tests.test_default_io_manager"
            ),
            "DAGSTER_DEFAULT_IO_MANAGER_ATTRIBUTE": "foo_io_manager_def",
        }
    ):
        result = execute_job(reconstructable(create_asset_job), instance)
        assert result.success


def test_bad_override(instance):
    with pytest.raises(DagsterSubprocessError, match=r"has no attribute \'foo_io_manager_def\'"):
        with environ(
            {
                "DAGSTER_DEFAULT_IO_MANAGER_MODULE": "dagster_tests",
                "DAGSTER_DEFAULT_IO_MANAGER_ATTRIBUTE": "foo_io_manager_def",
            }
        ):
            result = execute_job(reconstructable(fs_io_manager_job), instance, raise_on_error=True)
            assert not result.success

    with environ(
        {
            "DAGSTER_DEFAULT_IO_MANAGER_MODULE": "dagster_tests",
            "DAGSTER_DEFAULT_IO_MANAGER_ATTRIBUTE": "foo_io_manager_def",
            "DAGSTER_DEFAULT_IO_MANAGER_SILENCE_FAILURES": "True",
        }
    ):
        result = execute_job(reconstructable(fs_io_manager_job), instance, raise_on_error=True)
        assert result.success
