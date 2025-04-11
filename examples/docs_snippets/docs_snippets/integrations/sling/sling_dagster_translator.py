# start_sling_assets
from dagster_sling import SlingResource, sling_assets

from dagster import Definitions, file_relative_path

replication_config = file_relative_path(__file__, "../sling_replication.yaml")
sling_resource = SlingResource(connections=[...])  # Add connections here


@sling_assets(replication_config=replication_config)
def my_assets(context, sling: SlingResource):
    yield from sling.replicate(context=context)
    for row in sling.stream_raw_logs():
        context.log.info(row)


# end_sling_assets


# start_sling_defs
defs = Definitions(
    assets=[
        my_assets,
    ],
    resources={
        "sling": sling_resource,
    },
)
# end_sling_defs
