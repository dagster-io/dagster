from pathlib import Path

from dagster._utils import pushd

from dagster_components import Scaffolder, ScaffoldRequest
from dagster_components.components.shim_components.base import ShimComponent
from dagster_components.scaffoldable.decorator import scaffoldable


class AssetScaffolder(Scaffolder):
    def scaffold(self, request: ScaffoldRequest, params: None) -> None:
        with pushd(str(request.target_path)):
            Path("definitions.py").write_text("""
# import dagster as dg
# 
# @dg.asset
# def my_asset(context: dg.AssetExecutionContext) -> dg.MaterializeResult: ...
""")


@scaffoldable(AssetScaffolder)
class RawAssetComponent(ShimComponent):
    """Asset definition component."""
