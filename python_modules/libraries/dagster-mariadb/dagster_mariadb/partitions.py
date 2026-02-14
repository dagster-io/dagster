"""
MariaDB Partitioning Support

This module provides utilities for creating and managing partitioned tables in MariaDB,
integrated with Dagster's partitioning features.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date

from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import SQLAlchemyError
from dagster import (
    DailyPartitionsDefinition,
    MonthlyPartitionsDefinition,
    WeeklyPartitionsDefinition,
    StaticPartitionsDefinition,
    PartitionsDefinition,
)


class PartitionType(str, Enum):
    """MariaDB partition types."""
    RANGE = "RANGE"
    LIST = "LIST"
    HASH = "HASH"
    KEY = "KEY"
    RANGE_COLUMNS = "RANGE COLUMNS"
    LIST_COLUMNS = "LIST COLUMNS"


class PartitionStrategy:
    """Strategies for mapping Dagster partitions to MariaDB partitions."""
    
    @staticmethod
    def daily_to_range(
        partition_column: str,
        start_date: Union[str, datetime, date],
        end_date: Union[str, datetime, date],
        date_format: str = "%Y-%m-%d"
    ) -> Dict[str, Any]:
        """Convert daily partitions to RANGE partitioning strategy.
        
        Args:
            partition_column: Column to partition on (should be DATE or DATETIME)
            start_date: Start date for partitions
            end_date: End date for partitions
            date_format: Date format string
            
        Returns:
            Dictionary with partition configuration
        """
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, date_format).date()
        elif isinstance(start_date, datetime):
            start_date = start_date.date()
            
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, date_format).date()
        elif isinstance(end_date, datetime):
            end_date = end_date.date()
        
        return {
            "type": PartitionType.RANGE,
            "column": partition_column,
            "start_date": start_date,
            "end_date": end_date,
            "granularity": "daily"
        }
    
    @staticmethod
    def monthly_to_range(
        partition_column: str,
        start_date: Union[str, datetime, date],
        end_date: Union[str, datetime, date],
        date_format: str = "%Y-%m-%d"
    ) -> Dict[str, Any]:
        """Convert monthly partitions to RANGE partitioning strategy."""
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, date_format).date()
        elif isinstance(start_date, datetime):
            start_date = start_date.date()
            
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, date_format).date()
        elif isinstance(end_date, datetime):
            end_date = end_date.date()
        
        return {
            "type": PartitionType.RANGE,
            "column": partition_column,
            "start_date": start_date,
            "end_date": end_date,
            "granularity": "monthly"
        }
    
    @staticmethod
    def hash_partitions(
        partition_column: str,
        num_partitions: int
    ) -> Dict[str, Any]:
        """Create HASH partitioning strategy.
        
        Args:
            partition_column: Column to hash
            num_partitions: Number of hash partitions
            
        Returns:
            Dictionary with partition configuration
        """
        return {
            "type": PartitionType.HASH,
            "column": partition_column,
            "num_partitions": num_partitions
        }
    
    @staticmethod
    def list_partitions(
        partition_column: str,
        partition_values: Dict[str, List[Any]]
    ) -> Dict[str, Any]:
        """Create LIST partitioning strategy.
        
        Args:
            partition_column: Column to partition on
            partition_values: Dict mapping partition names to lists of values
            
        Returns:
            Dictionary with partition configuration
        """
        return {
            "type": PartitionType.LIST,
            "column": partition_column,
            "partition_values": partition_values
        }


def create_partitioned_table(
    table_name: str,
    schema_name: Optional[str],
    columns: Dict[str, str],
    partition_config: Dict[str, Any],
    connection: Connection,
    storage_engine: str = "InnoDB",
    additional_options: Optional[str] = None
) -> None:
    """Create a partitioned table in MariaDB.
    
    Args:
        table_name: Name of the table
        schema_name: Schema name (optional)
        columns: Dictionary of column_name -> column_definition
        partition_config: Partition configuration from PartitionStrategy
        connection: Database connection
        storage_engine: Storage engine to use
        additional_options: Additional table options
        
    Examples:
        >>> partition_config = PartitionStrategy.daily_to_range(
        ...     "event_date", "2024-01-01", "2024-12-31"
        ... )
        >>> create_partitioned_table(
        ...     "events", "analytics", 
        ...     {"id": "INT", "event_date": "DATE", "data": "TEXT"},
        ...     partition_config, connection
        ... )
    """
    qualified_name = f"`{schema_name}`.`{table_name}`" if schema_name else f"`{table_name}`"
    column_defs = ", ".join([f"`{name}` {defn}" for name, defn in columns.items()])
    
    partition_clause = _build_partition_clause(partition_config)
    
    options = f"ENGINE={storage_engine}"
    if additional_options:
        options += f" {additional_options}"
    
    query = f"""
        CREATE TABLE IF NOT EXISTS {qualified_name} (
            {column_defs}
        ) {options}
        {partition_clause}
    """
    
    try:
        connection.execute(text(query))
        connection.commit()
    except SQLAlchemyError as e:
        connection.rollback()
        raise RuntimeError(f"Failed to create partitioned table {qualified_name}: {e}") from e


def _build_partition_clause(partition_config: Dict[str, Any]) -> str:
    """Build the PARTITION BY clause for table creation."""
    partition_type = partition_config["type"]
    
    if partition_type == PartitionType.RANGE:
        return _build_range_partition_clause(partition_config)
    elif partition_type == PartitionType.LIST:
        return _build_list_partition_clause(partition_config)
    elif partition_type == PartitionType.HASH:
        return _build_hash_partition_clause(partition_config)
    elif partition_type == PartitionType.KEY:
        return _build_key_partition_clause(partition_config)
    else:
        raise ValueError(f"Unsupported partition type: {partition_type}")


def _build_range_partition_clause(config: Dict[str, Any]) -> str:
    """Build RANGE partition clause."""
    column = config["column"]
    granularity = config.get("granularity", "daily")
    
    if granularity == "daily":
        return _build_daily_range_partitions(config)
    elif granularity == "monthly":
        return _build_monthly_range_partitions(config)
    else:
        # Custom range partitions
        if "ranges" in config:
            partitions = []
            for part_name, less_than_value in config["ranges"].items():
                partitions.append(f"PARTITION `{part_name}` VALUES LESS THAN ({less_than_value})")
            return f"PARTITION BY RANGE(`{column}`) (\n    " + ",\n    ".join(partitions) + "\n)"
        else:
            raise ValueError("For custom RANGE partitions, provide 'ranges' dictionary")


def _build_daily_range_partitions(config: Dict[str, Any]) -> str:
    """Build daily RANGE partitions."""
    column = config["column"]
    start_date = config["start_date"]
    end_date = config["end_date"]
    
    partitions = []
    current_date = start_date
    
    from datetime import timedelta
    while current_date <= end_date:
        next_date = current_date + timedelta(days=1)
        part_name = "p{}".format(current_date.strftime('%Y%m%d'))
        # Use TO_DAYS for DATE columns
        partitions.append(
            "PARTITION `{}` VALUES LESS THAN (TO_DAYS('{}'))".format(
                part_name, next_date
            )
        )
        current_date = next_date
    
    # Add MAXVALUE partition for future dates
    partitions.append("PARTITION `pmax` VALUES LESS THAN MAXVALUE")
    
    return "PARTITION BY RANGE(TO_DAYS(`{}`)) (\n    ".format(column) + ",\n    ".join(partitions) + "\n)"



def _build_monthly_range_partitions(config: Dict[str, Any]) -> str:
    """Build monthly RANGE partitions."""
    column = config["column"]
    start_date = config["start_date"]
    end_date = config["end_date"]
    
    partitions = []
    current_date = start_date.replace(day=1)
    
    from datetime import timedelta
    while current_date <= end_date:
        # Move to first day of next month
        if current_date.month == 12:
            next_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            next_date = current_date.replace(month=current_date.month + 1)
        
        part_name = "p{}".format(current_date.strftime('%Y%m'))
        partitions.append(
            "PARTITION `{}` VALUES LESS THAN (TO_DAYS('{}'))".format(
                part_name, next_date
            )
        )
        current_date = next_date
    
    # Add MAXVALUE partition
    partitions.append("PARTITION `pmax` VALUES LESS THAN MAXVALUE")
    
    return "PARTITION BY RANGE(TO_DAYS(`{}`)) (\n    ".format(column) + ",\n    ".join(partitions) + "\n)"


def _build_list_partition_clause(config: Dict[str, Any]) -> str:
    """Build LIST partition clause."""
    column = config["column"]
    partition_values = config["partition_values"]
    
    # Check if we need LIST COLUMNS (for non-integer values)
    # MariaDB LIST partitioning requires integer expressions
    # For string/varchar values, we need LIST COLUMNS
    needs_columns = False
    for values in partition_values.values():
        for v in values:
            if isinstance(v, str):
                needs_columns = True
                break
        if needs_columns:
            break
    
    partitions = []
    for part_name, values in partition_values.items():
        value_list = ", ".join(["'{}'".format(v) if isinstance(v, str) else str(v) for v in values])
        partitions.append("PARTITION `{}` VALUES IN ({})".format(part_name, value_list))
    
    if needs_columns:
        return "PARTITION BY LIST COLUMNS(`{}`) (\n    ".format(column) + ",\n    ".join(partitions) + "\n)"
    else:
        return "PARTITION BY LIST(`{}`) (\n    ".format(column) + ",\n    ".join(partitions) + "\n)"


def _build_hash_partition_clause(config: Dict[str, Any]) -> str:
    """Build HASH partition clause."""
    column = config["column"]
    num_partitions = config["num_partitions"]
    
    return f"PARTITION BY HASH(`{column}`) PARTITIONS {num_partitions}"


def _build_key_partition_clause(config: Dict[str, Any]) -> str:
    """Build KEY partition clause."""
    columns = config.get("columns", [config["column"]])
    num_partitions = config["num_partitions"]
    
    column_list = ", ".join([f"`{col}`" for col in columns])
    return f"PARTITION BY KEY({column_list}) PARTITIONS {num_partitions}"


def add_partition(
    table_name: str,
    schema_name: Optional[str],
    partition_name: str,
    partition_definition: str,
    connection: Connection
) -> None:
    """Add a new partition to an existing partitioned table.
    
    Args:
        table_name: Name of the table
        schema_name: Schema name (optional)
        partition_name: Name for the new partition
        partition_definition: Partition definition (e.g., "VALUES LESS THAN (100)")
        connection: Database connection
    """
    qualified_name = f"`{schema_name}`.`{table_name}`" if schema_name else f"`{table_name}`"
    
    query = f"ALTER TABLE {qualified_name} ADD PARTITION (PARTITION `{partition_name}` {partition_definition})"
    
    try:
        connection.execute(text(query))
        connection.commit()
    except SQLAlchemyError as e:
        connection.rollback()
        raise RuntimeError(f"Failed to add partition to {qualified_name}: {e}") from e


def drop_partition(
    table_name: str,
    schema_name: Optional[str],
    partition_name: str,
    connection: Connection
) -> None:
    """Drop a partition from a partitioned table.
    
    Args:
        table_name: Name of the table
        schema_name: Schema name (optional)
        partition_name: Name of the partition to drop
        connection: Database connection
    """
    qualified_name = f"`{schema_name}`.`{table_name}`" if schema_name else f"`{table_name}`"
    
    query = f"ALTER TABLE {qualified_name} DROP PARTITION `{partition_name}`"
    
    try:
        connection.execute(text(query))
        connection.commit()
    except SQLAlchemyError as e:
        connection.rollback()
        raise RuntimeError(f"Failed to drop partition from {qualified_name}: {e}") from e


def truncate_partition(
    table_name: str,
    schema_name: Optional[str],
    partition_name: str,
    connection: Connection
) -> None:
    """Truncate a specific partition (remove all data but keep the partition).
    
    Args:
        table_name: Name of the table
        schema_name: Schema name (optional)
        partition_name: Name of the partition to truncate
        connection: Database connection
    """
    qualified_name = f"`{schema_name}`.`{table_name}`" if schema_name else f"`{table_name}`"
    
    query = f"ALTER TABLE {qualified_name} TRUNCATE PARTITION `{partition_name}`"
    
    try:
        connection.execute(text(query))
        connection.commit()
    except SQLAlchemyError as e:
        connection.rollback()
        raise RuntimeError(f"Failed to truncate partition in {qualified_name}: {e}") from e


def reorganize_partitions(
    table_name: str,
    schema_name: Optional[str],
    partition_names: List[str],
    new_partition_definitions: List[tuple[str, str]],
    connection: Connection
) -> None:
    """Reorganize existing partitions into new partitions.
    
    Args:
        table_name: Name of the table
        schema_name: Schema name (optional)
        partition_names: List of partition names to reorganize
        new_partition_definitions: List of (partition_name, definition) tuples
        connection: Database connection
    """
    qualified_name = f"`{schema_name}`.`{table_name}`" if schema_name else f"`{table_name}`"
    
    partition_list = ", ".join([f"`{name}`" for name in partition_names])
    new_partitions = ", ".join([
        f"PARTITION `{name}` {definition}" 
        for name, definition in new_partition_definitions
    ])
    
    query = f"ALTER TABLE {qualified_name} REORGANIZE PARTITION {partition_list} INTO ({new_partitions})"
    
    try:
        connection.execute(text(query))
        connection.commit()
    except SQLAlchemyError as e:
        connection.rollback()
        raise RuntimeError(f"Failed to reorganize partitions in {qualified_name}: {e}") from e


def get_partition_info(
    table_name: str,
    schema_name: Optional[str],
    connection: Connection
) -> List[Dict[str, Any]]:
    """Get information about partitions in a table.
    
    Args:
        table_name: Name of the table
        schema_name: Schema name (optional)
        connection: Database connection
        
    Returns:
        List of dictionaries containing partition information
    """
    schema_condition = f"AND TABLE_SCHEMA = '{schema_name}'" if schema_name else ""
    
    query = f"""
        SELECT 
            PARTITION_NAME,
            PARTITION_METHOD,
            PARTITION_EXPRESSION,
            PARTITION_DESCRIPTION,
            TABLE_ROWS,
            AVG_ROW_LENGTH,
            DATA_LENGTH,
            CREATE_TIME,
            UPDATE_TIME
        FROM information_schema.PARTITIONS
        WHERE TABLE_NAME = '{table_name}' {schema_condition}
        AND PARTITION_NAME IS NOT NULL
        ORDER BY PARTITION_ORDINAL_POSITION
    """
    
    try:
        result = connection.execute(text(query))
        rows = result.fetchall()
        
        partitions = []
        for row in rows:
            partitions.append({
                "name": row[0],
                "method": row[1],
                "expression": row[2],
                "description": row[3],
                "rows": row[4],
                "avg_row_length": row[5],
                "data_length": row[6],
                "create_time": row[7],
                "update_time": row[8]
            })
        
        return partitions
    except SQLAlchemyError as e:
        raise RuntimeError(f"Failed to get partition info for {table_name}: {e}") from e


def optimize_partition(
    table_name: str,
    schema_name: Optional[str],
    partition_name: str,
    connection: Connection
) -> None:
    """Optimize a specific partition to reclaim space and improve performance.
    
    Args:
        table_name: Name of the table
        schema_name: Schema name (optional)
        partition_name: Name of the partition to optimize
        connection: Database connection
    """
    qualified_name = f"`{schema_name}`.`{table_name}`" if schema_name else f"`{table_name}`"
    
    query = f"ALTER TABLE {qualified_name} OPTIMIZE PARTITION `{partition_name}`"
    
    try:
        connection.execute(text(query))
        connection.commit()
    except SQLAlchemyError as e:
        connection.rollback()
        raise RuntimeError(f"Failed to optimize partition in {qualified_name}: {e}") from e


def check_partition(
    table_name: str,
    schema_name: Optional[str],
    partition_name: str,
    connection: Connection
) -> Dict[str, Any]:
    """Check a partition for errors.
    
    Args:
        table_name: Name of the table
        schema_name: Schema name (optional)
        partition_name: Name of the partition to check
        connection: Database connection
        
    Returns:
        Dictionary with check results
    """
    qualified_name = f"`{schema_name}`.`{table_name}`" if schema_name else f"`{table_name}`"
    
    query = f"CHECK TABLE {qualified_name} PARTITION (`{partition_name}`)"
    
    try:
        result = connection.execute(text(query))
        row = result.fetchone()
        
        if row is None:
            raise RuntimeError(f"No results returned from CHECK TABLE for {qualified_name}")
        
        return {
            "table": row[0],
            "op": row[1],
            "msg_type": row[2],
            "msg_text": row[3]
        }
    except SQLAlchemyError as e:
        raise RuntimeError(f"Failed to check partition in {qualified_name}: {e}") from e


def repair_partition(
    table_name: str,
    schema_name: Optional[str],
    partition_name: str,
    connection: Connection
) -> Dict[str, Any]:
    """Repair a corrupted partition.
    
    Args:
        table_name: Name of the table
        schema_name: Schema name (optional)
        partition_name: Name of the partition to repair
        connection: Database connection
        
    Returns:
        Dictionary with repair results
    """
    qualified_name = f"`{schema_name}`.`{table_name}`" if schema_name else f"`{table_name}`"
    
    query = f"REPAIR TABLE {qualified_name} PARTITION (`{partition_name}`)"
    
    try:
        result = connection.execute(text(query))
        row = result.fetchone()
        
        if row is None:
            raise RuntimeError(f"No results returned from REPAIR TABLE for {qualified_name}")
        
        return {
            "table": row[0],
            "op": row[1],
            "msg_type": row[2],
            "msg_text": row[3]
        }
    except SQLAlchemyError as e:
        raise RuntimeError(f"Failed to repair partition in {qualified_name}: {e}") from e