from pathlib import Path

from consumption_datamart.common.resources.datawarehouse.sqlite import SQLiteDatawarehouseResource, SQLiteSchema
from consumption_datamart.common.resources.datawarehouse_io_manager import DataWarehouseIOManager
from dagster import Field, StringSource
from dagster import io_manager


@io_manager(
    {
        "base_path": Field(StringSource),
        "log_sql": Field(bool, default_value=False, is_required=False, description="Verbose logging of all executed SQL statements"),
    }
)
def fs_datawarehouse_io_manager(init_context):
    base_path = Path(init_context.resource_config["base_path"])
    datawarehouse_resource = SQLiteDatawarehouseResource(
        log_manager=init_context.log_manager,
        echo_sql=init_context.resource_config["log_sql"],
        schemas=[
            SQLiteSchema('consumption_datamart', f'file:{(base_path / "consumption_datamart.db").resolve()}'),
        ]
    )
    return DataWarehouseIOManager(datawarehouse_resource=datawarehouse_resource)
