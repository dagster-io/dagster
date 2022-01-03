from pathlib import Path

from consumption_datamart.resources.datawarehouse.sqlite import SQLiteDatawarehouseResource, SQLiteSchema
from dagster import Field
from dagster import IOManager, io_manager
from dagster_pandas import DataFrame


class DataWarehouseIOManager(IOManager):

    def __init__(self, datawarehouse_resource) -> None:
        super().__init__()
        self.datawarehouse_resource = datawarehouse_resource

    def handle_output(self, context, obj: DataFrame):
        context.log.warn("TODO: Implement logic to save output to datawarehouse")
        pass

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


@io_manager(
    {
        "log_sql": Field(bool, default_value=False, is_required=False, description="Verbose logging of all executed SQL statements"),
    }
)
def inmemory_datawarehouse_io_manager(init_context):
    base_dir = Path(__file__).parent.parent.parent
    datawarehouse_resource = SQLiteDatawarehouseResource(
        log_manager=init_context.log_manager,
        echo_sql=init_context.resource_config["log_sql"],
        schemas=[
            SQLiteSchema(
                'acme_lake', f'file:acme_lake?mode=memory',
                init_sql_file=str((base_dir / "consumption_datamart_tests/test_data/acme_lake.sqlite3.sql").resolve())
            ),
            SQLiteSchema(
                'consumption_datamart', f'file:consumption_datamart?mode=memory',
                init_sql_file=str((base_dir / "schema/consumption_datamart.sqlite3.sql").resolve())
            ),
        ]
    )
    return DataWarehouseIOManager(datawarehouse_resource=datawarehouse_resource)
