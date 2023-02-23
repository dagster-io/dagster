from typing import Optional

from dagster._core.definitions.data_version import (
    DataVersion,
    extract_data_version_from_entry,
)
from dagster._core.definitions.decorators.source_asset_decorator import observable_source_asset
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.observe import observe
from dagster._core.instance import DagsterInstance


def _get_current_logical_version(key: AssetKey, instance: DagsterInstance) -> Optional[DataVersion]:
    record = instance.get_latest_logical_version_record(AssetKey("foo"))
    assert record is not None
    return extract_data_version_from_entry(record.event_log_entry)


def test_basic_observe():
    @observable_source_asset
    def foo(_context) -> DataVersion:
        return DataVersion("alpha")

    instance = DagsterInstance.ephemeral()

    observe([foo], instance=instance)
    assert _get_current_logical_version(AssetKey("foo"), instance) == DataVersion("alpha")


def test_observe_tags():
    @observable_source_asset
    def foo(_context) -> DataVersion:
        return DataVersion("alpha")

    instance = DagsterInstance.ephemeral()

    result = observe([foo], instance=instance, tags={"key1": "value1"})
    assert result.success
    assert result.dagster_run.tags == {"key1": "value1"}


def test_observe_raise_on_error():
    @observable_source_asset
    def foo(_context) -> DataVersion:
        raise ValueError()

    instance = DagsterInstance.ephemeral()
    assert not observe([foo], raise_on_error=False, instance=instance).success
