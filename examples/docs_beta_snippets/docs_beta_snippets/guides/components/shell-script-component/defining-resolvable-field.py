from typing import Annotated, Optional

from dagster_components import SchemaFieldInfo
from dagster_components.core.schema.objects import AssetAttributesSchema, OpSpecSchema
from pydantic import BaseModel


class ShellScriptSchema(BaseModel):
    script_path: str
    asset_attributes: AssetAttributesSchema
    # highlight-start
    script_runner: Annotated[str, SchemaFieldInfo(required_scope={"get_script_runner"})]
    # highlight-end
    op: Optional[OpSpecSchema] = None
