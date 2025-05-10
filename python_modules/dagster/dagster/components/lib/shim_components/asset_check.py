import textwrap
from typing import Optional

from pydantic import BaseModel

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.decorators.asset_check_decorator import asset_check
from dagster.components.lib.shim_components.base import ShimScaffolder, scaffold_text
from dagster.components.scaffold.scaffold import ScaffoldRequest, scaffold_with


class AssetCheckScaffoldParams(BaseModel):
    """Parameters for the AssetCheckScaffolder."""

    asset_key: str


class AssetCheckScaffolder(ShimScaffolder[AssetCheckScaffoldParams]):
    @classmethod
    def get_scaffold_params(cls) -> type[AssetCheckScaffoldParams]:
        return AssetCheckScaffoldParams

    def get_text(self, filename: str, params: Optional[AssetCheckScaffoldParams]) -> str:
        """Get the text for an asset check.

        Args:
            filename: The name of the file to generate
            params: The parameters for the asset check, which will be validated against AssetCheckScaffoldParams

        Returns:
            The text for the asset check
        """
        assert params
        asset_key = AssetKey.from_user_string(params.asset_key)
        return textwrap.dedent(
            f"""\
            import dagster as dg


            @dg.asset_check(asset=dg.AssetKey({asset_key.path!s}))
            def {filename}(context: dg.AssetCheckExecutionContext) -> dg.AssetCheckResult: ...
            """
        )

    def scaffold(self, request: ScaffoldRequest[AssetCheckScaffoldParams]) -> None:
        return scaffold_text(self, request)


scaffold_with(AssetCheckScaffolder)(asset_check)
