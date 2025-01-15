import subprocess
from typing import Optional

from dagster_components import (
    Component,
    ComponentLoadContext,
    ComponentSchemaBaseModel,
    component_type,
)
from dagster_components.core.schema.objects import AssetAttributesModel, OpSpecBaseModel

import dagster as dg


# highlight-start
class ShellScriptSchema(ComponentSchemaBaseModel):
    script_path: str
    asset_attributes: AssetAttributesModel
    op: Optional[OpSpecBaseModel] = None
    # highlight-end


@component_type(name="shell_command")
class ShellCommand(Component):
    def __init__(self, params: ShellScriptSchema):
        self.params = params

    @classmethod
    def get_schema(cls) -> type[ShellScriptSchema]:
        # higlight-start
        return ShellScriptSchema
        # highlight-end

    @classmethod
    def load(cls, load_context: ComponentLoadContext) -> "ShellCommand":
        return cls(params=load_context.load_params(cls.get_schema()))

    def build_defs(self, load_context: ComponentLoadContext) -> dg.Definitions:
        resolved_asset_attributes = self.params.asset_attributes.resolve_properties(
            load_context.templated_value_resolver
        )
        resolved_op_properties = (
            self.params.op.resolve_properties(load_context.templated_value_resolver)
            if self.params.op
            else {}
        )

        @dg.asset(**resolved_asset_attributes, **resolved_op_properties)
        def _asset(context: dg.AssetExecutionContext):
            self.evaluate(context)

        return dg.Definitions(assets=[_asset])

    def evaluate(self, context: dg.AssetExecutionContext):
        subprocess.run(["sh", self.params.script_path], check=False)
