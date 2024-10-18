import dagster as dg
from dagster_duckdb import DuckDBResource

defs = dg.Definitions(
    resources={"duckdb": DuckDBResource(database="data/mydb.duckdb")},
)
