from typing import Optional

import pytest
from dagster import IOManager, asset
from dagster._core.definitions.data_version import DataVersion, extract_data_version_from_entry
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.metadata import TextMetadataValue
from dagster._core.definitions.observe import observe
from dagster._core.definitions.result import ObserveResult
from dagster._core.errors import DagsterInvalidObservationError
from dagster._core.instance import DagsterInstance


def _get_current_data_version(key: AssetKey, instance: DagsterInstance) -> Optional[DataVersion]:
    record = instance.get_latest_data_version_record(key)
    assert record is not None
    return extract_data_version_from_entry(record.event_log_entry)


def test_basic_observe():
    @asset(result_type="observe")
    def foo():
        return ObserveResult(data_version=DataVersion("alpha"))

    instance = DagsterInstance.ephemeral()

    observe([foo], instance=instance)
    assert _get_current_data_version(AssetKey("foo"), instance) == DataVersion("alpha")


def test_basic_observe_direct_data_version():
    @asset(result_type="observe")
    def foo() -> DataVersion:
        return DataVersion("alpha")

    instance = DagsterInstance.ephemeral()

    with pytest.raises(
        DagsterInvalidObservationError,
        match="Observation function must return ObserveResult, but returned output with value of type",
    ):
        observe([foo], instance=instance)


def test_observe_handle_output():
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            raise NotImplementedError("Shouldn't get here")

        def load_input(self, context):
            raise NotImplementedError("Shouldn't get here")

    @asset(result_type="observe")
    def foo() -> ObserveResult:
        return ObserveResult()

    instance = DagsterInstance.ephemeral()

    assert observe([foo], instance=instance, resources={"io_manager": MyIOManager()}).success


def test_observe_with_observe_result():
    @asset(result_type="observe")
    def foo() -> ObserveResult:
        return ObserveResult(data_version=DataVersion("alpha"), metadata={"foo": "bar"})

    instance = DagsterInstance.ephemeral()
    result = observe([foo], instance=instance)
    assert result.success
    observations = result.asset_observations_for_node("foo")
    assert len(observations) == 1
    assert _get_current_data_version(AssetKey("foo"), instance) == DataVersion("alpha")
    assert observations[0].metadata == {"foo": TextMetadataValue("bar")}


def test_observe_with_observe_result_no_data_version():
    @asset(result_type="observe")
    def foo() -> ObserveResult:
        return ObserveResult(metadata={"foo": "bar"})

    instance = DagsterInstance.ephemeral()
    result = observe([foo], instance=instance)
    assert result.success
    observations = result.asset_observations_for_node("foo")
    assert len(observations) == 1
    assert _get_current_data_version(AssetKey("foo"), instance) is None
    assert observations[0].metadata == {"foo": TextMetadataValue("bar")}
