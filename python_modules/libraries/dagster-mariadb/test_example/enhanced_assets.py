from dagster import asset, AssetExecutionContext, AssetIn
import pandas as pd
from dagster_mariadb import MariaDBResource

# ============================================================================
# BASIC ASSETS - Test handle_output (writing)
# ============================================================================

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


# ============================================================================
# ENHANCED ASSETS - Test load_input (reading via IO Manager)
# ============================================================================

@asset(
    io_manager_key="mariadb_io_manager",
    compute_kind="pandas"
)
def filtered_airports(
    context: AssetExecutionContext,
    raw_airports: pd.DataFrame  # ← IO Manager loads this!
) -> pd.DataFrame:
    """
    Test load_input: Load raw_airports via IO Manager and filter.
    This tests that the IO Manager can READ data it previously wrote.
    """
    context.log.info(f"Received {len(raw_airports)} airports via IO Manager")
    
    # Filter for large airports in the US
    filtered = raw_airports[
        (raw_airports['country'] == 'United States') & 
        (raw_airports['iata'].notna())
    ].copy()
    
    context.log.info(f"Filtered to {len(filtered)} US airports")
    return filtered


@asset(
    io_manager_key="mariadb_io_manager",
    compute_kind="pandas"
)
def airline_summary(
    context: AssetExecutionContext,
    raw_airlines: pd.DataFrame  # ← IO Manager loads this!
) -> pd.DataFrame:
    """
    Test load_input: Create summary statistics from airlines.
    """
    context.log.info(f"Received {len(raw_airlines)} airlines via IO Manager")
    
    # Group by country
    summary = raw_airlines.groupby('country').agg({
        'name': 'count',
        'active': lambda x: (x == 'Y').sum()
    }).reset_index()
    
    summary.columns = ['country', 'total_airlines', 'active_airlines']
    summary = summary.sort_values('total_airlines', ascending=False).head(20)
    
    context.log.info(f"Created summary for {len(summary)} countries")
    return summary


@asset(
    io_manager_key="mariadb_io_manager",
    compute_kind="pandas"
)
def route_analysis(
    context: AssetExecutionContext,
    raw_routes: pd.DataFrame,      # ← IO Manager loads this!
    raw_airports: pd.DataFrame     # ← IO Manager loads this too!
) -> pd.DataFrame:
    """
    Test load_input with multiple inputs: Join routes with airports.
    Tests that IO Manager can load multiple DataFrames.
    """
    context.log.info(f"Received {len(raw_routes)} routes via IO Manager")
    context.log.info(f"Received {len(raw_airports)} airports via IO Manager")
    
    # Create a mapping of IATA codes to countries
    airport_countries = raw_airports[['iata', 'country']].dropna()
    airport_countries = airport_countries.rename(columns={'country': 'source_country'})
    
    # Join routes with source airport countries
    routes_with_country = raw_routes.merge(
        airport_countries,
        left_on='src_ap',
        right_on='iata',
        how='inner'
    )
    
    # Count routes by source country
    route_counts = routes_with_country.groupby('source_country').size().reset_index()
    route_counts.columns = ['country', 'outbound_routes']
    route_counts = route_counts.sort_values('outbound_routes', ascending=False).head(30)
    
    context.log.info(f"Analyzed routes for {len(route_counts)} countries")
    return route_counts


# ============================================================================
# APPEND MODE TEST
# ============================================================================

@asset(
    io_manager_key="mariadb_io_manager_append",  # Different IO manager with append mode
    compute_kind="pandas"
)
def incremental_data(
    context: AssetExecutionContext,
    raw_airports: pd.DataFrame
) -> pd.DataFrame:
    """
    Test append mode: Each run adds more data instead of replacing.
    """
    # Take a small sample
    sample = raw_airports.sample(n=min(10, len(raw_airports)))
    context.log.info(f"Appending {len(sample)} airport records")
    return sample


# ============================================================================
# COLUMN SELECTION TEST (using metadata)
# ============================================================================

@asset(
    io_manager_key="mariadb_io_manager",
    compute_kind="pandas",
    ins={
        "raw_airports": AssetIn(
            metadata={"columns": ["name", "city", "country", "iata"]}
        )
    }
)
def airport_names_only(
    context: AssetExecutionContext,
    raw_airports: pd.DataFrame  # ← Should only load specified columns
) -> pd.DataFrame:
    """
    Test column selection: IO Manager should only load specified columns.
    """
    context.log.info(f"Columns loaded: {list(raw_airports.columns)}")
    context.log.info(f"Number of columns: {len(raw_airports.columns)}")
    
    # Should have only 4 columns if metadata worked
    if len(raw_airports.columns) == 4:
        context.log.info("✅ Column selection worked!")
    else:
        context.log.warning(f"⚠️  Expected 4 columns, got {len(raw_airports.columns)}")
    
    return raw_airports
