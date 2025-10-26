from collections.abc import Sequence
from contextlib import contextmanager
from typing import Any, Optional

import pandas as pd
from dagster import (
    ConfigurableIOManager,
    IOManagerDefinition,
    InputContext,
    OutputContext,
    MetadataValue,
    TableColumn,
    TableSchema,
    io_manager,
)
from dagster._core.definitions.metadata import TableMetadataSet
from dagster._core.storage.io_manager import dagster_maintained_io_manager
from pydantic import Field
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError


class MariaDBPandasIOManager(ConfigurableIOManager):
    """I/O Manager for storing Pandas DataFrames in MariaDB."""

    engine_resource_key: str = Field(
        description="The resource key for the MariaDBResource that provides the database connection."
    )
    
    schema: Optional[str] = Field(
        description="The database schema to use for storing tables.",
        default=None,
    )
    
    mode: str = Field(
        description="The write mode: 'replace', 'append' or 'fail'.",
        default="replace",
    )

    @classmethod
    def _is_dagster_maintained(cls):
        return True

    def _get_table_name(self, context: OutputContext) -> str:
        """Get the table name from the asset key."""
        return context.asset_key.path[-1]

    def _get_full_table_name(self, context: OutputContext) -> str:
        """Get the fully qualified table name."""
        table_name = self._get_table_name(context)
        if self.schema:
            return f"{self.schema}.{table_name}"
        return table_name

    def _ensure_schema_exists(self, connection, context: OutputContext) -> None:
        """Ensure the schema exists in the database."""
        if self.schema:
            try:
                connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {self.schema}"))
                connection.commit()
            except SQLAlchemyError as e:
                context.log.warning(f"Could not create schema {self.schema}: {e}")

    def _write_dataframe(self, df: pd.DataFrame, connection, context: OutputContext) -> None:
        """Write DataFrame to MariaDB table."""
        table_name = self._get_full_table_name(context)
        
        try:
            if self.mode == "replace":
                connection.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                connection.commit()
                
                df.to_sql(
                    name=self._get_table_name(context),
                    con=connection,
                    schema=self.schema,
                    if_exists="replace",
                    index=False,
                    method="multi",
                )
                
            elif self.mode == "append":
                df.to_sql(
                    name=self._get_table_name(context),
                    con=connection,
                    schema=self.schema,
                    if_exists="append",
                    index=False,
                    method="multi",
                )
                
            elif self.mode == "fail":
                df.to_sql(
                    name=self._get_table_name(context),
                    con=connection,
                    schema=self.schema,
                    if_exists="fail",
                    index=False,
                    method="multi",
                )
            else:
                raise ValueError(f"Invalid mode: {self.mode}. Must be 'replace', 'append' or 'fail'.")
                
            connection.commit()
            
        except SQLAlchemyError as e:
            connection.rollback()
            raise e

    def handle_output(self, context: OutputContext, obj: pd.DataFrame) -> None:
        """Handle output by writing DataFrame to MariaDB."""
        mariadb_resource = context.resources[self.engine_resource_key]
        
        with mariadb_resource.get_connection() as connection:
            self._ensure_schema_exists(connection, context)
            self._write_dataframe(obj, connection, context)
            
            context.add_output_metadata(
                {
                    **(
                        TableMetadataSet(partition_row_count=obj.shape[0])
                        if context.has_partition_key
                        else TableMetadataSet(row_count=obj.shape[0])
                    ),
                    "dataframe_columns": MetadataValue.table_schema(
                        TableSchema(
                            columns=[
                                TableColumn(name=name, type=str(dtype))
                                for name, dtype in obj.dtypes.items()
                            ]
                        )
                    ),
                    "table_name": self._get_full_table_name(context),
                }
            )

    def load_input(self, context: InputContext) -> pd.DataFrame:
        """Load input by reading DataFrame from MariaDB."""
        mariadb_resource = context.resources[self.engine_resource_key]

        table_name = context.asset_key.path[-1] if context.asset_key else "unknown"
        full_table_name = f"{self.schema}.{table_name}" if self.schema else table_name
        
        query = f"SELECT * FROM {full_table_name}"
        
        if context.metadata and "columns" in context.metadata:
            columns = context.metadata["columns"]
            if isinstance(columns, list):
                column_list = ", ".join(columns)
                query = f"SELECT {column_list} FROM {full_table_name}"
        
        with mariadb_resource.get_connection() as connection:
            try:
                df = pd.read_sql(query, connection)
                return df
            except SQLAlchemyError as e:
                context.log.error(f"Failed to load data from {full_table_name}: {e}")
                raise e


@dagster_maintained_io_manager
@io_manager(config_schema=MariaDBPandasIOManager.to_config_schema())
def mariadb_pandas_io_manager(init_context):
    """I/O Manager for storing Pandas DataFrames in MariaDB."""
    return MariaDBPandasIOManager(
        engine_resource_key=init_context.resource_config["engine_resource_key"],
        schema=init_context.resource_config.get("schema"),
        mode=init_context.resource_config.get("mode", "replace"),
    )
