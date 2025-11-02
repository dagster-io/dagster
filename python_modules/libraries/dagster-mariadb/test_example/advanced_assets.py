"""
Assets for testing MariaDB advanced features.
"""

from dagster import asset, AssetExecutionContext
import pandas as pd
from sqlalchemy import text 
from dagster_mariadb import MariaDBResource
from dagster_mariadb.advanced_features import (
    StorageEngine,
    create_table_with_storage_engine,
    check_galera_cluster_status,
    optimize_for_write_heavy_load,
    get_storage_engine_info,
    setup_analytics_warehouse,
    create_columnstore_table,
)


# ========== Test 1: Storage Engine Information ==========
@asset(compute_kind="MariaDB")
def storage_engine_info(context: AssetExecutionContext, mariadb: MariaDBResource) -> pd.DataFrame:
    """Test get_storage_engine_info - retrieves available storage engines."""
    with mariadb.get_connection() as conn:
        engine_info = get_storage_engine_info(conn)
        
        context.log.info(f"Available engines: {engine_info['available']}")
        context.log.info(f"Supported engines: {engine_info['supported']}")
        
        df = pd.DataFrame({
            'engine_type': ['available', 'supported'],
            'engines': [
                ', '.join(engine_info['available']),
                ', '.join(engine_info['supported'])
            ]
        })
    
    return df


# ========== Test 2: Create Table with InnoDB Engine ==========
@asset(compute_kind="MariaDB")
def test_innodb_table(context: AssetExecutionContext, mariadb: MariaDBResource) -> pd.DataFrame:
    """Test create_table_with_storage_engine with InnoDB (default engine)."""
    with mariadb.get_connection() as conn:
        from sqlalchemy import text
        
        # Drop table if exists
        try:
            conn.execute(text("DROP TABLE IF EXISTS flightdb2.test_innodb_logs"))
            conn.commit()
        except:
            pass
        
        # Create test table with InnoDB
        create_table_with_storage_engine(
            table_name="test_innodb_logs",
            schema_name="flightdb2",
            columns={
                "id": "INT AUTO_INCREMENT PRIMARY KEY",
                "log_message": "TEXT",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            },
            connection=conn,
            storage_engine=StorageEngine.InnoDB
        )
        
        # Insert test data
        conn.execute(text("""
            INSERT INTO flightdb2.test_innodb_logs (log_message)
            VALUES ('Test log entry 1'), ('Test log entry 2'), ('Test log entry 3')
        """))
        conn.commit()
        
        # Verify table creation and data
        df = pd.read_sql("SELECT * FROM flightdb2.test_innodb_logs", conn)
        
        context.log.info("Created InnoDB table with {} rows".format(len(df)))
    
    return df


# ========== Test 3: Create Table with Aria Engine ==========
@asset(compute_kind="MariaDB")
def test_aria_table(context: AssetExecutionContext, mariadb: MariaDBResource) -> pd.DataFrame:
    """Test create_table_with_storage_engine with Aria (crash-safe MyISAM)."""
    with mariadb.get_connection() as conn:
        from sqlalchemy import text
        
        # Drop table if exists to avoid duplicate key errors
        try:
            conn.execute(text("DROP TABLE IF EXISTS flightdb2.test_aria_cache"))
            conn.commit()
        except:
            pass
        
        # Create test table with Aria
        create_table_with_storage_engine(
            table_name="test_aria_cache",
            schema_name="flightdb2",
            columns={
                "cache_key": "VARCHAR(255) PRIMARY KEY",
                "cache_value": "TEXT",
                "expires_at": "DATETIME"
            },
            connection=conn,
            storage_engine=StorageEngine.Aria
        )
        
        # Insert test data
        conn.execute(text("""
            INSERT INTO flightdb2.test_aria_cache (cache_key, cache_value, expires_at)
            VALUES 
                ('key1', 'value1', '2025-12-31 23:59:59'),
                ('key2', 'value2', '2025-12-31 23:59:59'),
                ('key3', 'value3', '2025-12-31 23:59:59')
        """))
        conn.commit()
        
        # Verify
        df = pd.read_sql("SELECT * FROM flightdb2.test_aria_cache", conn)
        
        context.log.info("Created Aria table with {} rows".format(len(df)))
    
    return df


