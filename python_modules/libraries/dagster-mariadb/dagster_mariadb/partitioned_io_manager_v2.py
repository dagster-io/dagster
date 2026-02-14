"""
Enhanced Partitioned I/O Manager with full Dagster support AND native MariaDB partitioning.
"""

from typing import Any, Dict, Optional, Sequence
import pandas as pd

from dagster import (
    ConfigurableIOManager,
    InputContext,
    OutputContext,
    MetadataValue,
    TableColumn,
    TableSchema,
    DailyPartitionsDefinition,
    MonthlyPartitionsDefinition,
    WeeklyPartitionsDefinition,
    HourlyPartitionsDefinition,
    StaticPartitionsDefinition,
    DynamicPartitionsDefinition,
    MultiPartitionsDefinition,
    TimeWindowPartitionsDefinition,
)
from dagster._core.definitions.metadata import TableMetadataSet
from pydantic import Field
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from dagster_mariadb.resource import MariaDBResource
from dagster_mariadb.partitions import (
    PartitionStrategy,
    PartitionType,
    create_partitioned_table,
    get_partition_info,
    truncate_partition,
    add_partition,
)


class MariaDBPartitionedPandasIOManager(ConfigurableIOManager):
    """Enhanced I/O Manager with full Dagster partition support AND native MariaDB partitioning.
    
    Combines the best of both approaches:
    - Native MariaDB partitioning for performance (when supported)
    - Full support for all Dagster partition types
    - Multi-dimensional partition support
    - Flexible per-asset configuration
    
    Features:
    - Time-based partitions (Daily, Weekly, Monthly, Hourly, TimeWindow)
    - Static partitions
    - Dynamic partitions
    - Multi-dimensional partitions
    - Native MariaDB RANGE/LIST/HASH partitioning (when enabled)
    - Partition pruning for efficient queries
    """

    mariadb: MariaDBResource = Field(
        description="The MariaDB resource for database connections."
    )
    
    schema_name: Optional[str] = Field(
        description="The database schema to use for storing tables.",
        default=None,
    )
    
    mode: str = Field(
        description="The write mode: 'replace', 'append' or 'fail'.",
        default="replace",
    )
    
    use_native_partitioning: bool = Field(
        description="Use native MariaDB partitioning when supported. Provides better performance.",
        default=True,
    )
    
    storage_engine: str = Field(
        description="MariaDB storage engine to use for partitioned tables.",
        default="InnoDB",
    )
    
    default_partition_column: str = Field(
        description="Default partition column name (can be overridden per-asset via metadata).",
        default="partition_date",
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

    def _can_use_native_partitioning(
        self, 
        partitions_def,
        is_multi_dim: bool
    ) -> bool:
        """Determine if native MariaDB partitioning can be used."""
        if not self.use_native_partitioning:
            return False
        
        # Multi-dimensional partitions not supported by native MariaDB partitioning
        if is_multi_dim:
            return False
        
        # Dynamic partitions are too flexible for native partitioning
        if isinstance(partitions_def, DynamicPartitionsDefinition):
            return False
        
        # Supported: Daily, Monthly, Weekly, Hourly, TimeWindow, Static
        return isinstance(partitions_def, (
            DailyPartitionsDefinition,
            MonthlyPartitionsDefinition,
            WeeklyPartitionsDefinition,
            HourlyPartitionsDefinition,
            TimeWindowPartitionsDefinition,
            StaticPartitionsDefinition,
        ))

    def _get_partition_columns_and_values(
        self, 
        context: OutputContext
    ) -> Dict[str, Any]:
        """Extract partition columns and values from context.
        
        Handles:
        - Single dimension partitions
        - Multi-dimensional partitions
        - Time-based partitions
        - Static partitions
        """
        if not context.has_partition_key:
            return {}
        
        partition_key = context.partition_key
        partitions_def = context.asset_partitions_def
        
        # Handle multi-dimensional partitions
        if isinstance(partitions_def, MultiPartitionsDefinition):
            result = {}
            
            try:
                from dagster import MultiPartitionKey
                if isinstance(partition_key, MultiPartitionKey):
                    dimension_names = [dim.name for dim in partitions_def.partitions_defs]
                    for dim_name in dimension_names:
                        value = partition_key.keys_by_dimension[dim_name]
                        # Check for dimension-specific column name in metadata
                        column_name = (
                            context.metadata.get(f"{dim_name}_column") 
                            if context.metadata 
                            else None
                        ) or f"partition_{dim_name}"
                        result[column_name] = value
                    return result
            except Exception:
                pass
            
            # Fallback: split by separator (usually |)
            dimension_names = [dim.name for dim in partitions_def.partitions_defs]
            parts = str(partition_key).split("|")
            for i, dim_name in enumerate(dimension_names):
                if i < len(parts):
                    column_name = (
                        context.metadata.get(f"{dim_name}_column") 
                        if context.metadata 
                        else None
                    ) or f"partition_{dim_name}"
                    result[column_name] = parts[i]
            
            return result
        
        # Handle single dimension partitions
        partition_column = self._get_partition_column_name(context, partitions_def)
        
        # For time-based partitions, store the partition key directly
        return {partition_column: partition_key}

    def _get_partition_column_name(
        self, 
        context: OutputContext, 
        partitions_def
    ) -> str:
        """Determine the partition column name based on partition type."""
        # Check metadata first
        if context.metadata and "partition_column" in context.metadata:
            return context.metadata["partition_column"]
        
        # Infer from partition type
        if isinstance(partitions_def, (
            DailyPartitionsDefinition,
            WeeklyPartitionsDefinition,
            MonthlyPartitionsDefinition,
            HourlyPartitionsDefinition,
            TimeWindowPartitionsDefinition
        )):
            return "partition_date"
        
        # Default
        return self.default_partition_column

    def _build_partition_where_clause(
        self, 
        partition_columns_values: Dict[str, Any]
    ) -> str:
        """Build WHERE clause for partition filtering."""
        if not partition_columns_values:
            return ""
        
        clauses = []
        for column, value in partition_columns_values.items():
            clauses.append(f"`{column}` = '{value}'")
        
        return " AND ".join(clauses)

    def _ensure_table_exists(
        self,
        connection,
        context: OutputContext,
        df: pd.DataFrame,
        use_native_partitioning: bool
    ) -> None:
        """Ensure the table exists, optionally with native partitioning."""
        table_name = self._get_table_name(context)
        
        # Check if table exists
        check_query = f"""
            SELECT COUNT(*) FROM information_schema.TABLES 
            WHERE TABLE_NAME = '{table_name}'
            {f"AND TABLE_SCHEMA = '{self.schema_name}'" if self.schema_name else ""}
        """
        result = connection.execute(text(check_query))
        exists = result.scalar() > 0
        
        if exists:
            return  # Table already exists
        
        # Create table
        if use_native_partitioning:
            self._create_natively_partitioned_table(connection, context, df)
        else:
            self._create_regular_table(connection, context, df)

    def _create_natively_partitioned_table(
            self,
            connection,
            context: OutputContext,
            df: pd.DataFrame
        ) -> None:
            """Create a natively partitioned table in MariaDB."""
            table_name = self._get_table_name(context)
            partitions_def = context.asset_partitions_def
            
            # Get partition column name
            partition_column = self._get_partition_column_name(context, partitions_def)
            
            # Infer columns from DataFrame
            columns = {}
            for col in df.columns:
                if col == partition_column:
                    # Force correct type for partition column based on partition definition
                    if isinstance(partitions_def, (
                        DailyPartitionsDefinition,
                        WeeklyPartitionsDefinition,
                        MonthlyPartitionsDefinition,
                    )):
                        columns[col] = "DATE"
                    elif isinstance(partitions_def, HourlyPartitionsDefinition):
                        columns[col] = "DATETIME"
                    else:
                        columns[col] = "VARCHAR(255)"
                else:
                    columns[col] = self._infer_sql_type(df[col].dtype)
            
            # Ensure partition column exists (in case it wasn't in the DataFrame)
            if partition_column not in columns:
                # Infer type based on partition definition
                if isinstance(partitions_def, (
                    DailyPartitionsDefinition,
                    WeeklyPartitionsDefinition,
                    MonthlyPartitionsDefinition,
                )):
                    columns[partition_column] = "DATE"
                elif isinstance(partitions_def, HourlyPartitionsDefinition):
                    columns[partition_column] = "DATETIME"
                else:
                    columns[partition_column] = "VARCHAR(255)"
            
            # Build partition config
            partition_config = self._build_native_partition_config(context, partitions_def, partition_column)
            
            # Create the partitioned table
            create_partitioned_table(
                table_name=table_name,
                schema_name=self.schema_name,
                columns=columns,
                partition_config=partition_config,
                connection=connection,
                storage_engine=self.storage_engine,
            )
            context.log.info("Created natively partitioned table {}".format(self._get_full_table_name(context)))

    def _build_native_partition_config(
        self,
        context: OutputContext,
        partitions_def,
        partition_column: str
    ) -> Dict[str, Any]:
        """Build partition configuration for native MariaDB partitioning."""
        
        if isinstance(partitions_def, DailyPartitionsDefinition):
            return PartitionStrategy.daily_to_range(
                partition_column=partition_column,
                start_date=partitions_def.start,
                end_date=partitions_def.end if hasattr(partitions_def, 'end') and partitions_def.end else "2099-12-31",
            )
        
        elif isinstance(partitions_def, (WeeklyPartitionsDefinition, MonthlyPartitionsDefinition)):
            # Treat weekly as daily for native partitioning (more granular)
            return PartitionStrategy.monthly_to_range(
                partition_column=partition_column,
                start_date=partitions_def.start,
                end_date=partitions_def.end if hasattr(partitions_def, 'end') and partitions_def.end else "2099-12-31",
            ) if isinstance(partitions_def, MonthlyPartitionsDefinition) else PartitionStrategy.daily_to_range(
                partition_column=partition_column,
                start_date=partitions_def.start,
                end_date=partitions_def.end if hasattr(partitions_def, 'end') and partitions_def.end else "2099-12-31",
            )
        
        elif isinstance(partitions_def, HourlyPartitionsDefinition):
            # For hourly, use daily partitioning (hourly is too granular)
            return PartitionStrategy.daily_to_range(
                partition_column=partition_column,
                start_date=partitions_def.start,
                end_date=partitions_def.end if hasattr(partitions_def, 'end') and partitions_def.end else "2099-12-31",
            )
        
        elif isinstance(partitions_def, StaticPartitionsDefinition):
            partition_keys = partitions_def.get_partition_keys()
            partition_values = {key: [key] for key in partition_keys}
            return PartitionStrategy.list_partitions(
                partition_column=partition_column,
                partition_values=partition_values
            )
        
        else:
            # Default to hash partitioning
            return PartitionStrategy.hash_partitions(
                partition_column=partition_column,
                num_partitions=10
            )

    def _create_regular_table(
        self,
        connection,
        context: OutputContext,
        df: pd.DataFrame
    ) -> None:
        """Create a regular (non-partitioned) table."""
        table_name = self._get_table_name(context)
        
        # Let pandas create the table
        df.head(0).to_sql(
            name=table_name,
            con=connection,
            schema=self.schema_name,
            if_exists="fail",
            index=False,
        )
        connection.commit()
        context.log.info(f"Created regular table {self._get_full_table_name(context)}")

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

    def _get_partition_name_from_key(self, partition_key: str) -> str:
        """Convert partition key to MariaDB partition name."""
        # Remove special characters that aren't allowed in partition names
        clean_key = partition_key.replace('-', '').replace('_', '').replace(':', '').replace(' ', '')
        return f"p{clean_key}"

    def handle_output(self, context: OutputContext, obj: pd.DataFrame) -> None:
        """Handle output by writing DataFrame to MariaDB with optimal partitioning."""
        with self.mariadb.get_connection() as connection:
            self._ensure_schema_exists(connection, context)
            
            # Determine partitioning strategy
            is_partitioned = context.has_partition_key
            partitions_def = context.asset_partitions_def if is_partitioned else None
            is_multi_dim = isinstance(partitions_def, MultiPartitionsDefinition) if partitions_def else False
            
            use_native = (
                is_partitioned 
                and self._can_use_native_partitioning(partitions_def, is_multi_dim)
            )
            
            # Handle partitioned assets
            if is_partitioned:
                # Get partition columns and values
                partition_data = self._get_partition_columns_and_values(context)
                
                # Add partition columns to dataframe if not present
                df_to_write = obj.copy()
                for column, value in partition_data.items():
                    if column not in df_to_write.columns:
                        df_to_write[column] = value
                
                # Ensure table exists
                self._ensure_table_exists(connection, context, df_to_write, use_native)
                
                # Handle replace mode
                if self.mode == "replace":
                    if use_native:
                        # Use native partition truncation
                        partition_name = self._get_partition_name_from_key(context.partition_key)
                        
                        # Check if partition exists
                        partition_info = get_partition_info(
                            table_name=self._get_table_name(context),
                            schema_name=self.schema_name,
                            connection=connection
                        )
                        
                        partition_exists = any(p['name'] == partition_name for p in partition_info)
                        
                        if partition_exists:
                            truncate_partition(
                                table_name=self._get_table_name(context),
                                schema_name=self.schema_name,
                                partition_name=partition_name,
                                connection=connection
                            )
                            context.log.debug(f"Truncated native partition {partition_name}")
                    else:
                        # Use WHERE clause deletion
                        where_clause = self._build_partition_where_clause(partition_data)
                        if where_clause:
                            table_name = self._get_full_table_name(context)
                            try:
                                delete_query = f"DELETE FROM {table_name} WHERE {where_clause}"
                                context.log.debug(f"Deleting partition data: {delete_query}")
                                connection.execute(text(delete_query))
                                connection.commit()
                            except SQLAlchemyError:
                                # Table might not exist yet
                                pass
                
                # Write the data
                self._write_dataframe(df_to_write, connection, context)
                
                # Add metadata
                metadata = {
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
                    "partition_key": str(context.partition_key),
                    "native_partitioning": use_native,
                }
                
                context.add_output_metadata(metadata)
            else:
                # Non-partitioned asset
                self._ensure_table_exists(connection, context, obj, False)
                self._write_dataframe(obj, connection, context)
                
                context.add_output_metadata({
                    **TableMetadataSet(row_count=obj.shape[0]),
                    "dataframe_columns": MetadataValue.table_schema(
                        TableSchema(
                            columns=[
                                TableColumn(name=str(name), type=str(dtype))
                                for name, dtype in obj.dtypes.items()
                            ]
                        )
                    ),
                    "table_name": self._get_full_table_name(context),
                })

    def _write_dataframe(self, df: pd.DataFrame, connection, context: OutputContext) -> None:
        """Write DataFrame to MariaDB table."""
        table_name = self._get_table_name(context)
        
        try:
            if self.mode == "replace" and not context.has_partition_key:
                # Only drop table for non-partitioned replace mode
                full_table = self._get_full_table_name(context)
                connection.execute(text(f"DROP TABLE IF EXISTS {full_table}"))
                connection.commit()
                
                df.to_sql(
                    name=table_name,
                    con=connection,
                    schema=self.schema_name,
                    if_exists="replace",
                    index=False,
                    method="multi",
                )
            elif self.mode == "append" or context.has_partition_key:
                df.to_sql(
                    name=table_name,
                    con=connection,
                    schema=self.schema_name,
                    if_exists="append",
                    index=False,
                    method="multi",
                )
            elif self.mode == "fail":
                df.to_sql(
                    name=table_name,
                    con=connection,
                    schema=self.schema_name,
                    if_exists="fail",
                    index=False,
                    method="multi",
                )
            else:
                raise ValueError(f"Invalid mode: {self.mode}")
                
            connection.commit()
            
        except SQLAlchemyError as e:
            connection.rollback()
            raise e

    def load_input(self, context: InputContext) -> pd.DataFrame:
            """Load input by reading DataFrame from MariaDB with partition support."""
            table_name = context.asset_key.path[-1] if context.asset_key else "unknown"
            full_table_name = "`{}`.`{}`".format(self.schema_name, table_name) if self.schema_name else "`{}`".format(table_name)
            
            # Build base query
            query = "SELECT * FROM {}".format(full_table_name)
            
            # Build WHERE clauses
            where_clauses = []
            
            # Handle partitioned loading
            if context.has_partition_key:
                partition_key = context.partition_key
                upstream_output = context.upstream_output
                
                if upstream_output and hasattr(upstream_output, 'asset_partitions_def'):
                    partitions_def = upstream_output.asset_partitions_def
                elif hasattr(context, 'asset_partitions_def'):
                    partitions_def = context.asset_partitions_def
                else:
                    partitions_def = None
                
                # Try to get partition column from upstream asset metadata first
                partition_column = None
                if upstream_output and hasattr(upstream_output, 'metadata') and upstream_output.metadata:
                    partition_column = upstream_output.metadata.get("partition_column")
                
                # Fallback to context metadata
                if not partition_column and context.metadata:
                    partition_column = context.metadata.get("partition_column")
                
                # Get partition columns and build filter
                if partitions_def and isinstance(partitions_def, MultiPartitionsDefinition):
                    # Multi-dimensional partitions
                    try:
                        from dagster import MultiPartitionKey
                        if isinstance(partition_key, MultiPartitionKey):
                            dimension_names = [dim.name for dim in partitions_def.partitions_defs]
                            for dim_name in dimension_names:
                                dim_key = partition_key.keys_by_dimension[dim_name]
                                column_name = (
                                    context.metadata.get("{}_column".format(dim_name)) 
                                    if context.metadata 
                                    else None
                                ) or "partition_{}".format(dim_name)
                                where_clauses.append("`{}` = '{}'".format(column_name, dim_key))
                    except Exception:
                        # Fallback parsing
                        dimension_names = [dim.name for dim in partitions_def.partitions_defs]
                        parts = str(partition_key).split("|")
                        for i, dim_name in enumerate(dimension_names):
                            if i < len(parts):
                                column_name = (
                                    context.metadata.get("{}_column".format(dim_name)) 
                                    if context.metadata 
                                    else None
                                ) or "partition_{}".format(dim_name)
                                where_clauses.append("`{}` = '{}'".format(column_name, parts[i]))
                else:
                    # Single dimension partition
                    if not partition_column:
                        # Infer from partition type if not specified
                        if partitions_def and isinstance(partitions_def, (
                            DailyPartitionsDefinition,
                            WeeklyPartitionsDefinition,
                            MonthlyPartitionsDefinition,
                            HourlyPartitionsDefinition,
                            TimeWindowPartitionsDefinition
                        )):
                            partition_column = "partition_date"
                        else:
                            partition_column = self.default_partition_column
                    
                    where_clauses.append("`{}` = '{}'".format(partition_column, partition_key))
            
            # Add column selection if specified
            if context.metadata and "columns" in context.metadata:
                columns = context.metadata["columns"]
                if isinstance(columns, list):
                    column_list = ", ".join(["`{}`".format(col) for col in columns])
                    query = "SELECT {} FROM {}".format(column_list, full_table_name)
            
            # Add WHERE clause
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            
            context.log.debug("Loading data with query: {}".format(query))
            
            with self.mariadb.get_connection() as connection:
                try:
                    df = pd.read_sql(query, connection)
                    context.log.info("Loaded {} rows from {}".format(len(df), full_table_name))
                    return df
                except SQLAlchemyError as e:
                    context.log.error("Failed to load data from {}: {}".format(full_table_name, e))
                    raise e