import textwrap
from typing import Any, Optional

from pydantic import BaseModel

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.decorators.asset_check_decorator import asset_check
from dagster.components.lib.shim_components.base import ShimScaffolder
from dagster.components.scaffold.scaffold import scaffold_with


class AssetCheckScaffoldParams(BaseModel):
    asset_key: Optional[str] = None


class AssetCheckScaffolder(ShimScaffolder):
    @classmethod
    def get_scaffold_params(cls) -> Optional[type[BaseModel]]:
        return AssetCheckScaffoldParams

    def get_text(self, filename: str, params: Any) -> str:
        asset_key_input = params.asset_key if isinstance(params, AssetCheckScaffoldParams) else None
        asset_key = AssetKey.from_user_string(asset_key_input) if asset_key_input else None
        if asset_key:
            return textwrap.dedent(
                f"""\
                import dagster as dg


                @dg.asset_check(asset=dg.AssetKey({asset_key.path!s}))
                def {filename}(context: dg.AssetCheckExecutionContext) -> dg.AssetCheckResult: ...
                """
            )
        else:
            return textwrap.dedent(
                f"""\
                # import dagster as dg
                #
                #
                # @dg.asset_check(asset=...)
                # def {filename}(context: dg.AssetCheckExecutionContext) -> dg.AssetCheckResult: ...
                """
            )


scaffold_with(AssetCheckScaffolder)(asset_check)
