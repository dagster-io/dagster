from dagster._core.definitions.decorators.asset_decorator import asset
from dagster.components.lib.shim_components.base import ShimScaffolder
from dagster.components.scaffold.scaffold import scaffold_with


class AssetScaffolder(ShimScaffolder):
    def get_text(self, filename: str) -> str:
        return f"""# import dagster as dg
# 
#
# @dg.asset
# def {filename}(context: dg.AssetExecutionContext) -> dg.MaterializeResult: ...

"""


scaffold_with(AssetScaffolder)(asset)
