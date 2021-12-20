from abc import abstractmethod, ABC

from dagster import IOManager, io_manager
from dagster_pandas import DataFrame


class SQLLakeIOManager(IOManager, ABC):

    def __init__(self, datawarehouse_resource) -> None:
        super().__init__()
        self.datawarehouse_resource = datawarehouse_resource

    def handle_output(self, context, obj: DataFrame):
        pass

    @abstractmethod
    def load_input(self, context):
        pass


class AssetSQLLakeIOManager(SQLLakeIOManager):

    def load_input(self, context):
        asset_out = context.solid_def.outs['result']
        metadata = asset_out.metadata
        dagster_type = asset_out.metadata['dagster_type']

        df = self.datawarehouse_resource.read_sql_query(metadata['load_sql'])
        typed_df = dagster_type.convert_dtypes(df)

        dagster_type.calculate_data_quality(typed_df)

        return typed_df


class ForeignAssetSQLLakeIOManager(SQLLakeIOManager):

    def load_input(self, context):
        asset_out = context.upstream_output
        metadata = asset_out.metadata
        dagster_type = asset_out.metadata['dagster_type']

        df = self.datawarehouse_resource.read_sql_query(metadata['load_sql'])
        typed_df = dagster_type.convert_dtypes(df)

        dagster_type.calculate_data_quality(typed_df)

        # When AssetObservation is implemented, emit metadata about the (foreign) Asset just loaded
        # yield AssetObservation(
        #     asset_key=context.asset_key,
        #     metadata=dagster_type.extract_event_metadata(typed_df),
        # )

        return typed_df


@io_manager(
    required_resource_keys={'datawarehouse'},
)
def asset_lake_input_manager(init_context):
    return AssetSQLLakeIOManager(datawarehouse_resource=init_context.resources.datawarehouse)


@io_manager(
    required_resource_keys={'datawarehouse'},
)
def foreign_asset_lake_input_manager(init_context):
    return ForeignAssetSQLLakeIOManager(datawarehouse_resource=init_context.resources.datawarehouse)
