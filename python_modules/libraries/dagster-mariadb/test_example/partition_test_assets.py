"""
Comprehensive tests for MariaDB native partitioning with Dagster.
Tests Version 2: MariaDBPartitionedPandasIOManager
"""

from dagster import (
    asset,
    AssetExecutionContext,
    DailyPartitionsDefinition,
    MonthlyPartitionsDefinition,
    WeeklyPartitionsDefinition,
    StaticPartitionsDefinition,
    MultiPartitionsDefinition,
)
import pandas as pd
from datetime import datetime, timedelta
from dagster_mariadb import MariaDBResource
from dagster_mariadb.partitions import get_partition_info, check_partition, optimize_partition


# ========== Define Partition Definitions ==========
daily_partitions = DailyPartitionsDefinition(start_date="2024-01-01", end_date="2024-01-10")
monthly_partitions = MonthlyPartitionsDefinition(start_date="2024-01-01", end_date="2024-06-01")
weekly_partitions = WeeklyPartitionsDefinition(start_date="2024-01-01", end_date="2024-02-01")
region_partitions = StaticPartitionsDefinition(["north", "south", "east", "west"])

# Multi-dimensional: date x region
multi_partitions = MultiPartitionsDefinition({
    "date": DailyPartitionsDefinition(start_date="2024-01-01", end_date="2024-01-05"),
    "region": StaticPartitionsDefinition(["north", "south"])
})


# ========== Test 1: Daily Partitioned Asset with Native Partitioning ==========
@asset(
    partitions_def=daily_partitions,
    io_manager_key="partitioned_io_manager",
    compute_kind="MariaDB",
    metadata={"partition_column": "event_date"}
)
def daily_sales(context: AssetExecutionContext) -> pd.DataFrame:
    """Generate daily sales data with native MariaDB partitioning."""
    date = context.partition_key
    context.log.info("Generating daily sales for {}".format(date))
    
    from datetime import datetime
    date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    # Generate sample sales data
    num_records = 50
    df = pd.DataFrame({
        'sale_id': range(1, num_records + 1),
        'event_date': [date_obj] * num_records,
        'product': ['Product_{}'.format(i % 5) for i in range(num_records)],
        'amount': [100.0 + (i * 10.5) for i in range(num_records)],
        'quantity': [i % 10 + 1 for i in range(num_records)]
    })
    
    context.log.info("Generated {} sales records for {}".format(len(df), date))
    return df


# ========== Test 2: Monthly Partitioned Asset ==========
@asset(
    partitions_def=monthly_partitions,
    io_manager_key="partitioned_io_manager",
    compute_kind="MariaDB",
    metadata={"partition_column": "month"}
)
def monthly_revenue(context: AssetExecutionContext) -> pd.DataFrame:
    """Generate monthly revenue summary with native partitioning."""
    month = context.partition_key
    context.log.info("Generating monthly revenue for {}".format(month))
    
    # Convert month string to date (first day of month) for proper partitioning
    from datetime import datetime
    month_date = datetime.strptime(month, "%Y-%m-%d").date()
    
    df = pd.DataFrame({
        'month': [month_date] * 20,  # Use date type instead of string
        'department': ['Dept_{}'.format(i) for i in range(20)],
        'revenue': [10000.0 * (i + 1) for i in range(20)],
        'expenses': [7000.0 * (i + 1) for i in range(20)],
        'profit': [3000.0 * (i + 1) for i in range(20)]
    })
    
    context.log.info("Generated {} department records for {}".format(len(df), month))
    return df


# ========== Test 3: Weekly Partitioned Asset ==========
@asset(
    partitions_def=weekly_partitions,
    io_manager_key="partitioned_io_manager",
    compute_kind="MariaDB",
    metadata={"partition_column": "week_start"}
)
def weekly_metrics(context: AssetExecutionContext) -> pd.DataFrame:
    """Generate weekly metrics with native partitioning."""
    week = context.partition_key
    context.log.info("Generating weekly metrics for {}".format(week))
    
    from datetime import datetime
    week_date = datetime.strptime(week, "%Y-%m-%d").date()
    df = pd.DataFrame({
        'week_start': [week_date] * 15,
        'metric_name': ['metric_{}'.format(i) for i in range(15)],
        'value': [1000.0 * i for i in range(15)],
        'target': [1200.0 * i for i in range(15)]
    })
    
    context.log.info("Generated {} metrics for week {}".format(len(df), week))
    return df


