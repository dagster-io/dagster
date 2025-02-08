from typing import Annotated, Optional

from dagster_components import ResolvableFieldInfo
from dagster_components.core.schema.objects import AssetAttributesSchema, OpSpecSchema
from pydantic import BaseModel


class ShellScriptSchema(BaseModel):
    script_path: str
    asset_attributes: AssetAttributesSchema
    # highlight-start
    script_runner: Annotated[
        str, ResolvableFieldInfo(required_scope={"get_script_runner"})
    ]
    # highlight-end
    op: Optional[OpSpecSchema] = None
