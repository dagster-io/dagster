import datetime
import json

from dagster import AssetKey, StaticPartitionsDefinition, asset
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster._core.definitions.asset_graph import AssetGraph

partitions = StaticPartitionsDefinition(partition_keys=["a", "b", "c"])


@asset(partitions_def=partitions)
def my_asset(_):
    pass


def test_forwards_compat() -> None:
    forwardscompat_serialized = """H4sIAJGshGUC/+1aa2vcOBT9K8IwtF2aRbblV76FtFAo+6DNUpYyCD2uMqZ+rSXn0ZD/XsnOzKQdtylNwiZBzIeMdB/SPT5n4it0EVAqKqY1pcE+Cg60BvOKQd02h0Ov2z54iQLmJqkYx9p6fbyYCTpsG1macjfuE5xbp7mQt9Zi3TpmVi5rcBAsL+0YzkzPfnad15OzDRNrA9UN6/SqNd9ZdpPh/drPRa/KStIV0ysYl166uTGwYTW42HdDBZtQFyJBi77sxqG1N61BNTPQl6wqP4NEumwEIJvDING3DdJiBdImQaYUn1Cr0DOMfps+z9BzU9bwuW1gH/1zdPgi+AqIi0s7fFRgnDJraY6RLXvotOmB1Ugyw5BpEQc7ZwcgH3uVcCYApEbhtQfPnPG5foE66FFdNoOBnTLdSl0PJ2U7aAonrBrYVcofbv711tNtldlpByPVA7du1r8ZqmpT2DbvzVp6oJmXT1LWU+manpZmRWswzAljvTnTD9fAmavz/WT89d9XhzHshhzZnX4oG9me/s16M8Kht2vZoqtBgqSuILt15zf39LdZXBQ0cn4hbVjdfbAAHF3h47zN2mC9wjjJSEwwxr/jK9PoZuMtkBOOxu7zVukx+V76UaLNUNNug4WLGtFcT1AJ6udgfAWqbDYEc6yha9a4kA1ftpBdqcIOaKvURAa3UVW7b8Hi371FvbeQe4s3+4s/gjsAIyY/xHoXoAmiu1VnwGOV4yyPU8gUiQiXBEKSqCyz8zFPcLCr37/6r/PPSPigObe69Nrz2nsy2nt5yzcFT25P7odK7vt5z/SM94z3jPeM94x/yIxfPq6zq6fVTszSFnva3m/PKwiO45wxQmKpeBZyOyrSmCv7Nw9x5nteT9L/naQhgyQuwpBAiiMe4SRNQ5BERQQinofhDEn/bM2NLLU+/ljGv9X4YxlPbk9u36R6xnvG+yb1zq8e+AbANwC3bQCiNBeFEDwMccpTYlsBnic4L3CUYFYI5hsA/x/DK+8+lJcUUQiCKBJLDDxOBZepVFaGAscghHRBEecZBpZmSaoYFEmUpTInChPFWJZj4XwKpopICRAxhoRLYEmW5BnBWc5yADXXwh808uaDpqrylyu8iJ9WFz93O5POPMU4njJv3Gt2RrVpe3YMtFzXO2J+LdFoIHbOXSKkrWVifwK0h/8Gm3+7DOXn9Fsl1KzryuaYlgbqCYmPy8vLL9G5ZgjFLQAA"""
    asset_graph = AssetGraph.from_assets([my_asset])
    assert (
        AssetDaemonCursor.from_serialized(forwardscompat_serialized, asset_graph)
        == AssetDaemonCursor.empty()
    )


def test_asset_reconciliation_cursor_evaluation_id_backcompat() -> None:
    backcompat_serialized = (
        """[20, ["a"], {"my_asset": "{\\"version\\": 1, \\"subset\\": [\\"a\\"]}"}]"""
    )

    assert AssetDaemonCursor.get_evaluation_id_from_serialized(backcompat_serialized) is None

    asset_graph = AssetGraph.from_assets([my_asset])
    c = AssetDaemonCursor.from_serialized(backcompat_serialized, asset_graph)

    assert c == AssetDaemonCursor(
        20,
        {AssetKey("a")},
        {AssetKey("my_asset"): partitions.empty_subset().with_partition_keys(["a"])},
        0,
        {},
        {},
        0,
    )

    c2 = c.with_updates(
        21,
        1,
        [],
        0,
        [],
        datetime.datetime.now(),
        [],
    )

    serdes_c2 = AssetDaemonCursor.from_serialized(c2.serialize(), asset_graph)
    assert serdes_c2 == c2
    assert serdes_c2.evaluation_id == 1

    assert AssetDaemonCursor.get_evaluation_id_from_serialized(c2.serialize()) == 1


def test_asset_reconciliation_cursor_auto_observe_backcompat():
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

    cursor = AssetDaemonCursor.from_serialized(
        serialized, asset_graph=AssetGraph.from_assets([asset1, asset2])
    )
    assert cursor.latest_storage_id == 25
    assert cursor.handled_root_asset_keys == handled_root_asset_keys
    assert cursor.handled_root_partitions_by_asset_key == handled_root_partitions_by_asset_key
