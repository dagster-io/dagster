from dagster import Definitions, file_relative_path
from dagster_embedded_elt.sling import DagsterSlingTranslator, sling_assets
from dagster_embedded_elt.sling.resources import SlingConnectionResource, SlingResource

replication_config = file_relative_path(__file__, "sling_replication.yaml")


@sling_assets(replication_config=replication_config)
def my_assets(sling: SlingResource):
    yield from sling.replicate(
        replication_config=replication_config,
        dagster_sling_translator=DagsterSlingTranslator(),
    )


sling_resource = SlingResource(
    connections=[
        SlingConnectionResource(
            name="LOCAL_DUCKDB",
            type="duckdb",
            connection_string="duckdb://local.duckdb",
            duckdb_version="0.9.2",
        ),
        SlingConnectionResource(
            name="AWS_S3",
            type="s3",
            bucket="your-bucket-name",
            access_key_id="your-access-key-id",
            secret_access_key="your-secret-access-key",
        ),
    ]
)

defs = Definitions(
    assets=[my_assets],
    resources={
        "sling": sling_resource,
    },
)
