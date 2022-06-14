# isort: skip_file
# pylint: disable=reimported
import os

import pandas as pd
from dagster import AssetKey, AssetMaterialization, IOManager


def read_csv(_path):
    return pd.DataFrame()


# start_marker_0
from dagster import AssetMaterialization, IOManager


class PandasCsvIOManager(IOManager):
    def load_input(self, context):
        file_path = os.path.join("my_base_dir", context.step_key, context.name)
        return read_csv(file_path)

    def handle_output(self, context, obj):
        file_path = os.path.join("my_base_dir", context.step_key, context.name)

        obj.to_csv(file_path)

        context.log_event(
            AssetMaterialization(
                asset_key=AssetKey(file_path),
                description="Persisted result to storage.",
            )
        )


# end_marker_0


# start_marker_1
from dagster import AssetMaterialization, IOManager


class PandasCsvIOManagerWithAsset(IOManager):
    def load_input(self, context):
        file_path = os.path.join("my_base_dir", context.step_key, context.name)
        return read_csv(file_path)

    def handle_output(self, context, obj):
        file_path = os.path.join("my_base_dir", context.step_key, context.name)

        obj.to_csv(file_path)

        context.log_event(
            AssetMaterialization(
                asset_key=AssetKey(file_path),
                description="Persisted result to storage.",
                metadata={
                    "number of rows": obj.shape[0],
                    "some_column mean": obj["some_column"].mean(),
                },
            )
        )


# end_marker_1
