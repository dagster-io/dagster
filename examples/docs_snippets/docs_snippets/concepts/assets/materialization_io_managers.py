# isort: skip_file
# pylint: disable=reimported
import os

import pandas as pd
from dagster import AssetKey, AssetMaterialization, IOManager, MetadataEntry


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


# start_asset_def
from dagster import AssetKey, IOManager, MetadataEntry


class PandasCsvIOManagerWithOutputAsset(IOManager):
    def load_input(self, context):
        file_path = os.path.join("my_base_dir", context.step_key, context.name)
        return read_csv(file_path)

    def handle_output(self, context, obj):
        file_path = os.path.join("my_base_dir", context.step_key, context.name)

        obj.to_csv(file_path)

        yield MetadataEntry.int(obj.shape[0], label="number of rows")
        yield MetadataEntry.float(obj["some_column"].mean(), "some_column mean")

    def get_output_asset_key(self, context):
        file_path = os.path.join("my_base_dir", context.step_key, context.name)
        return AssetKey(file_path)


# end_asset_def

# start_partitioned_asset_def
from dagster import AssetKey, IOManager, MetadataEntry


class PandasCsvIOManagerWithOutputAssetPartitions(IOManager):
    def load_input(self, context):
        file_path = os.path.join("my_base_dir", context.step_key, context.name)
        return read_csv(file_path)

    def handle_output(self, context, obj):
        file_path = os.path.join("my_base_dir", context.step_key, context.name)

        obj.to_csv(file_path)

        yield MetadataEntry.int(obj.shape[0], label="number of rows")
        yield MetadataEntry.float(obj["some_column"].mean(), "some_column mean")

    def get_output_asset_key(self, context):
        file_path = os.path.join("my_base_dir", context.step_key, context.name)
        return AssetKey(file_path)

    def get_output_asset_partitions(self, context):
        return set(context.config["partitions"])


# end_partitioned_asset_def
