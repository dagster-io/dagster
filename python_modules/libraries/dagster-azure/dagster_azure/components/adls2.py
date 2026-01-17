"""Azure Data Lake Storage Gen2 Resource Component for dagster-dg."""

from typing import Optional, Union

import dagster as dg
from dagster.components import Component, Model
from dagster._annotations import public, preview
from pydantic import Field

from dagster_azure.adls2.resources import (
    ADLS2DefaultAzureCredential,
    ADLS2Key,
    ADLS2Resource,
    ADLS2SASToken,
)


@public
@preview
class ADLS2ResourceComponent(Component, dg.Resolvable, Model):
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
                token: ${ADLS2_SAS_TOKEN}
              resource_key: adls2
    """

    storage_account: str = Field(
        description="The storage account name.",
    )

    credential: Union[ADLS2SASToken, ADLS2Key, ADLS2DefaultAzureCredential] = Field(
        discriminator="credential_type",
        description="The credentials with which to authenticate.",
    )

    resource_key: Optional[str] = Field(
        default=None, description="Resource key for binding to definitions."
    )

    @property
    def resource(self) -> ADLS2Resource:
        """Return the underlying ADLS2Resource."""
        return ADLS2Resource(
            storage_account=self.storage_account,
            credential=self.credential,
        )

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        if self.resource_key is None:
            return dg.Definitions()
        return dg.Definitions(resources={self.resource_key: self.resource})
