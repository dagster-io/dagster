import dagster as dg
import pytest
from dagster._core.definitions.assets.graph.asset_graph import AssetGraph
from dagster._core.storage.fs_io_manager import PickledObjectFilesystemIOManager
from dagster._core.test_utils import environ


@pytest.fixture
def instance():
    with dg.instance_for_test() as instance:
        yield instance


@dg.op
def fs_io_manager_op(context):
    assert type(context.resources.io_manager) == PickledObjectFilesystemIOManager


@dg.job
def fs_io_manager_job():
    fs_io_manager_op()


def test_default_io_manager(instance):
    result = dg.execute_job(dg.reconstructable(fs_io_manager_job), instance)
    assert result.success


class FooIoManager(PickledObjectFilesystemIOManager):
    def __init__(self, ctx):
        super().__init__(base_dir="/tmp/dagster/foo-io-manager")
        assert ctx.instance


foo_io_manager_def = dg.IOManagerDefinition(
    resource_fn=FooIoManager,
    config_schema={},
)


@dg.op
def foo_io_manager_op(context):
    assert type(context.resources.io_manager) == FooIoManager


@dg.job
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
        result = dg.execute_job(dg.reconstructable(foo_io_manager_job), instance)
        assert result.success


@dg.asset
def foo_io_manager_asset(context):
    assert type(context.resources.io_manager) == FooIoManager


@dg.asset_check(asset=foo_io_manager_asset)
def check_foo(context, foo_io_manager_asset):
    assert foo_io_manager_asset is None
    assert type(context.resources.io_manager) == FooIoManager
    return dg.AssetCheckResult(passed=True)


def create_asset_job():
    return dg.define_asset_job(name="foo_io_manager_asset_job").resolve(
        asset_graph=AssetGraph.from_assets([foo_io_manager_asset, check_foo])
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
        result = dg.execute_job(dg.reconstructable(create_asset_job), instance)
        assert result.success


def test_bad_override(instance):
    with pytest.raises(dg.DagsterSubprocessError, match=r"has no attribute \'foo_io_manager_def\'"):
        with environ(
            {
                "DAGSTER_DEFAULT_IO_MANAGER_MODULE": "dagster_tests",
                "DAGSTER_DEFAULT_IO_MANAGER_ATTRIBUTE": "foo_io_manager_def",
            }
        ):
            result = dg.execute_job(
                dg.reconstructable(fs_io_manager_job), instance, raise_on_error=True
            )
            assert not result.success

    with environ(
        {
            "DAGSTER_DEFAULT_IO_MANAGER_MODULE": "dagster_tests",
            "DAGSTER_DEFAULT_IO_MANAGER_ATTRIBUTE": "foo_io_manager_def",
            "DAGSTER_DEFAULT_IO_MANAGER_SILENCE_FAILURES": "True",
        }
    ):
        result = dg.execute_job(
            dg.reconstructable(fs_io_manager_job), instance, raise_on_error=True
        )
        assert result.success
