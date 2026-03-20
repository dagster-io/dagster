import dagster as dg
from dagster_duckdb import DuckDBResource


@dg.asset(
    # highlight-start
    deps=[dg.AssetKey(["daily_metrics"])],
    # highlight-end
    kinds={"duckdb"},
)
def manhattan_stats(database: DuckDBResource) -> dg.MaterializeResult:
    query = """
        select count(*)
        from daily_metrics
    """

    with database.get_connection() as conn:
        result = conn.execute(query).fetchone()
        count = result[0] if result else 0
        return dg.MaterializeResult(metadata={"table_count": dg.MetadataValue.int(count)})
