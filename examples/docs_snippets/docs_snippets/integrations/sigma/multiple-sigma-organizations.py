from dagster_sigma import SigmaBaseUrl, SigmaOrganization

import dagster as dg

sales_team_organization = SigmaOrganization(
    base_url=SigmaBaseUrl.AWS_US,
    client_id=dg.EnvVar("SALES_SIGMA_CLIENT_ID"),
    client_secret=dg.EnvVar("SALES_SIGMA_CLIENT_SECRET"),
)

marketing_team_organization = SigmaOrganization(
    base_url=SigmaBaseUrl.AWS_US,
    client_id=dg.EnvVar("MARKETING_SIGMA_CLIENT_ID"),
    client_secret=dg.EnvVar("MARKETING_SIGMA_CLIENT_SECRET"),
)

defs = dg.Definitions.merge(
    sales_team_organization.build_defs(),
    marketing_team_organization.build_defs(),
)
