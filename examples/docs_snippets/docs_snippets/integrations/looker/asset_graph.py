from dagster_looker import LookerResource, load_looker_asset_specs

import dagster as dg

looker_resource = LookerResource(
    client_id=dg.EnvVar("LOOKERSDK_CLIENT_ID"),
    client_secret=dg.EnvVar("LOOKERSDK_CLIENT_SECRET"),
    base_url=dg.EnvVar("LOOKERSDK_HOST_URL"),
)

looker_specs = load_looker_asset_specs(looker_resource=looker_resource)
defs = dg.Definitions(assets=[*looker_specs], resources={"looker": looker_resource})
