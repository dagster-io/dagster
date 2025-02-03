from typing import Optional

from dagster_components import (
    Component,
    ComponentLoadContext,
    registered_component_type,
)
from dagster_components.core.schema.objects import AssetAttributesModel, OpSpecModel
from pydantic import BaseModel

from dagster import Definitions


# highlight-start
class ShellScriptSchema(BaseModel):
    script_path: str
    asset_attributes: AssetAttributesModel
    op: Optional[OpSpecModel] = None
    # highlight-end


@registered_component_type(name="shell_command")
class ShellCommand(Component):
    @classmethod
    def get_schema(cls) -> type[ShellScriptSchema]:
        # higlight-start
        return ShellScriptSchema
        # highlight-end

    def build_defs(self, load_context: ComponentLoadContext) -> Definitions: ...
