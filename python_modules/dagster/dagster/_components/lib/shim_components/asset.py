from dagster import asset
from dagster._components.lib.shim_components.base import ShimScaffolder
from dagster._components.scaffold.scaffold import scaffold_with


class AssetScaffolder(ShimScaffolder):
    def get_text(self, filename: str) -> str:
        return f"""# import dagster as dg
# 
#
# @dg.asset
# def {filename}(context: dg.AssetExecutionContext) -> dg.MaterializeResult: ...

"""


scaffold_with(AssetScaffolder)(asset)
