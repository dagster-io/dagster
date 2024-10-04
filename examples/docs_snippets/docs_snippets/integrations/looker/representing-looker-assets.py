from dagster_looker import LookerResource

from dagster import EnvVar

resource = LookerResource(
    client_id=EnvVar("LOOKERSDK_CLIENT_ID"),
    client_secret=EnvVar("LOOKERSDK_CLIENT_SECRET"),
    base_url=EnvVar("LOOKERSDK_HOST_URL"),
)

defs = resource.build_defs()
