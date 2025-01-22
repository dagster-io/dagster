from dagster_looker import (
    LookerResource,
    RequestStartPdtBuild,
    build_looker_pdt_assets_definitions,
    load_looker_asset_specs,
)

import dagster as dg

looker_resource = LookerResource(
    client_id=dg.EnvVar("LOOKERSDK_CLIENT_ID"),
    client_secret=dg.EnvVar("LOOKERSDK_CLIENT_SECRET"),
    base_url=dg.EnvVar("LOOKERSDK_HOST_URL"),
)

looker_specs = load_looker_asset_specs(looker_resource=looker_resource)

pdts = build_looker_pdt_assets_definitions(
    resource_key="looker",
    request_start_pdt_builds=[
        RequestStartPdtBuild(model_name="my_model", view_name="my_view")
    ],
)


defs = dg.Definitions(
    assets=[*pdts, *looker_specs],
    resources={"looker": looker_resource},
)
