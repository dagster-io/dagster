from dataclasses import dataclass

from dagster import AssetSpec, Resolvable
from dagster._core.definitions.definitions_class import Definitions
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext
from dagster.components.scaffold.scaffold import scaffold_with

from dagster_databricks.components.databricks_asset_bundle.scaffolder import (
    DatabricksAssetBundleScaffolder,
)


@scaffold_with(DatabricksAssetBundleScaffolder)
@dataclass
class DatabricksAssetBundleComponent(Component, Resolvable):
    def get_asset_spec(self) -> AssetSpec:
        raise NotImplementedError()

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        raise NotImplementedError()
