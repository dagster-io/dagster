from dagster_sigma import (
    DagsterSigmaTranslator,
    SigmaBaseUrl,
    SigmaOrganization,
    SigmaWorkbook,
)

from dagster import AssetSpec, EnvVar

resource = SigmaOrganization(
    base_url=SigmaBaseUrl.AWS_US,
    client_id=EnvVar("SIGMA_CLIENT_ID"),
    client_secret=EnvVar("SIGMA_CLIENT_SECRET"),
)


# A translator class lets us customize properties of the built
# Sigma assets, such as the owners or asset key
class MyCustomSigmaTranslator(DagsterSigmaTranslator):
    def get_workbook_spec(self, data: SigmaWorkbook) -> AssetSpec:
        # We add a custom team owner tag to all reports
        return super().get_workbook_spec(data)._replace(owners=["my_team"])


defs = resource.build_defs(dagster_sigma_translator=MyCustomSigmaTranslator)
