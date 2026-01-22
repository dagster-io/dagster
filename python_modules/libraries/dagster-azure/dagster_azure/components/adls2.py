from typing import Any, Literal, Union

import dagster as dg
from dagster._annotations import preview, public
from dagster.components import Component, ComponentLoadContext, Model
from pydantic import Field

from dagster_azure.adls2.resources import (
    ADLS2DefaultAzureCredential,
    ADLS2Key,
    ADLS2Resource,
    ADLS2SASToken,
)


def _resolve(val: str):
    if isinstance(val, str) and val.startswith("{{ env.") and val.endswith(" }}"):
        return dg.EnvVar(val[7:-3].strip())
    return val


class ADLS2SASTokenModel(Model):
    credential_type: Literal["sas"]
    token: str


class ADLS2KeyModel(Model):
    credential_type: Literal["key"]
    storage_account_key: str


class ADLS2DefaultAzureCredentialModel(Model):
    credential_type: Literal["default_azure_credential"]
    kwargs: dict[str, Any] = {}


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
    storage_account: str = Field(description="The storage account name.")

    credential: Union[ADLS2SASTokenModel, ADLS2KeyModel, ADLS2DefaultAzureCredentialModel] = Field(
        description="The credentials with which to authenticate."
    )

    resource_key: str = Field(
        default="adls2", description="Resource key for binding to definitions."
    )

    def build_resource(self, context: ComponentLoadContext) -> ADLS2Resource:
        cred: Any = ADLS2DefaultAzureCredential(kwargs={})

        if self.credential.credential_type == "sas":
            cred = ADLS2SASToken(token=_resolve(self.credential.token))
        elif self.credential.credential_type == "key":
            cred = ADLS2Key(key=_resolve(self.credential.storage_account_key))
        elif self.credential.credential_type == "default_azure_credential":
            cred = ADLS2DefaultAzureCredential(kwargs=self.credential.kwargs)

        return ADLS2Resource(
            storage_account=_resolve(self.storage_account),
            credential=cred,
        )

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions(resources={self.resource_key: self.build_resource(context)})
