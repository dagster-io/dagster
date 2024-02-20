import os

import pyarrow as pa
import pytest
from dagster import asset, materialize
from dagster_deltalake import DeltaTableResource
from dagster_deltalake.config import AzureConfig, ClientConfig, GcsConfig, LocalConfig, S3Config
from deltalake import write_deltalake


def test_resource(tmp_path):
    data = pa.table(
        {
            "a": pa.array([1, 2, 3], type=pa.int32()),
            "b": pa.array([5, 6, 7], type=pa.int32()),
        }
    )

    @asset
    def create_table(delta_table: DeltaTableResource):
        write_deltalake(delta_table.url, data, storage_options=delta_table.storage_options.dict())

    @asset
    def read_table(delta_table: DeltaTableResource):
        res = delta_table.load().to_pyarrow_table()
        assert res.equals(data)

    materialize(
        [create_table, read_table],
        resources={
            "delta_table": DeltaTableResource(
                url=os.path.join(tmp_path, "table"), storage_options=LocalConfig()
            )
        },
    )


def test_resource_versioned(tmp_path):
    data = pa.table(
        {
            "a": pa.array([1, 2, 3], type=pa.int32()),
            "b": pa.array([5, 6, 7], type=pa.int32()),
        }
    )

    @asset
    def create_table(delta_table: DeltaTableResource):
        write_deltalake(delta_table.url, data, storage_options=delta_table.storage_options.dict())
        write_deltalake(
            delta_table.url, data, storage_options=delta_table.storage_options.dict(), mode="append"
        )

    @asset
    def read_table(delta_table: DeltaTableResource):
        res = delta_table.load().to_pyarrow_table()
        assert res.equals(data)

    materialize(
        [create_table, read_table],
        resources={
            "delta_table": DeltaTableResource(
                url=os.path.join(tmp_path, "table"), storage_options=LocalConfig(), version=0
            )
        },
    )


@pytest.mark.parametrize(
    "config",
    [
        LocalConfig(),
        AzureConfig(account_name="test", use_azure_cli=True),
        GcsConfig(bucket="test"),
        S3Config(bucket="test"),
        ClientConfig(timeout=1),
    ],
)
def test_resource_storage_options(tmp_path, config):
    data = pa.table(
        {
            "a": pa.array([1, 2, 3], type=pa.int32()),
            "b": pa.array([5, 6, 7], type=pa.int32()),
        }
    )

    write_deltalake(os.path.join(tmp_path, "table"), data, storage_options=config.dict())
