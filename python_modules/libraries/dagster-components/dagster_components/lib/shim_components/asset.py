from dagster import asset

from dagster_components.lib.shim_components.base import ShimScaffolder
from dagster_components.scaffold.scaffold import scaffold_with


class AssetScaffolder(ShimScaffolder):
    def get_text(self, filename: str) -> str:
        return f"""# import dagster as dg
# 
#
# @dg.asset
# def {filename}(context: dg.AssetExecutionContext) -> dg.MaterializeResult: ...

"""


scaffold_with(AssetScaffolder)(asset)
