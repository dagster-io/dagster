from typing import Any, cast

import dagster as dg
from dagster._annotations import preview, public
from dagster.components import Component, ComponentLoadContext, Model
from pydantic import Field

from dagster_azure.adls2.io_manager import ADLS2PickleIOManager


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
    adls2: str = Field(description="The resource key for the ADLS2 resource.")
    adls2_file_system: str = Field(description="The ADLS2 file system to use.")
    adls2_prefix: str = Field(default="dagster", description="The prefix to use for IO.")

    resource_key: str = Field(
        default="io_manager", description="Resource key for binding to definitions."
    )

    def build_resource(self, context: ComponentLoadContext) -> ADLS2PickleIOManager:
        return ADLS2PickleIOManager(
            adls2=cast("Any", self.adls2),
            adls2_file_system=self.adls2_file_system,
            adls2_prefix=self.adls2_prefix,
        )

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions(resources={self.resource_key: self.build_resource(context)})
