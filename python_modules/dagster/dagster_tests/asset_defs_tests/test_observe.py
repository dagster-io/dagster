from typing import Optional

import dagster as dg
import pytest
from dagster._core.definitions.data_version import extract_data_version_from_entry
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.observe import observe
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.errors import DagsterInvalidObservationError
from dagster._core.instance import DagsterInstance


def _get_current_data_version(
    key: AssetKey, instance: DagsterInstance, partition_key: Optional[str] = None
) -> Optional[dg.DataVersion]:
    record = instance.get_latest_data_version_record(key)
    assert record is not None
    return extract_data_version_from_entry(record.event_log_entry)


def test_basic_observe():
    @dg.observable_source_asset
    def foo(_context) -> dg.DataVersion:
        return dg.DataVersion("alpha")

    instance = DagsterInstance.ephemeral()

    observe([foo], instance=instance)
    assert _get_current_data_version(dg.AssetKey("foo"), instance) == dg.DataVersion("alpha")


def test_observe_partitions():
    @dg.observable_source_asset(
        partitions_def=dg.StaticPartitionsDefinition(["apple", "orange", "kiwi"])
    )
    def foo():
        return dg.DataVersionsByPartition({"apple": "one", "orange": dg.DataVersion("two")})

    result = observe([foo])
    observations = result.asset_observations_for_node("foo")
    assert len(observations) == 2
    observations_by_asset_partition = {
        (observation.asset_key, observation.partition): observation for observation in observations
    }
    assert observations_by_asset_partition.keys() == {(foo.key, "apple"), (foo.key, "orange")}
    assert observations_by_asset_partition[(foo.key, "apple")].tags == {
        "dagster/data_version": "one"
    }
    assert observations_by_asset_partition[(foo.key, "orange")].tags == {
        "dagster/data_version": "two"
    }


def test_observe_result_partitions():
    @dg.observable_source_asset(
        partitions_def=dg.StaticPartitionsDefinition(["apple", "orange", "kiwi"])
    )
    def foo():
        return dg.ObserveResult(
            asset_key=foo.key,
            data_version=dg.DataVersionsByPartition({"apple": "one", "orange": dg.DataVersion("two")})
        )

    result = observe([foo])
    observations = result.asset_observations_for_node("foo")
    assert len(observations) == 2
    observations_by_asset_partition = {
        (observation.asset_key, observation.partition): observation for observation in observations
    }
    assert observations_by_asset_partition.keys() == {(foo.key, "apple"), (foo.key, "orange")}
    assert observations_by_asset_partition[(foo.key, "apple")].tags == {
        "dagster/data_version": "one"
    }
    assert observations_by_asset_partition[(foo.key, "orange")].tags == {
        "dagster/data_version": "two"
    }


def test_multi_observe_partitions():
    @dg.multi_observable_source_asset(
        specs=[
            dg.AssetSpec(
                key=["multi", "foo"],
                partitions_def=dg.StaticPartitionsDefinition(["apple", "orange", "kiwi"]),
            )
        ],
        can_subset=True
    )
    def foo(context: dg.AssetExecutionContext):
        for asset_key in context.selected_asset_keys:
            yield dg.ObserveResult(
                asset_key=asset_key,
                data_version=dg.DataVersionsByPartition({"apple": "one", "orange": dg.DataVersion("two")}),
            )
    observe([foo])



def test_observe_partitions_non_partitioned_asset():
    @dg.observable_source_asset
    def foo():
        return dg.DataVersionsByPartition({"apple": "one", "orange": dg.DataVersion("two")})

    with pytest.raises(DagsterInvalidObservationError):
        observe([foo])


def test_observe_data_version_partitioned_asset():
    @dg.observable_source_asset(
        partitions_def=dg.StaticPartitionsDefinition(["apple", "orange", "kiwi"])
    )
    def foo():
        return dg.DataVersion("one")

    with pytest.raises(DagsterInvalidObservationError):
        observe([foo])


def test_observe_tags():
    @dg.observable_source_asset
    def foo(_context) -> dg.DataVersion:
        return dg.DataVersion("alpha")

    instance = DagsterInstance.ephemeral()

    result = observe([foo], instance=instance, tags={"key1": "value1"})
    assert result.success
    assert result.dagster_run.tags == {"key1": "value1"}


def test_observe_raise_on_error():
    @dg.observable_source_asset
    def foo(_context) -> dg.DataVersion:
        raise ValueError()

    instance = DagsterInstance.ephemeral()
    assert not observe([foo], raise_on_error=False, instance=instance).success


