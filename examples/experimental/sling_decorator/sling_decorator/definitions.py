from dagster import Definitions, file_relative_path
from dagster_embedded_elt.sling import sling_assets
from dagster_embedded_elt.sling.resources import SlingConnectionResource, SlingResource

replication_config = file_relative_path(__file__, "../sling_replication.yaml")

sling_resource = SlingResource(
    connections=[
        SlingConnectionResource(
            name="MY_POSTGRES",
            type="postgres",
            connection_string="postgres://postgres:postgres@localhost:54321/finance?sslmode=disable",
        ),
        SlingConnectionResource(
            name="MY_DUCKDB",
            type="duckdb",
            connection_string="duckdb:///var/tmp/duckdb.db",
        ),
    ]
)


@sling_assets(replication_config=replication_config)
def my_assets(context, sling: SlingResource):
    yield from sling.replicate(context=context).fetch_column_metadata()
    for row in sling.stream_raw_logs():
        context.log.info(row)


defs = Definitions(
    assets=[
        my_assets,
    ],
    resources={
        "sling": sling_resource,
    },
)
