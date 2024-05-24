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
        write_deltalake(
            delta_table.url, data, storage_options=delta_table.storage_options.str_dict()
        )

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
        write_deltalake(
            delta_table.url, data, storage_options=delta_table.storage_options.str_dict()
        )
        write_deltalake(
            delta_table.url,
            data,
            storage_options=delta_table.storage_options.str_dict(),
            mode="append",
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
def test_config_classes_are_string_dicts(tmp_path, config):
    data = pa.table(
        {
            "a": pa.array([1, 2, 3], type=pa.int32()),
            "b": pa.array([5, 6, 7], type=pa.int32()),
        }
    )
    config_dict = config.str_dict()
    assert all([isinstance(val, str) for val in config_dict.values()])
    # passing the config_dict to write_deltalake validates that all dict values are str.
    # it will throw an exception if there are other value types
    write_deltalake(os.path.join(tmp_path, "table"), data, storage_options=config_dict)
