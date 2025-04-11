from typing import Union

from dagster_sigma import (
    DagsterSigmaTranslator,
    SigmaBaseUrl,
    SigmaDatasetTranslatorData,
    SigmaOrganization,
    SigmaWorkbookTranslatorData,
    load_sigma_asset_specs,
)

import dagster as dg

sigma_organization = SigmaOrganization(
    base_url=SigmaBaseUrl.AWS_US,
    client_id=dg.EnvVar("SIGMA_CLIENT_ID"),
    client_secret=dg.EnvVar("SIGMA_CLIENT_SECRET"),
)


# start_upstream_asset
class MyCustomSigmaTranslator(DagsterSigmaTranslator):
    def get_asset_spec(
        self, data: Union[SigmaDatasetTranslatorData, SigmaWorkbookTranslatorData]
    ) -> dg.AssetSpec:
        # We create the default asset spec using super()
        default_spec = super().get_asset_spec(data)
        # We customize upstream dependencies for the Sigma workbook named `my_sigma_workbook`
        return default_spec.replace_attributes(
            deps=["my_upstream_asset"]
            if data.properties["name"] == "my_sigma_workbook"
            else ...
        )


sigma_specs = load_sigma_asset_specs(
    sigma_organization, dagster_sigma_translator=MyCustomSigmaTranslator()
)
# end_upstream_asset

defs = dg.Definitions(assets=[*sigma_specs], resources={"sigma": sigma_organization})
