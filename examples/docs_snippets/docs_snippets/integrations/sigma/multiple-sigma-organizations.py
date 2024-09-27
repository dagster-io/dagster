from dagster_sigma import SigmaBaseUrl, SigmaOrganization

from dagster import Definitions, EnvVar

sales_team_organization = SigmaOrganization(
    base_url=SigmaBaseUrl.AWS_US,
    client_id=EnvVar("SALES_SIGMA_CLIENT_ID"),
    client_secret=EnvVar("SALES_SIGMA_CLIENT_SECRET"),
)

marketing_team_organization = SigmaOrganization(
    base_url=SigmaBaseUrl.AWS_US,
    client_id=EnvVar("MARKETING_SIGMA_CLIENT_ID"),
    client_secret=EnvVar("MARKETING_SIGMA_CLIENT_SECRET"),
)
defs = Definitions.merge(
    sales_team_organization.build_defs(),
    marketing_team_organization.build_defs(),
)
