from typing import Optional

from dagster_components import (
    Component,
    ComponentLoadContext,
    ComponentSchemaBaseModel,
    component_type,
)
from dagster_components.core.schema.objects import AssetAttributesModel, OpSpecBaseModel

from dagster import Definitions


# highlight-start
class ShellScriptSchema(ComponentSchemaBaseModel):
    script_path: str
    asset_attributes: AssetAttributesModel
    op: Optional[OpSpecBaseModel] = None
    # highlight-end


@component_type(name="shell_command")
class ShellCommand(Component):
    @classmethod
    def get_schema(cls) -> type[ComponentSchemaBaseModel]:
        # higlight-start
        return ShellScriptSchema
        # highlight-end

    def build_defs(self, load_context: ComponentLoadContext) -> Definitions: ...
