import os

import pandas as pd
from dagster import asset, materialize
from dagster_deltalake import DeltaTableResource
from dagster_deltalake.config import LocalConfig
from deltalake.writer import write_deltalake


def test_resource(tmp_path):
    df = pd.DataFrame({"a": [1, 2, 3], "b": [5, 6, 7]})

    @asset
    def create_table(delta_table: DeltaTableResource):
        write_deltalake(delta_table.url, df, storage_options=delta_table.storage_options.dict())

    @asset
    def read_table(delta_table: DeltaTableResource):
        res = delta_table.load().to_pandas()
        assert res.equals(df)

    materialize(
        [create_table, read_table],
        resources={
            "delta_table": DeltaTableResource(
                url=os.path.join(tmp_path, "table"), storage_options=LocalConfig()
            )
        },
    )
