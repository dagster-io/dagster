from dagster import asset, AssetExecutionContext
import pandas as pd
from dagster_mariadb import MariaDBResource

@asset(
    io_manager_key="mariadb_io_manager",
    compute_kind="MariaDB"
)
def raw_airports(context: AssetExecutionContext, mariadb: MariaDBResource) -> pd.DataFrame:
    """Load raw airports data from the existing OpenFlights database."""
    
    with mariadb.get_connection() as conn:
        query = "SELECT * FROM airports"
        df = pd.read_sql(query, conn)
    
    context.log.info(f"Loaded {len(df)} airports from MariaDB")
    return df

@asset(
    io_manager_key="mariadb_io_manager",
    compute_kind="MariaDB"
)
def raw_airlines(context: AssetExecutionContext, mariadb: MariaDBResource) -> pd.DataFrame:
    """Load raw airlines data from the existing OpenFlights database."""
    
    with mariadb.get_connection() as conn:
        query = "SELECT * FROM airlines"
        df = pd.read_sql(query, conn)
    
    context.log.info(f"Loaded {len(df)} airlines from MariaDB")
    return df

@asset(
    io_manager_key="mariadb_io_manager",
    compute_kind="MariaDB"
)
def raw_routes(context: AssetExecutionContext, mariadb: MariaDBResource) -> pd.DataFrame:
    """Load raw routes data from the existing OpenFlights database."""
    
    with mariadb.get_connection() as conn:
        query = "SELECT * FROM routes"
        df = pd.read_sql(query, conn)
    
    context.log.info(f"Loaded {len(df)} routes from MariaDB")
    return df

@asset(
    io_manager_key="mariadb_io_manager",
    compute_kind="pandas",
    deps=[raw_airports, raw_airlines, raw_routes]
)
def airports_with_airline_count(context: AssetExecutionContext, mariadb: MariaDBResource) -> pd.DataFrame:
    """Calculate number of airlines per airport."""
    
    with mariadb.get_connection() as conn:
        query = """
        SELECT 
            a.name as airport_name,
            a.city,
            a.country,
            a.iata,
            COUNT(DISTINCT r.airline) as airline_count
        FROM airports a
        LEFT JOIN routes r ON a.iata = r.src_ap
        GROUP BY a.iata, a.name, a.city, a.country
        HAVING airline_count > 0
        ORDER BY airline_count DESC
        LIMIT 100
        """
        df = pd.read_sql(query, conn)
    
    context.log.info(f"Calculated airline counts for {len(df)} airports")
    return df

@asset(
    io_manager_key="mariadb_io_manager",
    compute_kind="pandas",
    deps=[raw_routes, raw_airports]
)
def route_statistics(context: AssetExecutionContext, mariadb: MariaDBResource) -> pd.DataFrame:
    """Calculate route statistics by country."""
    
    with mariadb.get_connection() as conn:
        query = """
        SELECT 
            a.country,
            COUNT(DISTINCT r.src_ap) as unique_source_airports,
            COUNT(DISTINCT r.dst_ap) as unique_dest_airports,
            COUNT(*) as total_routes
        FROM routes r
        JOIN airports a ON r.src_ap = a.iata
        GROUP BY a.country
        ORDER BY total_routes DESC
        LIMIT 50
        """
        df = pd.read_sql(query, conn)
    
    context.log.info(f"Calculated route statistics for {len(df)} countries")
    return df