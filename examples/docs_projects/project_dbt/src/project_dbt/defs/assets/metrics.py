import dagster as dg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from dagster_duckdb import DuckDBResource


@dg.asset(
    deps=[
        dg.AssetKey(["daily_metrics"]),
    ],
    kinds={"duckdb"},
)
def manhattan_stats(database: DuckDBResource) -> dg.MaterializeResult:
    query = """
        select count(*)
        from daily_metrics
    """

    with database.get_connection() as conn:
        count = conn.execute(query).fetchone()[0]
        return dg.MaterializeResult(metadata={"table_count": dg.MetadataValue.int(count)})