import dagster as dg
from . import assets, resources, schedules, jobs

all_assets = dg.load_assets_from_modules([assets])
external_assets = [assets.goodreads]

defs = dg.Definitions(
    assets=all_assets + external_assets,
    resources={
        "duckdb_resource": resources.duckdb_resouce,
        "pinecone_resource": resources.pinecone_resource,
    },
    jobs=[jobs.goodreads_pinecone],
    schedules=[schedules.goodreads_pinecone_schedule],
)