# ========== Test 4: Static Partitioned Asset (by Region) ==========
@asset(
    partitions_def=region_partitions,
    io_manager_key="partitioned_io_manager",
    compute_kind="MariaDB",
    metadata={"partition_column": "region"}
)
def regional_inventory(context: AssetExecutionContext) -> pd.DataFrame:
    """Generate regional inventory with LIST partitioning."""
    region = context.partition_key
    context.log.info("Generating inventory for region: {}".format(region))
    
    df = pd.DataFrame({
        'region': [region] * 30,
        'product_id': ['PROD_{}'.format(i) for i in range(30)],
        'stock_level': [100 + (i * 5) for i in range(30)],
        'reorder_point': [50 + (i * 2) for i in range(30)]
    })
    
    context.log.info("Generated {} inventory items for {}".format(len(df), region))
    return df


# ========== Test 5: Multi-Dimensional Partitioned Asset ==========
@asset(
    partitions_def=multi_partitions,
    io_manager_key="partitioned_io_manager_app_level",  # Multi-dim uses app-level
    compute_kind="MariaDB",
    metadata={
        "date_column": "event_date",
        "region_column": "region"
    }
)
def multi_dim_transactions(context: AssetExecutionContext) -> pd.DataFrame:
    """Generate transaction data partitioned by date AND region."""
    partition_key = context.partition_key
    context.log.info("Generating transactions for partition: {}".format(partition_key))
    
    # Parse multi-partition key
    from dagster import MultiPartitionKey
    if isinstance(partition_key, MultiPartitionKey):
        date = partition_key.keys_by_dimension["date"]
        region = partition_key.keys_by_dimension["region"]
    else:
        parts = str(partition_key).split("|")
        region = parts[0] if len(parts) > 0 else "unknown"
        date = parts[1] if len(parts) > 1 else "2024-01-01"
    
    df = pd.DataFrame({
        'transaction_id': range(1, 21),
        'event_date': [date] * 20,
        'region': [region] * 20,
        'amount': [50.0 + (i * 7.5) for i in range(20)],
        'customer_id': ['CUST_{}'.format(i) for i in range(20)]
    })
    
    context.log.info("Generated {} transactions for {} in {}".format(len(df), date, region))
    return df


# ========== Test 6: Partition-Dependent Asset ==========
@asset(
    partitions_def=daily_partitions,
    io_manager_key="partitioned_io_manager",
    compute_kind="pandas",
    metadata={"partition_column": "summary_date"}
)
def daily_sales_summary(
    context: AssetExecutionContext,
    daily_sales: pd.DataFrame  # This will automatically use the correct partition column from upstream
) -> pd.DataFrame:
    """Aggregate daily sales - depends on partitioned asset."""
    date = context.partition_key
    context.log.info("Creating summary for {}".format(date))
    
    # Convert date string to date object
    from datetime import datetime
    date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    
    # Aggregate by product
    summary = daily_sales.groupby('product').agg({
        'amount': ['sum', 'mean', 'count'],
        'quantity': 'sum'
    }).reset_index()
    
    # Flatten column names
    summary.columns = ['product', 'total_amount', 'avg_amount', 'num_sales', 'total_quantity']
    summary['summary_date'] = date_obj  # Use date type
    
    context.log.info("Created summary with {} products".format(len(summary)))
    return summary


