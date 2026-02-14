"""
Partitioned I/O Manager for MariaDB with native partition support.
"""

from typing import Any, Dict, Optional
import pandas as pd

from dagster import (
    ConfigurableIOManager,
    InputContext,
    OutputContext,
    MetadataValue,
    TableColumn,
    TableSchema,
)
from dagster._core.definitions.metadata import TableMetadataSet
from pydantic import Field
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from dagster_mariadb.resource import MariaDBResource
from dagster_mariadb.partitions import (
    PartitionStrategy,
    create_partitioned_table,
    get_partition_info,
    truncate_partition,
    add_partition,
)


class MariaDBPartitionedIOManager(ConfigurableIOManager):
    """I/O Manager for storing partitioned Pandas DataFrames in MariaDB with native partitioning.
    
    This I/O manager creates and manages natively partitioned tables in MariaDB,
    providing better query performance and easier partition management.
    """

    mariadb: MariaDBResource = Field(
        description="The MariaDB resource for database connections."
    )
    
    schema_name: Optional[str] = Field(
        description="The database schema to use for storing tables.",
        default=None,
    )
    
    partition_column: str = Field(
        description="Column name to use for partitioning.",
        default="partition_date",
    )
    
    partition_type: str = Field(
        description="Type of partitioning: 'range', 'list', 'hash'.",
        default="range",
    )
    
    storage_engine: str = Field(
        description="MariaDB storage engine to use.",
        default="InnoDB",
    )
    
    auto_create_partitions: bool = Field(
        description="Automatically create partitions if they don't exist.",
        default=True,
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
        if self.schema_name:
            return f"`{self.schema_name}`.`{table_name}`"
        return f"`{table_name}`"

    def _ensure_schema_exists(self, connection, context: OutputContext) -> None:
        """Ensure the schema exists in the database."""
        if self.schema_name:
            try:
                connection.execute(text(f"CREATE DATABASE IF NOT EXISTS `{self.schema_name}`"))
                connection.commit()
            except SQLAlchemyError as e:
                context.log.warning(f"Could not create schema {self.schema_name}: {e}")

    def _ensure_partitioned_table_exists(
        self,
        connection,
        context: OutputContext,
        df: pd.DataFrame
    ) -> None:
        """Ensure the partitioned table exists with proper schema."""
        table_name = self._get_table_name(context)
        
        # Check if table exists
        check_query = f"""
            SELECT COUNT(*) FROM information_schema.TABLES 
            WHERE TABLE_NAME = '{table_name}'
            {f"AND TABLE_SCHEMA = '{self.schema_name}'" if self.schema_name else ""}
        """
        result = connection.execute(text(check_query))
        exists = result.scalar() > 0
        
        if not exists:
            # Create table with partitioning
            columns = {col: self._infer_sql_type(df[col].dtype) for col in df.columns}
            
            # Ensure partition column exists
            if self.partition_column not in columns:
                columns[self.partition_column] = "VARCHAR(255)"
            
            # Build partition config based on Dagster partition definition
            partition_config = self._build_partition_config(context)
            
            create_partitioned_table(
                table_name=table_name,
                schema_name=self.schema_name,
                columns=columns,
                partition_config=partition_config,
                connection=connection,
                storage_engine=self.storage_engine,
            )
            context.log.info(f"Created partitioned table {self._get_full_table_name(context)}")

    def _build_partition_config(self, context: OutputContext) -> Dict[str, Any]:
        """Build partition configuration from Dagster partition definition."""
        if not hasattr(context, 'asset_partitions_def') or context.asset_partitions_def is None:
            # Default to hash partitioning if no partition definition
            return PartitionStrategy.hash_partitions(
                partition_column=self.partition_column,
                num_partitions=10
            )
        
        from dagster import DailyPartitionsDefinition, MonthlyPartitionsDefinition, StaticPartitionsDefinition
        
        partitions_def = context.asset_partitions_def
        
        if isinstance(partitions_def, DailyPartitionsDefinition):
            return PartitionStrategy.daily_to_range(
                partition_column=self.partition_column,
                start_date=partitions_def.start,
                end_date=partitions_def.end if hasattr(partitions_def, 'end') and partitions_def.end else "2099-12-31",
            )
        elif isinstance(partitions_def, MonthlyPartitionsDefinition):
            return PartitionStrategy.monthly_to_range(
                partition_column=self.partition_column,
                start_date=partitions_def.start,
                end_date=partitions_def.end if hasattr(partitions_def, 'end') and partitions_def.end else "2099-12-31",
            )
        elif isinstance(partitions_def, StaticPartitionsDefinition):
            # Use LIST partitioning for static partitions
            partition_keys = partitions_def.get_partition_keys()
            partition_values = {key: [key] for key in partition_keys}
            return PartitionStrategy.list_partitions(
                partition_column=self.partition_column,
                partition_values=partition_values
            )
        else:
            # Default to hash partitioning
            return PartitionStrategy.hash_partitions(
                partition_column=self.partition_column,
                num_partitions=10
            )

    def _infer_sql_type(self, dtype) -> str:
        """Infer SQL type from pandas dtype."""
        dtype_str = str(dtype)
        if 'int' in dtype_str:
            return 'BIGINT'
        elif 'float' in dtype_str:
            return 'DOUBLE'
        elif 'bool' in dtype_str:
            return 'BOOLEAN'
        elif 'datetime' in dtype_str:
            return 'DATETIME'
        elif 'date' in dtype_str:
            return 'DATE'
        else:
            return 'VARCHAR(255)'

    def handle_output(self, context: OutputContext, obj: pd.DataFrame) -> None:
        """Handle output by writing DataFrame to partitioned MariaDB table."""
        if not context.has_partition_key:
            raise ValueError("MariaDBPartitionedIOManager requires partitioned assets")
        
        with self.mariadb.get_connection() as connection:
            self._ensure_schema_exists(connection, context)
            
            # Add partition column to dataframe
            if self.partition_column not in obj.columns:
                obj = obj.copy()
                obj[self.partition_column] = context.partition_key
            
            # Ensure partitioned table exists
            self._ensure_partitioned_table_exists(connection, context, obj)
            
            # Get partition info
            partition_info = get_partition_info(
                table_name=self._get_table_name(context),
                schema_name=self.schema_name,
                connection=connection
            )
            
            # Determine partition name from partition key
            partition_name = self._get_partition_name_from_key(context.partition_key)
            
            # Check if partition exists for this key
            partition_exists = any(p['name'] == partition_name for p in partition_info)
            
            if partition_exists:
                # Truncate partition before writing
                truncate_partition(
                    table_name=self._get_table_name(context),
                    schema_name=self.schema_name,
                    partition_name=partition_name,
                    connection=connection
                )
            
            # Write data to table (it will go to the appropriate partition)
            table_name = self._get_table_name(context)
            try:
                obj.to_sql(
                    name=table_name,
                    con=connection,
                    schema=self.schema_name,
                    if_exists="append",
                    index=False,
                    method="multi",
                )
                connection.commit()
            except SQLAlchemyError as e:
                connection.rollback()
                raise e
            
            context.add_output_metadata(
                {
                    **TableMetadataSet(partition_row_count=obj.shape[0]),
                    "dataframe_columns": MetadataValue.table_schema(
                        TableSchema(
                            columns=[
                                TableColumn(name=str(name), type=str(dtype))
                                for name, dtype in obj.dtypes.items()
                            ]
                        )
                    ),
                    "table_name": self._get_full_table_name(context),
                    "partition_name": partition_name,
                }
            )

    def load_input(self, context: InputContext) -> pd.DataFrame:
        """Load input by reading DataFrame from partitioned MariaDB table."""
        if not context.has_partition_key:
            raise ValueError("MariaDBPartitionedIOManager requires partitioned assets")
        
        table_name = context.asset_key.path[-1] if context.asset_key else "unknown"
        full_table_name = f"`{self.schema_name}`.`{table_name}`" if self.schema_name else f"`{table_name}`"
        
        # Build query with partition filter
        query = f"SELECT * FROM {full_table_name} WHERE `{self.partition_column}` = :partition_key"
        
        with self.mariadb.get_connection() as connection:
            try:
                df = pd.read_sql(
                    query,
                    connection,
                    params={"partition_key": context.partition_key}
                )
                return df
            except SQLAlchemyError as e:
                context.log.error(f"Failed to load data from {full_table_name}: {e}")
                raise e

    def _get_partition_name_from_key(self, partition_key: str) -> str:
        """Convert partition key to MariaDB partition name."""
        # Remove special characters that aren't allowed in partition names
        return f"p{partition_key.replace('-', '').replace('_', '').replace(':', '')}"