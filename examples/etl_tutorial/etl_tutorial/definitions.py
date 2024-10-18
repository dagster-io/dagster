import json
import os

from dagster_duckdb import DuckDBResource

import dagster as dg


defs = dg.Definitions(
    resources={"duckdb": DuckDBResource(database="data/mydb.duckdb")},
)