@pytest.mark.parametrize(
    "is_valid,resource_defs",
    [(True, {"bar": ResourceDefinition.hardcoded_resource("bar")}), (False, {})],
)
def test_observe_resource(is_valid, resource_defs):
    @dg.observable_source_asset(
        required_resource_keys={"bar"},
        resource_defs=resource_defs,
    )
    def foo(context) -> dg.DataVersion:
        return dg.DataVersion(f"{context.resources.bar}-alpha")

    instance = DagsterInstance.ephemeral()

    if is_valid:
        observe([foo], instance=instance)
        assert _get_current_data_version(dg.AssetKey("foo"), instance) == dg.DataVersion(
            "bar-alpha"
        )
    else:
        with pytest.raises(
            dg.DagsterInvalidDefinitionError,
            match="resource with key 'bar' required by op 'foo' was not provided",
        ):
            observe([foo], instance=instance)


@pytest.mark.parametrize(
    "is_valid,config_value",
    [(True, {"resources": {"bar": {"config": {"baz": "baz"}}}}), (False, {"fake": "fake"})],
)
def test_observe_config(is_valid, config_value):
    @dg.resource(config_schema={"baz": str})
    def bar(context):
        return context.resource_config["baz"]

    @dg.observable_source_asset(required_resource_keys={"bar"}, resource_defs={"bar": bar})
    def foo(context) -> dg.DataVersion:
        return dg.DataVersion(f"{context.resources.bar}-alpha")

    instance = DagsterInstance.ephemeral()

    if is_valid:
        observe([foo], instance=instance, run_config=config_value)
        assert _get_current_data_version(dg.AssetKey("foo"), instance) == dg.DataVersion(
            "baz-alpha"
        )
    else:
        with pytest.raises(dg.DagsterInvalidConfigError, match="Error in config for job"):
            observe([foo], instance=instance, run_config=config_value)


def test_observe_handle_output():
    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            raise NotImplementedError("Shouldn't get here")

        def load_input(self, context):
            raise NotImplementedError("Shouldn't get here")

    @dg.observable_source_asset
    def foo() -> dg.DataVersion:
        return dg.DataVersion("alpha")

    instance = DagsterInstance.ephemeral()

    assert observe([foo], instance=instance, resources={"io_manager": MyIOManager()}).success


def test_observe_with_observe_result():
    @dg.observable_source_asset
    def foo() -> dg.ObserveResult:
        return dg.ObserveResult(data_version=dg.DataVersion("alpha"), metadata={"foo": "bar"})

    instance = DagsterInstance.ephemeral()
    result = observe([foo], instance=instance)
    assert result.success
    observations = result.asset_observations_for_node("foo")
    assert len(observations) == 1
    assert _get_current_data_version(dg.AssetKey("foo"), instance) == dg.DataVersion("alpha")
    assert observations[0].metadata == {"foo": dg.TextMetadataValue("bar")}


def test_observe_with_observe_result_no_data_version():
    @dg.observable_source_asset
    def foo() -> dg.ObserveResult:
        return dg.ObserveResult(metadata={"foo": "bar"})

    instance = DagsterInstance.ephemeral()
    result = observe([foo], instance=instance)
    assert result.success
    observations = result.asset_observations_for_node("foo")
    assert len(observations) == 1
    assert _get_current_data_version(dg.AssetKey("foo"), instance) is None
    assert observations[0].metadata == {"foo": dg.TextMetadataValue("bar")}


def test_observe_pythonic_resource():
    with dg.instance_for_test() as instance:

        class FooResource(dg.ConfigurableResource):
            foo: str

        @dg.observable_source_asset
        def foo(foo: FooResource) -> dg.DataVersion:
            return dg.DataVersion(f"{foo.foo}-alpha")

        observe([foo], instance=instance, resources={"foo": FooResource(foo="bar")})
        assert _get_current_data_version(dg.AssetKey("foo"), instance) == dg.DataVersion(
            "bar-alpha"
        )


def test_observe_backcompat_pythonic_resource():
    class FooResource(dg.ConfigurableResource):
        foo: str

        def get_object_to_set_on_execution_context(self):
            raise Exception("Shouldn't get here")

    @dg.observable_source_asset
    def foo(foo: FooResource) -> dg.DataVersion:
        return dg.DataVersion(f"{foo.foo}-alpha")

    instance = DagsterInstance.ephemeral()

    observe([foo], instance=instance, resources={"foo": FooResource(foo="bar")})
    assert _get_current_data_version(dg.AssetKey("foo"), instance) == dg.DataVersion("bar-alpha")
