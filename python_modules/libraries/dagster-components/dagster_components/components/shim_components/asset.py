from dagster_components.blueprint import scaffold_with
from dagster_components.components.shim_components.base import ShimBlueprint, ShimComponent


class AssetBlueprint(ShimBlueprint):
    def get_text(self) -> str:
        return """# import dagster as dg
# 
#
# @dg.asset
# def my_asset(context: dg.AssetExecutionContext) -> dg.MaterializeResult: ...
"""


@scaffold_with(AssetBlueprint)
class RawAssetComponent(ShimComponent):
    """Asset definition component."""
