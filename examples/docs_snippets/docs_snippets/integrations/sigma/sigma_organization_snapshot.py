from dagster_sigma import SigmaBaseUrl, SigmaOrganization, load_sigma_asset_specs

import dagster as dg

sigma_organization = SigmaOrganization(
    base_url=SigmaBaseUrl.AWS_US,
    client_id=dg.EnvVar("SIGMA_CLIENT_ID"),
    client_secret=dg.EnvVar("SIGMA_CLIENT_SECRET"),
)

sigma_specs = load_sigma_asset_specs(
    organization=sigma_organization, snapshot_path=dg.EnvVar("SIGMA_SNAPSHOT_PATH")
)

defs = dg.Definitions(assets=[*sigma_specs], resources={"sigma": sigma_organization})
