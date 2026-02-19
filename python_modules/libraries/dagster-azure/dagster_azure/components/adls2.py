
import dagster as dg
from dagster._annotations import preview, public
from pydantic import Field

from dagster_azure.adls2.resources import (
    ADLS2DefaultAzureCredential,
    ADLS2Key,
    ADLS2Resource,
    ADLS2SASToken,
)


@public
@preview
class ADLS2ResourceComponent(dg.Component, dg.Resolvable, dg.Model):
    """Component for Azure Data Lake Storage Gen2 Resource.

    Wraps ADLS2Resource for use in YAML-based configuration.

    Example usage in YAML:

    .. code-block:: YAML

        resources:
          - name: adls2
            type: dagster_azure.ADLS2ResourceComponent
            attributes:
              storage_account: my_storage_account
              credential:
                credential_type: sas
                token: "{{ env.ADLS2_SAS_TOKEN }}"
              resource_key: adls2
    """

    storage_account: str | None = Field(default=None, description="The storage account name")

    credential: ADLS2SASToken | ADLS2Key | ADLS2DefaultAzureCredential | None = Field(
        default=None,
        description="The credentials with which to authenticate",
    )

    resource_key: str | None = Field(
        default=None, description="Resource key for binding to definitions"
    )

    @property
    def resource(self) -> ADLS2Resource:
        return ADLS2Resource(
            storage_account=self.storage_account,
            credential=self.credential,
        )

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        if self.resource_key is None:
            return dg.Definitions()
        return dg.Definitions(resources={self.resource_key: self.resource})
