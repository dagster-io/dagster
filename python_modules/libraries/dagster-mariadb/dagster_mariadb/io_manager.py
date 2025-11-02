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
from dagster_mariadb.resource import MariaDBResource


class MariaDBPandasIOManager(ConfigurableIOManager):
    """I/O Manager for storing Pandas DataFrames in MariaDB."""

    mariadb: MariaDBResource = Field(
        description="The MariaDB resource for database connections."
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
            return f"`{self.schema}`.`{table_name}`"
        return f"`{table_name}`"

    def _ensure_schema_exists(self, connection, context: OutputContext) -> None:
        """Ensure the schema exists in the database."""
        if self.schema:
            try:
                connection.execute(text(f"CREATE DATABASE IF NOT EXISTS `{self.schema}`"))
                connection.commit()
            except SQLAlchemyError as e:
                context.log.warning(f"Could not create schema {self.schema}: {e}")

    def _write_dataframe(self, df: pd.DataFrame, connection, context: OutputContext) -> None:
        """Write DataFrame to MariaDB table."""
        table_name = self._get_table_name(context)
        
        try:
            if self.mode == "replace":
                full_table = self._get_full_table_name(context)
                connection.execute(text(f"DROP TABLE IF EXISTS {full_table}"))
                connection.commit()
                
                df.to_sql(
                    name=table_name,
                    con=connection,
                    schema=self.schema,
                    if_exists="replace",
                    index=False,
                    method="multi",
                )
                
            elif self.mode == "append":
                df.to_sql(
                    name=table_name,
                    con=connection,
                    schema=self.schema,
                    if_exists="append",
                    index=False,
                    method="multi",
                )
                
            elif self.mode == "fail":
                df.to_sql(
                    name=table_name,
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
        with self.mariadb.get_connection() as connection:
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
        table_name = context.asset_key.path[-1] if context.asset_key else "unknown"
        full_table_name = f"`{self.schema}`.`{table_name}`" if self.schema else f"`{table_name}`"
        
        query = f"SELECT * FROM {full_table_name}"
        
        if context.metadata and "columns" in context.metadata:
            columns = context.metadata["columns"]
            if isinstance(columns, list):
                column_list = ", ".join([f"`{col}`" for col in columns])
                query = f"SELECT {column_list} FROM {full_table_name}"
        
        with self.mariadb.get_connection() as connection:
            try:
                df = pd.read_sql(query, connection)
                return df
            except SQLAlchemyError as e:
                context.log.error(f"Failed to load data from {full_table_name}: {e}")
                raise e