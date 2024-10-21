from dagster_sigma import SigmaBaseUrl, SigmaOrganization

import dagster as dg

resource = SigmaOrganization(
    base_url=SigmaBaseUrl.AWS_US,
    client_id=dg.EnvVar("SIGMA_CLIENT_ID"),
    client_secret=dg.EnvVar("SIGMA_CLIENT_SECRET"),
)

defs = resource.build_defs()
