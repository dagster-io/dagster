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
        # Filter down to only the workbooks in these folders
        workbook_folders=[
            ("my_folder", "my_subfolder"),
            ("my_folder", "my_other_subfolder"),
        ],
        # Specify whether to include datasets that are not used in any workbooks
        # default is True
        include_unused_datasets=False,
    ),
)
defs = dg.Definitions(assets=[*sigma_specs], resources={"sigma": sigma_organization})
