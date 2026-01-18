from dagster_looker import LookerFilter, LookerResource, load_looker_asset_specs

import dagster as dg

looker_resource = LookerResource(
    client_id=dg.EnvVar("LOOKERSDK_CLIENT_ID"),
    client_secret=dg.EnvVar("LOOKERSDK_CLIENT_SECRET"),
    base_url=dg.EnvVar("LOOKERSDK_HOST_URL"),
)

looker_specs = load_looker_asset_specs(
    looker_resource=looker_resource,
    looker_filter=LookerFilter(
        dashboard_folders=[
            ["my_folder", "my_subfolder"],
            ["my_folder", "my_other_subfolder"],
        ],
        only_fetch_explores_used_in_dashboards=True,
    ),
)
defs = dg.Definitions(assets=[*looker_specs], resources={"looker": looker_resource})
