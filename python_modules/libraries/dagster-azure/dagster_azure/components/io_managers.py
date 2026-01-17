"""Azure Data Lake Storage Gen2 IO Manager Component for dagster-dg."""

from typing import Optional

import dagster as dg
from dagster import ResourceDependency
from dagster.components import Component, Model
from dagster._annotations import public, preview
from pydantic import Field

from dagster_azure.adls2.io_manager import ADLS2PickleIOManager
from dagster_azure.adls2.resources import ADLS2Resource


@public
@preview
class ADLS2PickleIOManagerComponent(Component, dg.Resolvable, Model):
    """Component for ADLS2 Pickle IO Manager.

    Wraps ADLS2PickleIOManager for use in YAML-based configuration.

    Example usage in YAML:

    .. code-block:: YAML

        resources:
          - name: io_manager
            type: dagster_azure.ADLS2PickleIOManagerComponent
            attributes:
              adls2_file_system: my-cool-fs
              adls2_prefix: my-cool-prefix
              adls2: ${adls2_resource}
              resource_key: io_manager
    """

    adls2: ResourceDependency[ADLS2Resource] = Field(
        description="The ADLS2 resource to use for IO management.",
    )

    adls2_file_system: str = Field(
        description="ADLS Gen2 file system name.",
    )

    adls2_prefix: str = Field(
        default="dagster",
        description="ADLS Gen2 file system prefix to write to.",
    )

    lease_duration: int = Field(
        default=60,
        description="Lease duration in seconds. Must be between 15 and 60 seconds or -1 for infinite.",
    )

    resource_key: Optional[str] = Field(
        default=None, description="Resource key for binding to definitions."
    )

    @property
    def resource(self) -> ADLS2PickleIOManager:
        """Return the underlying ADLS2PickleIOManager."""
        return ADLS2PickleIOManager(
            adls2=self.adls2,
            adls2_file_system=self.adls2_file_system,
            adls2_prefix=self.adls2_prefix,
            lease_duration=self.lease_duration,
        )

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        if self.resource_key is None:
            return dg.Definitions()
        return dg.Definitions(resources={self.resource_key: self.resource})
