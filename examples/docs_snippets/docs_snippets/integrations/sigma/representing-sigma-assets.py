from dagster_sigma import SigmaBaseUrl, SigmaOrganization

from dagster import EnvVar

resource = SigmaOrganization(
    base_url=SigmaBaseUrl.AWS_US,
    client_id=EnvVar("SIGMA_CLIENT_ID"),
    client_secret=EnvVar("SIGMA_CLIENT_SECRET"),
)


defs = resource.build_defs()
