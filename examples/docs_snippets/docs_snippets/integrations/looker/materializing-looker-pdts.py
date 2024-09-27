from dagster_looker import LookerResource, RequestStartPdtBuild

from dagster import EnvVar

resource = LookerResource(
    client_id=EnvVar("LOOKERSDK_CLIENT_ID"),
    client_secret=EnvVar("LOOKERSDK_CLIENT_SECRET"),
    base_url=EnvVar("LOOKERSDK_HOST_URL"),
)

defs = resource.build_defs(
    request_start_pdt_builds=[
        RequestStartPdtBuild(
            model_name="analytics",
            view_name="page_keyword_performance",
        ),
    ]
)
