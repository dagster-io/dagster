from pathlib import Path

from dagster._utils import pushd

from dagster_components import Blueprint, ScaffoldRequest
from dagster_components.blueprint import scaffold_with
from dagster_components.components.shim_components.base import ShimComponent


class AssetBlueprint(Blueprint):
    def scaffold(self, request: ScaffoldRequest, params: None) -> None:
        with pushd(str(request.target_path)):
            Path("definitions.py").write_text("""# import dagster as dg
# 
#
# @dg.asset
# def my_asset(context: dg.AssetExecutionContext) -> dg.MaterializeResult: ...
""")


@scaffold_with(AssetBlueprint)
class RawAssetComponent(ShimComponent):
    """Asset definition component."""