# ========== Test 4: Optimize Table for Write-Heavy Load ==========
@asset(
    compute_kind="MariaDB",
    deps=[test_innodb_table]
)
def test_optimize_write_heavy(context: AssetExecutionContext, mariadb: MariaDBResource) -> pd.DataFrame:
    """Test optimize_for_write_heavy_load - converts table engine for better write performance."""
    with mariadb.get_connection() as conn:
        from sqlalchemy import text
        
        # Drop table if exists
        try:
            conn.execute(text("DROP TABLE IF EXISTS flightdb2.test_write_heavy"))
            conn.commit()
        except:
            pass
        
        # Create a temporary table for testing
        create_table_with_storage_engine(
            table_name="test_write_heavy",
            schema_name="flightdb2",
            columns={
                "id": "INT AUTO_INCREMENT PRIMARY KEY",
                "data": "VARCHAR(255)",
                "timestamp": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            },
            connection=conn,
            storage_engine=StorageEngine.InnoDB
        )
        
        # Check initial engine
        initial_engine = pd.read_sql("""
            SELECT ENGINE 
            FROM information_schema.TABLES 
            WHERE TABLE_SCHEMA = 'flightdb2' 
            AND TABLE_NAME = 'test_write_heavy'
        """, conn)
        
        context.log.info("Initial engine: {}".format(initial_engine['ENGINE'].iloc[0]))
        
        # Note: optimize_for_write_heavy_load would convert to MyRocks if available
        # but MyRocks may not be installed, so we'll just test the InnoDB path
        try:
            optimize_for_write_heavy_load(
                table_name="test_write_heavy",
                schema_name="flightdb2",
                connection=conn,
                use_myrocks=False  # Use InnoDB since MyRocks may not be available
            )
        except Exception as e:
            context.log.warning("MyRocks optimization not available: {}".format(str(e)))
        
        # Check final engine
        final_engine = pd.read_sql("""
            SELECT ENGINE 
            FROM information_schema.TABLES 
            WHERE TABLE_SCHEMA = 'flightdb2' 
            AND TABLE_NAME = 'test_write_heavy'
        """, conn)
        
        context.log.info("Final engine: {}".format(final_engine['ENGINE'].iloc[0]))
        
        result_df = pd.DataFrame({
            'table': ['test_write_heavy'],
            'initial_engine': [initial_engine['ENGINE'].iloc[0]],
            'final_engine': [final_engine['ENGINE'].iloc[0]]
        })
    
    return result_df



# ========== Test 5: Galera Cluster Status ==========
@asset(compute_kind="MariaDB")
def test_galera_cluster_status(context: AssetExecutionContext, mariadb: MariaDBResource) -> pd.DataFrame:
    """Test check_galera_cluster_status - checks if running in Galera Cluster mode."""
    with mariadb.get_connection() as conn:
        cluster_status = check_galera_cluster_status(conn)
        
        if cluster_status is None:
            context.log.info("Not running in Galera Cluster mode")
            df = pd.DataFrame({
                'status': ['Not in Galera Cluster'],
                'value': ['N/A']
            })
        else:
            context.log.info(f"Galera Cluster Status: {cluster_status}")
            df = pd.DataFrame([
                {'metric': 'connected', 'value': cluster_status['connected']},
                {'metric': 'ready', 'value': cluster_status['ready']},
                {'metric': 'cluster_size', 'value': cluster_status['cluster_size']},
                {'metric': 'local_state', 'value': cluster_status['local_state']}
            ])
    
    return df


