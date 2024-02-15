import os

from dagster import Definitions, EnvVar, file_relative_path
from dagster_embedded_elt.sling import DagsterSlingTranslator, sling_assets
from dagster_embedded_elt.sling.resources import SlingConnectionResource, SlingResource

replication_config = file_relative_path(__file__, "sling_replication.yaml")
os.environ["POSTGRES_URL"] = "postgres://postgres:postgres@localhost:5432/finance?sslmode=disable"
sling_resource = SlingResource(
    connections=[
        SlingConnectionResource(
            name="MY_POSTGRES", type="postgres", connection_string=EnvVar("POSTGRES_URL")
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
    for lines in sling.replicate(
        replication_config=replication_config,
        dagster_sling_translator=DagsterSlingTranslator(),
        debug=True,
    ):
        context.log.info(lines)


defs = Definitions(
    assets=[my_assets],
    resources={"sling": sling_resource},
)
