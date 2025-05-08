import textwrap
from typing import Optional

from pydantic import BaseModel

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.decorators.asset_check_decorator import asset_check
from dagster.components.lib.shim_components.base import ShimScaffolder, scaffold_text
from dagster.components.scaffold.scaffold import ScaffoldRequest, scaffold_with


class AssetCheckScaffoldParams(BaseModel):
    asset_key: Optional[str] = None


class AssetCheckScaffolder(ShimScaffolder[AssetCheckScaffoldParams]):
    @classmethod
    def get_scaffold_params(cls) -> type[AssetCheckScaffoldParams]:
        return AssetCheckScaffoldParams

    def scaffold_with_params(
        self, request: ScaffoldRequest, params: AssetCheckScaffoldParams
    ) -> None:
        return scaffold_text(self, request, params)

    def get_text(self, filename: str, params: Optional[AssetCheckScaffoldParams]) -> str:
        assert params is not None
        asset_key_input = params.asset_key
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