# ========== Test 6: Analytics Warehouse Setup ==========
@asset(compute_kind="MariaDB")
def test_analytics_warehouse(context: AssetExecutionContext, mariadb: MariaDBResource) -> pd.DataFrame:
    """Test setup_analytics_warehouse - creates a database for analytics."""
    with mariadb.get_connection() as conn:
        warehouse_name = "test_analytics_warehouse"
        
        # Setup warehouse
        setup_analytics_warehouse(
            connection=conn,
            database_name=warehouse_name
        )
        
        context.log.info(f"Created analytics warehouse: {warehouse_name}")
        
        # Verify database creation
        df = pd.read_sql(f"""
            SELECT SCHEMA_NAME 
            FROM information_schema.SCHEMATA 
            WHERE SCHEMA_NAME = '{warehouse_name}'
        """, conn)
        
        if len(df) > 0:
            context.log.info(f"Warehouse {warehouse_name} successfully created")
        else:
            context.log.warning(f"Warehouse {warehouse_name} not found")
    
    return df


# ========== Test 7: Table Engine Comparison ==========
@asset(
    compute_kind="MariaDB",
    deps=[test_innodb_table, test_aria_table]
)
def compare_storage_engines(context: AssetExecutionContext, mariadb: MariaDBResource) -> pd.DataFrame:
    """Compare different storage engines used in test tables."""
    with mariadb.get_connection() as conn:
        df = pd.read_sql("""
            SELECT 
                TABLE_NAME,
                ENGINE,
                TABLE_ROWS,
                DATA_LENGTH,
                INDEX_LENGTH,
                CREATE_TIME
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = 'flightdb2'
            AND TABLE_NAME LIKE 'test_%%'
            ORDER BY TABLE_NAME
        """, conn)
        
        context.log.info(f"Found {len(df)} test tables with various engines")
        
        for _, row in df.iterrows():
            context.log.info(
                f"Table: {row['TABLE_NAME']}, "
                f"Engine: {row['ENGINE']}, "
                f"Rows: {row['TABLE_ROWS']}"
            )
    
    return df


# ========== Test 8: Multi-Engine Performance Test ==========
@asset(compute_kind="MariaDB")
def test_multi_engine_performance(context: AssetExecutionContext, mariadb: MariaDBResource) -> pd.DataFrame:
    """Create identical tables with different engines and insert test data."""
    with mariadb.get_connection() as conn:
        from sqlalchemy import text
        
        engines_to_test = [StorageEngine.InnoDB, StorageEngine.Aria]
        results = []
        
        for engine in engines_to_test:
            table_name = "perf_test_{}".format(engine.lower())
            
            # Drop table if exists
            try:
                conn.execute(text("DROP TABLE IF EXISTS flightdb2.{}".format(table_name)))
                conn.commit()
            except:
                pass
            
            # Create table
            create_table_with_storage_engine(
                table_name=table_name,
                schema_name="flightdb2",
                columns={
                    "id": "INT AUTO_INCREMENT PRIMARY KEY",
                    "data1": "VARCHAR(100)",
                    "data2": "INT",
                    "data3": "DECIMAL(10,2)"
                },
                connection=conn,
                storage_engine=engine
            )
            
            # Insert 300 rows
            import time
            start_time = time.time()
            
            for i in range(100):  # Insert in batches
                conn.execute(text("""
                    INSERT INTO flightdb2.{} (data1, data2, data3)
                    VALUES 
                        ('test_{}_1', {}, {}),
                        ('test_{}_2', {}, {}),
                        ('test_{}_3', {}, {})
                """.format(
                    table_name,
                    i, i * 10, i * 1.5,
                    i, i * 20, i * 2.5,
                    i, i * 30, i * 3.5
                )))
            conn.commit()
            
            insert_time = time.time() - start_time
            
            # Get row count
            count_df = pd.read_sql(
                "SELECT COUNT(*) as cnt FROM flightdb2.{}".format(table_name),
                conn
            )
            
            results.append({
                'engine': engine,
                'table_name': table_name,
                'rows_inserted': count_df['cnt'].iloc[0],
                'insert_time_seconds': round(insert_time, 3)
            })
            
            context.log.info(
                "{} engine: Inserted {} rows in {:.3f} seconds".format(
                    engine,
                    count_df['cnt'].iloc[0],
                    insert_time
                )
            )
        
        df = pd.DataFrame(results)
    
    return df


