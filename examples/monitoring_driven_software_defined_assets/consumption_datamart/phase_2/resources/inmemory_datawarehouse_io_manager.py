from pathlib import Path

from consumption_datamart.common.resources.datawarehouse.sqlite import SQLiteDatawarehouseResource, SQLiteSchema
from consumption_datamart.common.resources.datawarehouse_io_manager import DataWarehouseIOManager
from dagster import Field
from dagster import io_manager


@io_manager(
    {
        "log_sql": Field(bool, default_value=False, is_required=False, description="Verbose logging of all executed SQL statements"),
    }
)
def inmemory_datawarehouse_io_manager(init_context):
    base_dir = Path(__file__).parent.parent.parent.parent
    datawarehouse_resource = SQLiteDatawarehouseResource(
        log_manager=init_context.log_manager,
        echo_sql=init_context.resource_config["log_sql"],
        schemas=[
            SQLiteSchema(
                'consumption_datamart', f'file:consumption_datamart?mode=memory',
                init_sql_file=str((base_dir / "consumption_datamart_tests/phase_1/phase_1/consumption_datamart.sqlite3.sql").resolve())
            ),
        ]
    )
    return DataWarehouseIOManager(datawarehouse_resource=datawarehouse_resource)
