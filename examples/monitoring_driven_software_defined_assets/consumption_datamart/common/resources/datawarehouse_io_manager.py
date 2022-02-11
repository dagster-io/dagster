from dagster import IOManager
from dagster_pandas import DataFrame


class DataWarehouseIOManager(IOManager):

    def __init__(self, datawarehouse_resource) -> None:
        super().__init__()
        self.datawarehouse_resource = datawarehouse_resource

    def handle_output(self, context, df: DataFrame):
        schema = context.asset_key.path[-2]
        table = context.asset_key.path[-1]
        at_date = context.partition_key
        self.datawarehouse_resource.update_snapshot_partition(df, schema, table, at_date)

    def load_input(self, context):
        if hasattr(context, 'upstream_output'):  # We're dealing with a foreign asset
            asset_out = context.upstream_output
        else:  # We're dealing with an asset
            asset_out = context.solid_def.outs['result']

        metadata = asset_out.metadata
        dagster_type = asset_out.metadata['dagster_type']

        df = self.datawarehouse_resource.read_sql_query(metadata['load_sql'])
        typed_df = dagster_type.convert_dtypes(df)

        dagster_type.calculate_data_quality(typed_df)

        return typed_df
