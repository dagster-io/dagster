import textwrap

from pydantic import BaseModel

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.decorators.asset_check_decorator import asset_check
from dagster.components.lib.shim_components.base import ShimScaffolder
from dagster.components.scaffold.scaffold import ScaffoldRequest, scaffold_with


class AssetCheckScaffoldParams(BaseModel):
    """Parameters for the AssetCheckScaffolder."""

    asset_key: str


class AssetCheckScaffolder(ShimScaffolder[AssetCheckScaffoldParams]):
    @classmethod
    def get_scaffold_params(cls) -> type[AssetCheckScaffoldParams]:
        return AssetCheckScaffoldParams

    def get_text(self, request: ScaffoldRequest[AssetCheckScaffoldParams]) -> str:
        """Get the text for an asset check.

        Args:
            request: The scaffold request containing type name, target path, format, project root and optional params

        Returns:
            The text for the asset check
        """
        assert request.params
        asset_key = AssetKey.from_user_string(request.params.asset_key)
        return textwrap.dedent(
            f"""\
            import dagster as dg


            @dg.asset_check(asset=dg.AssetKey({asset_key.path!s}))
            def {request.target_path.stem}(context: dg.AssetCheckExecutionContext) -> dg.AssetCheckResult: ...
            """
        )


scaffold_with(AssetCheckScaffolder)(asset_check)
