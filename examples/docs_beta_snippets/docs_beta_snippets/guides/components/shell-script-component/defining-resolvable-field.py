from typing import Annotated, Optional

from dagster_components import ComponentSchemaBaseModel, ResolvableFieldInfo
from dagster_components.core.schema.objects import AssetAttributesModel, OpSpecBaseModel


class ScriptRunner: ...


class ShellScriptSchema(ComponentSchemaBaseModel):
    script_path: str
    asset_attributes: AssetAttributesModel
    # highlight-start
    script_runner: Annotated[
        str,
        ResolvableFieldInfo(
            output_type=ScriptRunner, additional_scope={"get_script_runner"}
        ),
    ]
    # highlight-end
    op: Optional[OpSpecBaseModel] = None
