import textwrap
from typing import Optional

from pydantic import BaseModel

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster.components.lib.shim_components.base import ShimScaffolder
from dagster.components.scaffold.scaffold import ScaffoldRequest, scaffold_with


class MultiAssetScaffoldParams(BaseModel):
    asset_key: Optional[list[str]] = None


class MultiAssetScaffolder(ShimScaffolder[MultiAssetScaffoldParams]):
    @classmethod
    def get_scaffold_params(cls) -> type[MultiAssetScaffoldParams]:
        return MultiAssetScaffoldParams

    def get_text(self, request: ScaffoldRequest[MultiAssetScaffoldParams]) -> str:
        asset_keys = (
            request.params.asset_key
            if request.params and request.params.asset_key
            # Default to two sample assets based on the filename
            else [
                f"{request.target_path.stem}/first_asset",
                f"{request.target_path.stem}/second_asset",
            ]
        )

        specs_str = textwrap.indent(
            ",\n".join(
                f"dg.AssetSpec(key=dg.AssetKey({AssetKey.from_user_string(key).path!r}))"
                for key in asset_keys
            ),
            prefix=" " * 20,
        )
        return textwrap.dedent(
            f"""\
            import dagster as dg


            @dg.multi_asset(
                specs=[
{specs_str}
                ]
            )
            def {request.target_path.stem}(context: dg.AssetExecutionContext):
                ...
            """
        )


scaffold_with(MultiAssetScaffolder)(multi_asset)
