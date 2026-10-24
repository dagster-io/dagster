import pandas as pd

from dagster import MultiPartitionKey, materialize
from docs_snippets.guides.build.partitions_backfills.partitioning.two_dimensional_partitioning import (
    daily_regional_sales_data,
    daily_regional_sales_summary,
)


def test_two_dimensional_partitioning(tmp_path, monkeypatch):
    # the snippet writes its CSV relative to the working directory
    monkeypatch.chdir(tmp_path)

    partition_key = MultiPartitionKey({"date": "2024-01-01", "region": "us"})
    result = materialize(
        [daily_regional_sales_data, daily_regional_sales_summary],
        partition_key=partition_key,
    )
    assert result.success

    # each dimension of the partition key must reach the asset body
    df = pd.read_csv(
        tmp_path / "data" / "daily_regional_sales" / "sales_2024-01-01|us.csv"
    )
    assert set(df["date"]) == {"2024-01-01"}
    assert set(df["region"]) == {"us"}
