from dagster_sigma import SigmaBaseUrl, SigmaOrganization, load_sigma_asset_specs

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

sales_team_specs = load_sigma_asset_specs(sales_team_organization)
marketing_team_specs = load_sigma_asset_specs(marketing_team_organization)

# Merge the specs into a single set of definitions
defs = dg.Definitions(
    assets=[*sales_team_specs, *marketing_team_specs],
    resources={
        "marketing_sigma": marketing_team_organization,
        "sales_sigma": sales_team_organization,
    },
)
