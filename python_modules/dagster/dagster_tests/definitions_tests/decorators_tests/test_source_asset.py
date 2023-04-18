from dagster import Definitions
from dagster._core.definitions.assets_job import (
    build_source_asset_observation_job,
)
from dagster._core.definitions.data_version import DataVersion
from dagster._core.definitions.decorators.source_asset_decorator import observable_source_asset
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.definitions.partition import StaticPartitionsDefinition
from dagster._core.storage.io_manager import io_manager


def test_all_fields():
    StaticPartitionsDefinition(["a", "b", "c", "d"])

    @io_manager(required_resource_keys={"baz"})
    def foo_manager():
        pass

    @observable_source_asset(
        name="alpha",
        description="beta",
        key_prefix="delta",
        metadata={"epsilon": "gamma"},
        io_manager_key="lambda",
        io_manager_def=foo_manager,
        group_name="rho",
    )
    def foo_source_asset(context):
        raise Exception("not executed")

    assert foo_source_asset.key == AssetKey(["delta", "alpha"])
    assert foo_source_asset.description == "beta"
    assert foo_source_asset.io_manager_key == "lambda"
    assert foo_source_asset.group_name == "rho"
    assert foo_source_asset.resource_defs == {"lambda": foo_manager}
    assert foo_source_asset.io_manager_def == foo_manager
    assert foo_source_asset.metadata == {"epsilon": MetadataValue.text("gamma")}


def test_no_context_observable_asset():
    executed = {}

    @observable_source_asset
    def observable_asset_no_context():
        executed["yes"] = True
        return DataVersion("version-string")

    asset_job = build_source_asset_observation_job(
        "source_job", source_assets=[observable_asset_no_context]
    )

    defs = Definitions(jobs=[asset_job], assets=[observable_asset_no_context])

    job_def = defs.get_job_def("source_job")

    assert job_def.execute_in_process().success

    assert executed["yes"]