# ========== Test 7: Inspect Partition Information ==========
@asset(
    compute_kind="MariaDB",
    deps=[daily_sales, monthly_revenue, regional_inventory]
)
def partition_metadata_report(
    context: AssetExecutionContext,
    mariadb: MariaDBResource
) -> pd.DataFrame:
    """Inspect native partition metadata for all partitioned tables."""
    with mariadb.get_connection() as conn:
        tables_to_inspect = [
            ('daily_sales', 'flightdb2'),
            ('monthly_revenue', 'flightdb2'),
            ('regional_inventory', 'flightdb2'),
            ('weekly_metrics', 'flightdb2')
        ]
        
        all_partition_info = []
        
        for table_name, schema_name in tables_to_inspect:
            try:
                partition_info = get_partition_info(
                    table_name=table_name,
                    schema_name=schema_name,
                    connection=conn
                )
                
                context.log.info("Table: {} has {} partitions".format(
                    table_name, len(partition_info)
                ))
                
                for partition in partition_info:
                    all_partition_info.append({
                        'table': table_name,
                        'partition_name': partition['name'],
                        'method': partition['method'],
                        'expression': partition['expression'],
                        'rows': partition['rows'],
                        'data_length_kb': partition['data_length'] / 1024 if partition['data_length'] else 0
                    })
                    
            except Exception as e:
                context.log.warning("Could not inspect {}: {}".format(table_name, str(e)))
        
        df = pd.DataFrame(all_partition_info)
        context.log.info("Collected metadata for {} partitions".format(len(df)))
        
        return df


# ========== Test 8: Query Specific Partition ==========
@asset(
    compute_kind="MariaDB",
    deps=[daily_sales]
)
def query_specific_partition(
    context: AssetExecutionContext,
    mariadb: MariaDBResource
) -> pd.DataFrame:
    """Query a specific partition directly to test partition pruning."""
    target_date = "2024-01-05"
    
    with mariadb.get_connection() as conn:
        # Query with partition filter - MariaDB should prune other partitions
        query = """
            SELECT 
                event_date,
                product,
                COUNT(*) as sale_count,
                SUM(amount) as total_amount,
                SUM(quantity) as total_quantity
            FROM flightdb2.daily_sales
            WHERE event_date = '{}'
            GROUP BY event_date, product
        """.format(target_date)
        
        df = pd.read_sql(query, conn)
        
        context.log.info("Queried partition for {} - found {} products".format(
            target_date, len(df)
        ))
        
        # Check explain to see if partition pruning worked
        explain_query = "EXPLAIN PARTITIONS " + query
        explain_result = pd.read_sql(explain_query, conn)
        
        context.log.info("Partitions accessed: {}".format(
            explain_result['partitions'].iloc[0] if len(explain_result) > 0 else 'unknown'
        ))
    
    return df


# ========== Test 9: Check and Optimize Partitions ==========
@asset(
    compute_kind="MariaDB",
    deps=[daily_sales, monthly_revenue]
)
def partition_maintenance(
    context: AssetExecutionContext,
    mariadb: MariaDBResource
) -> pd.DataFrame:
    """Perform maintenance operations on partitions."""
    results = []
    
    with mariadb.get_connection() as conn:
        # Check partitions for daily_sales
        partition_info = get_partition_info(
            table_name="daily_sales",
            schema_name="flightdb2",
            connection=conn
        )
        
        for partition in partition_info[:3]:  # Check first 3 partitions
            partition_name = partition['name']
            
            try:
                # Check partition health
                check_result = check_partition(
                    table_name="daily_sales",
                    schema_name="flightdb2",
                    partition_name=partition_name,
                    connection=conn
                )
                
                context.log.info("Checked partition {}: {}".format(
                    partition_name, check_result['msg_text']
                ))
                
                # Optimize partition
                optimize_partition(
                    table_name="daily_sales",
                    schema_name="flightdb2",
                    partition_name=partition_name,
                    connection=conn
                )
                
                context.log.info("Optimized partition {}".format(partition_name))
                
                results.append({
                    'table': 'daily_sales',
                    'partition': partition_name,
                    'check_status': check_result['msg_text'],
                    'optimized': True
                })
                
            except Exception as e:
                context.log.warning("Maintenance failed for {}: {}".format(
                    partition_name, str(e)
                ))
                results.append({
                    'table': 'daily_sales',
                    'partition': partition_name,
                    'check_status': 'Error',
                    'optimized': False
                })
    
    df = pd.DataFrame(results)
    return df


