from dagster_looker import LookerResource, RequestStartPdtBuild

import dagster as dg

resource = LookerResource(
    client_id=dg.EnvVar("LOOKERSDK_CLIENT_ID"),
    client_secret=dg.EnvVar("LOOKERSDK_CLIENT_SECRET"),
    base_url=dg.EnvVar("LOOKERSDK_HOST_URL"),
)

defs = resource.build_defs(
    request_start_pdt_builds=[
        RequestStartPdtBuild(
            model_name="analytics",
            view_name="page_keyword_performance",
        ),
    ]
)
