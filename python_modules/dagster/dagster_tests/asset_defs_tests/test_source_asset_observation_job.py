from typing import Optional

import pytest
from dagster._check import CheckError
from dagster._config.pythonic_config import ConfigurableResource
from dagster._core.definitions.data_version import (
    DataVersion,
    extract_data_version_from_entry,
)
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.decorators.source_asset_decorator import observable_source_asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.partition import StaticPartitionsDefinition
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.definitions.unresolved_asset_job_definition import define_asset_job
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.instance import DagsterInstance
from dagster._core.instance_for_test import instance_for_test


def _get_current_data_version(key: AssetKey, instance: DagsterInstance) -> Optional[DataVersion]:
    record = instance.get_latest_data_version_record(key)
    assert record is not None
    return extract_data_version_from_entry(record.event_log_entry)


def test_execute_source_asset_observation_job():
    executed = {}

    @observable_source_asset
    def foo(_context) -> DataVersion:
        executed["foo"] = True
        return DataVersion("alpha")

    @observable_source_asset
    def bar(context):
        executed["bar"] = True
        return DataVersion("beta")

    instance = DagsterInstance.ephemeral()

    result = (
        Definitions(
            assets=[foo, bar],
            jobs=[define_asset_job("source_asset_job", [foo, bar])],
        )
        .get_job_def("source_asset_job")
        .execute_in_process(instance=instance)
    )

    assert result.success
    assert executed["foo"]
    assert _get_current_data_version(AssetKey("foo"), instance) == DataVersion("alpha")
    assert executed["bar"]
    assert _get_current_data_version(AssetKey("bar"), instance) == DataVersion("beta")


@pytest.mark.skip("Temporarily disabling this feature pending GQL UI work")
def test_partitioned_observable_source_asset():
    partitions_def_a = StaticPartitionsDefinition(["A"])
    partitions_def_b = StaticPartitionsDefinition(["B"])

    called = set()

    @observable_source_asset(partitions_def=partitions_def_a)
    def foo(context):
        called.add("foo")
        return DataVersion(context.partition_key)

    @asset(partitions_def=partitions_def_a)
    def bar():
        called.add("bar")
        return 1

    @asset(partitions_def=partitions_def_b)
    def baz():
        return 1

    with instance_for_test() as instance:
        job_def = Definitions(assets=[foo, bar, baz]).get_implicit_job_def_for_assets([foo.key])

        # If the asset selection contains any materializable assets, source assets observations will not run
        job_def.execute_in_process(partition_key="A", instance=instance)
        assert called == {"bar"}

        # If the asset selection contains only observable source assets, source assets are observed
        job_def.execute_in_process(partition_key="A", asset_selection=[foo.key], instance=instance)
        assert called == {"bar", "foo"}
        record = instance.get_latest_data_version_record(AssetKey(["foo"]))
        assert record and extract_data_version_from_entry(record.event_log_entry) == DataVersion(
            "A"
        )


def test_mixed_source_asset_observation_job():
    @observable_source_asset
    def foo(_context) -> DataVersion:
        return DataVersion("alpha")

    @asset(deps=["foo"])
    def bar(context):
        return 1

    with pytest.raises(
        CheckError, match=r"Asset selection specified both regular assets and source assets"
    ):
        Definitions(
            assets=[foo, bar],
            jobs=[define_asset_job("mixed_job", [foo, bar])],
        )


@pytest.mark.parametrize(
    "is_valid,resource_defs",
    [(True, {"bar": ResourceDefinition.hardcoded_resource("bar")}), (False, {})],
)
def test_source_asset_observation_job_with_resource(is_valid, resource_defs):
    executed = {}

    @observable_source_asset(
        required_resource_keys={"bar"},
    )
    def foo(context) -> DataVersion:
        executed["foo"] = True
        return DataVersion(f"{context.resources.bar}")

    instance = DagsterInstance.ephemeral()

    if is_valid:
        result = (
            Definitions(
                assets=[foo],
                jobs=[define_asset_job("source_asset_job", [foo])],
                resources=resource_defs,
            )
            .get_job_def("source_asset_job")
            .execute_in_process(instance=instance)
        )

        assert result.success
        assert executed["foo"]
        assert _get_current_data_version(AssetKey("foo"), instance) == DataVersion("bar")
    else:
        with pytest.raises(
            DagsterInvalidDefinitionError,
            match="resource with key 'bar' required by op 'foo' was not provided",
        ):
            result = (
                Definitions(
                    assets=[foo],
                    jobs=[define_asset_job("source_asset_job", [foo])],
                    resources=resource_defs,
                )
                .get_job_def("source_asset_job")
                .execute_in_process(instance=instance)
            )


class Bar(ConfigurableResource):
    data_version: str


@pytest.mark.parametrize(
    "is_valid,resource_defs",
    [(True, {"bar": Bar(data_version="bar")}), (False, {})],
)
def test_source_asset_observation_job_with_pythonic_resource(is_valid, resource_defs):
    executed = {}

    @observable_source_asset
    def foo(bar: Bar) -> DataVersion:
        executed["foo"] = True
        return DataVersion(f"{bar.data_version}")

    instance = DagsterInstance.ephemeral()

    if is_valid:
        result = (
            Definitions(
                assets=[foo],
                jobs=[define_asset_job("source_asset_job", [foo])],
                resources=resource_defs,
            )
            .get_job_def("source_asset_job")
            .execute_in_process(instance=instance)
        )

        assert result.success
        assert executed["foo"]
        assert _get_current_data_version(AssetKey("foo"), instance) == DataVersion("bar")
    else:
        with pytest.raises(
            DagsterInvalidDefinitionError,
            match="resource with key 'bar' required by op 'foo' was not provided",
        ):
            Definitions(
                assets=[foo],
                jobs=[define_asset_job("source_asset_job", [foo])],
                resources=resource_defs,
            )
