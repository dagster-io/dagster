from typing import Annotated, Optional

from dagster_components import ResolvableFieldInfo
from dagster_components.core.schema.objects import AssetAttributesModel, OpSpecModel
from pydantic import BaseModel


class ShellScriptSchema(BaseModel):
    script_path: str
    asset_attributes: AssetAttributesModel
    # highlight-start
    script_runner: Annotated[
        str, ResolvableFieldInfo(required_scope={"get_script_runner"})
    ]
    # highlight-end
    op: Optional[OpSpecModel] = None
