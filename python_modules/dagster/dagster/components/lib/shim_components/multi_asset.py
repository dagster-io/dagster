import textwrap
from typing import Any, Optional

from pydantic import BaseModel, Field

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster.components.lib.shim_components.base import ShimScaffolder
from dagster.components.scaffold.scaffold import scaffold_with


class MultiAssetScaffoldParams(BaseModel):
    asset_key: Optional[list[str]] = Field(
        default=None, description="Optional list of asset keys to use in specs"
    )


class MultiAssetScaffolder(ShimScaffolder):
    @classmethod
    def get_scaffold_params(cls) -> Optional[type[BaseModel]]:
        return MultiAssetScaffoldParams

    def get_text(self, filename: str, params: Any) -> str:
        asset_keys = (
            params.asset_key
            if isinstance(params, MultiAssetScaffoldParams) and params.asset_key
            # Default to two sample assets based on the filename
            else [
                f"{filename}/first_asset",
                f"{filename}/second_asset",
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
            def {filename}(context: dg.AssetExecutionContext):
                ...
            """
        )


scaffold_with(MultiAssetScaffolder)(multi_asset)