# ========== Test 10: Partition Performance Comparison ==========
@asset(
    compute_kind="MariaDB",
    deps=[daily_sales]
)
def partition_performance_test(
    context: AssetExecutionContext,
    mariadb: MariaDBResource
) -> pd.DataFrame:
    """Compare query performance with and without partition pruning."""
    import time
    
    results = []
    
    with mariadb.get_connection() as conn:
        # Test 1: Query with partition filter (should use partition pruning)
        start = time.time()
        query_with_filter = """
            SELECT COUNT(*), SUM(amount) 
            FROM flightdb2.daily_sales 
            WHERE event_date = '2024-01-03'
        """
        df1 = pd.read_sql(query_with_filter, conn)
        time_with_filter = time.time() - start
        
        context.log.info("Query with partition filter: {:.4f}s".format(time_with_filter))
        
        # Test 2: Query without filter (full table scan)
        start = time.time()
        query_full_scan = """
            SELECT COUNT(*), SUM(amount) 
            FROM flightdb2.daily_sales
        """
        df2 = pd.read_sql(query_full_scan, conn)
        time_full_scan = time.time() - start
        
        context.log.info("Query full table scan: {:.4f}s".format(time_full_scan))
        
        # Test 3: Query with range filter (should use multiple partitions)
        start = time.time()
        query_range = """
            SELECT COUNT(*), SUM(amount) 
            FROM flightdb2.daily_sales 
            WHERE event_date BETWEEN '2024-01-01' AND '2024-01-05'
        """
        df3 = pd.read_sql(query_range, conn)
        time_range = time.time() - start
        
        context.log.info("Query with range filter: {:.4f}s".format(time_range))
        
        results = [{
            'query_type': 'Single Partition',
            'execution_time_ms': time_with_filter * 1000,
            'rows_returned': df1.iloc[0, 0]
        }, {
            'query_type': 'Full Table Scan',
            'execution_time_ms': time_full_scan * 1000,
            'rows_returned': df2.iloc[0, 0]
        }, {
            'query_type': 'Range (5 partitions)',
            'execution_time_ms': time_range * 1000,
            'rows_returned': df3.iloc[0, 0]
        }]
    
    df = pd.DataFrame(results)
    return df


# ========== Test 11: Comprehensive Test Summary ==========
@asset(
    compute_kind="MariaDB",
    deps=[
        daily_sales,
        monthly_revenue,
        weekly_metrics,
        regional_inventory,
        multi_dim_transactions,
        daily_sales_summary,
        partition_metadata_report,
        partition_maintenance,
        partition_performance_test
    ]
)
def partition_test_summary(
    context: AssetExecutionContext,
    mariadb: MariaDBResource
) -> pd.DataFrame:
    """Generate comprehensive summary of all partition tests."""
    with mariadb.get_connection() as conn:
        # Get all partitioned tables
        query = """
            SELECT 
                TABLE_NAME,
                CREATE_OPTIONS,
                TABLE_ROWS,
                ROUND(DATA_LENGTH/1024/1024, 2) as DATA_MB,
                ENGINE
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = 'flightdb2'
            AND (TABLE_NAME LIKE 'daily_%%' 
                OR TABLE_NAME LIKE 'monthly_%%' 
                OR TABLE_NAME LIKE 'weekly_%%' 
                OR TABLE_NAME LIKE 'regional_%%'
                OR TABLE_NAME LIKE 'multi_%%'
            )
            ORDER BY TABLE_NAME
        """
        
        tables_df = pd.read_sql(query, conn)
        
        # Count partitions for each table
        partition_counts = []
        for _, row in tables_df.iterrows():
            table_name = row['TABLE_NAME']
            try:
                partition_info = get_partition_info(
                    table_name=table_name,
                    schema_name='flightdb2',
                    connection=conn
                )
                partition_counts.append(len(partition_info))
            except:
                partition_counts.append(0)
        
        tables_df['num_partitions'] = partition_counts
        
        context.log.info("=" * 70)
        context.log.info("PARTITION TEST SUMMARY")
        context.log.info("=" * 70)
        context.log.info("Total partitioned tables: {}".format(len(tables_df)))
        context.log.info("Total partitions across all tables: {}".format(sum(partition_counts)))
        context.log.info("\nTables by partition type:")
        
        for _, row in tables_df.iterrows():
            context.log.info("  {}: {} partitions, {} rows, {:.2f} MB".format(
                row['TABLE_NAME'],
                row['num_partitions'],
                row['TABLE_ROWS'],
                row['DATA_MB']
            ))
        
        context.log.info("=" * 70)
    
    return tables_df