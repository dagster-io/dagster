from dagster_components.components.shim_components.base import ShimComponent, ShimScaffolder
from dagster_components.scaffold import scaffold_with


class AssetScaffolder(ShimScaffolder):
    def get_text(self) -> str:
        return """# import dagster as dg
# 
#
# @dg.asset
# def my_asset(context: dg.AssetExecutionContext) -> dg.MaterializeResult: ...
"""


@scaffold_with(AssetScaffolder)
class RawAssetComponent(ShimComponent):
    """Asset definition component."""