# ========== Test 9: ColumnStore Table Test ==========
@asset(compute_kind="MariaDB")
def test_columnstore_table(context: AssetExecutionContext, mariadb: MariaDBResource) -> pd.DataFrame:
    """Test create_columnstore_table for analytical workloads (if ColumnStore is available)."""
    with mariadb.get_connection() as conn:
        from sqlalchemy import text
        
        try:
            # Drop table if exists
            try:
                conn.execute(text("DROP TABLE IF EXISTS flightdb2.test_columnstore_analytics"))
                conn.commit()
            except:
                pass
            
            # Try to create ColumnStore table
            create_columnstore_table(
                table_name="test_columnstore_analytics",
                schema_name="flightdb2",
                columns={
                    "year": "INT",
                    "month": "INT",
                    "revenue": "DECIMAL(15,2)",
                    "transactions": "BIGINT"
                },
                connection=conn
            )
            
            # Insert sample data
            conn.execute(text("""
                INSERT INTO flightdb2.test_columnstore_analytics 
                VALUES (2024, 1, 100000.50, 1500),
                       (2024, 2, 150000.75, 2000),
                       (2024, 3, 200000.25, 2500)
            """))
            conn.commit()
            
            df = pd.read_sql("SELECT * FROM flightdb2.test_columnstore_analytics", conn)
            
            context.log.info("ColumnStore table created with {} rows".format(len(df)))
            
        except Exception as e:
            context.log.warning("ColumnStore not available: {}".format(str(e)))
            df = pd.DataFrame({
                'status': ['ColumnStore not available'],
                'message': [str(e)]
            })
    
    return df


# ========== Test 10: Comprehensive Engine Feature Summary ==========
@asset(
    compute_kind="MariaDB",
    deps=[
        storage_engine_info,
        test_innodb_table,
        test_aria_table,
        compare_storage_engines,
        test_multi_engine_performance
    ]
)
def advanced_features_summary(context: AssetExecutionContext, mariadb: MariaDBResource) -> pd.DataFrame:
    """Generate comprehensive summary of all advanced features tested."""
    with mariadb.get_connection() as conn:
        # Get all test tables
        tables_df = pd.read_sql("""
            SELECT 
                TABLE_NAME,
                ENGINE,
                TABLE_ROWS,
                ROUND(DATA_LENGTH/1024, 2) as DATA_KB,
                CREATE_TIME
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = 'flightdb2'
            AND (TABLE_NAME LIKE 'test_%%' OR TABLE_NAME LIKE 'perf_%%')
            ORDER BY CREATE_TIME DESC
        """, conn)
        
        context.log.info("=" * 60)
        context.log.info("ADVANCED FEATURES TEST SUMMARY")
        context.log.info("=" * 60)
        context.log.info(f"Total test tables created: {len(tables_df)}")
        
        # Group by engine
        engine_summary = tables_df.groupby('ENGINE').agg({
            'TABLE_NAME': 'count',
            'TABLE_ROWS': 'sum'
        }).reset_index()
        
        context.log.info("\nTables by Engine:")
        for _, row in engine_summary.iterrows():
            context.log.info(
                "  {}: {} tables, {} total rows".format(
                    row['ENGINE'], 
                    row['TABLE_NAME'], 
                    row['TABLE_ROWS']
            ))
        
        context.log.info("=" * 60)
    
    return tables_df