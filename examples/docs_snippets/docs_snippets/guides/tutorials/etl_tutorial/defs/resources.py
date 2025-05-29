from dagster_duckdb import DuckDBResource

import dagster as dg

database_resource = DuckDBResource(database="mydb.duckdb")

defs = dg.Definitions(resources={"duckdb": database_resource})
