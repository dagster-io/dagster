import datetime
import json

from dagster import StaticPartitionsDefinition, asset
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._daemon.asset_daemon import (
    asset_daemon_cursor_from_pre_sensor_auto_materialize_serialized_cursor,
)
from dagster._serdes.serdes import serialize_value

partitions = StaticPartitionsDefinition(partition_keys=["a", "b", "c"])


@asset(partitions_def=partitions)
def my_asset(_):
    pass


def test_asset_reconciliation_cursor_evaluation_id_backcompat() -> None:
    # we no longer attempt to deserialize asset information from this super-old cursor format
    # instead, the next tick after a transition will just start from a clean slate (preserving
    # the evaluation id)
    backcompat_serialized = (
        """[20, ["a"], {"my_asset": "{\\"version\\": 1, \\"subset\\": [\\"a\\"]}"}]"""
    )

    assert asset_daemon_cursor_from_pre_sensor_auto_materialize_serialized_cursor(
        backcompat_serialized, None
    ) == AssetDaemonCursor.empty(20)

    asset_graph = AssetGraph.from_assets([my_asset])
    c = asset_daemon_cursor_from_pre_sensor_auto_materialize_serialized_cursor(
        backcompat_serialized, asset_graph
    )

    assert c == AssetDaemonCursor.empty(20)

    c2 = c.with_updates(21, datetime.datetime.now().timestamp(), [], [])

    serdes_c2 = asset_daemon_cursor_from_pre_sensor_auto_materialize_serialized_cursor(
        serialize_value(c2), asset_graph
    )
    assert serdes_c2 == c2
    assert serdes_c2.evaluation_id == 21

    assert (
        asset_daemon_cursor_from_pre_sensor_auto_materialize_serialized_cursor(
            serialize_value(c2), None
        ).evaluation_id
        == 21
    )


def test_asset_reconciliation_cursor_auto_observe_backcompat() -> None:
    partitions_def = StaticPartitionsDefinition(["a", "b", "c"])

    @asset(partitions_def=partitions_def)
    def asset1():
        ...

    @asset
    def asset2():
        ...

    handled_root_partitions_by_asset_key = {
        asset1.key: partitions_def.subset_with_partition_keys(["a", "b"])
    }
    handled_root_asset_keys = {asset2.key}
    serialized = json.dumps(
        (
            25,
            [key.to_user_string() for key in handled_root_asset_keys],
            {
                key.to_user_string(): subset.serialize()
                for key, subset in handled_root_partitions_by_asset_key.items()
            },
        )
    )

    cursor = asset_daemon_cursor_from_pre_sensor_auto_materialize_serialized_cursor(
        serialized, AssetGraph.from_assets([asset1, asset2])
    )
    assert cursor.evaluation_id == 25
