"""Round-trip I/O manager tests with Pandas against real ClickHouse (Docker)."""

import pandas as pd
import pytest
from clickhouse_driver import Client  # ty: ignore[unresolved-import]
from dagster import AssetKey, Definitions, MetadataValue, asset, materialize
from dagster_clickhouse_pandas import ClickhousePandasIOManager

pytestmark = [pytest.mark.integration]


def test_pandas_io_manager_roundtrip(clickhouse_connection):
    ch_db = "dagster_io_pandas_test"

    @asset(key_prefix=[ch_db])
    def upstream() -> pd.DataFrame:
        return pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

    @asset
    def downstream(upstream: pd.DataFrame) -> None:
        assert list(upstream.columns) == ["a", "b"]
        assert len(upstream) == 3
        assert upstream["a"].tolist() == [1, 2, 3]

    defs = Definitions(
        assets=[upstream, downstream],
        resources={
            "io_manager": ClickhousePandasIOManager(
                host=clickhouse_connection["host"],
                port=clickhouse_connection["port"],
                user=clickhouse_connection["user"],
                password=clickhouse_connection["password"],
                database=clickhouse_connection["database"],
            )
        },
    )
    result = materialize(
        [upstream, downstream],
        resources=defs.resources,
    )
    assert result.success
    assert upstream.key == AssetKey([ch_db, "upstream"])

    upstream_mat = next(
        event.materialization
        for event in result.get_asset_materialization_events()
        if event.asset_key == upstream.key
    )
    assert upstream_mat.metadata["dagster/storage_kind"] == MetadataValue.text("clickhouse")

    client = Client(**clickhouse_connection)
    try:
        client.execute(f"DROP DATABASE IF EXISTS `{ch_db}`")
    finally:
        client.disconnect()
