from dagster_sigma import (
    SigmaBaseUrl,
    SigmaFilter,
    SigmaOrganization,
    load_sigma_asset_specs,
)

import dagster as dg

sigma_organization = SigmaOrganization(
    base_url=SigmaBaseUrl.AWS_US,
    client_id=dg.EnvVar("SIGMA_CLIENT_ID"),
    client_secret=dg.EnvVar("SIGMA_CLIENT_SECRET"),
)

sigma_specs = load_sigma_asset_specs(
    organization=sigma_organization,
    sigma_filter=SigmaFilter(
        workbook_folders=[
            ["my_folder", "my_subfolder"],
            ["my_folder", "my_other_subfolder"],
        ]
    ),
)
defs = dg.Definitions(assets=[*sigma_specs], resources={"sigma": sigma_organization})
