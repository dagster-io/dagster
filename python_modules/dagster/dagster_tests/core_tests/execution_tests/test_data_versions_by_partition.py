import pytest
from dagster import (
    AssetKey,
    DataVersion,
    DataVersionsByPartition,
    MaterializeResult,
    Output,
    StaticPartitionsDefinition,
    asset,
    materialize,
)
from dagster._core.errors import DagsterInvariantViolationError


def test_data_versions_by_partition_unpartitioned():
    @asset
    def unpartitioned_asset():
        return MaterializeResult(
            data_version=DataVersionsByPartition({"a": "1"})
        )

    with pytest.raises(DagsterInvariantViolationError, match="Cannot use DataVersionsByPartition for unpartitioned asset"):
        materialize([unpartitioned_asset])


def test_data_versions_by_partition_materialize():
    partitions_def = StaticPartitionsDefinition(["a", "b"])

    @asset(partitions_def=partitions_def)
    def my_asset():
        return MaterializeResult(
            data_version=DataVersionsByPartition({"a": "1", "b": "2"})
        )

    # test version info not loaded (the default path usually doesn't have it loaded if not explicitly enabled)
    result = materialize([my_asset], partition_key="a")
    assert result.success

    events = result.get_asset_materialization_events()
    assert len(events) == 1
    tags = events[0].materialization.tags
    assert tags.get("dagster/data_version") == "1"


def test_data_versions_by_partition_output():
    partitions_def = StaticPartitionsDefinition(["a", "b"])

    @asset(partitions_def=partitions_def)
    def output_asset():
        yield Output(None, data_version=DataVersionsByPartition({"a": "1", "b": "2"}))

    result = materialize([output_asset], partition_key="b")
    assert result.success

    events = result.get_asset_materialization_events()
    assert len(events) == 1
    tags = events[0].materialization.tags
    assert tags.get("dagster/data_version") == "2"
