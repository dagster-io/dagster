from dataclasses import dataclass
from typing import Annotated

from dagster import AssetSpec, Resolvable
from dagster._core.definitions.definitions_class import Definitions
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext
from dagster.components.resolved.core_models import ResolutionContext
from dagster.components.resolved.model import Resolver
from dagster.components.scaffold.scaffold import scaffold_with

from dagster_databricks.components.databricks_asset_bundle.databricks_configs import (
    DatabricksConfigs,
)
from dagster_databricks.components.databricks_asset_bundle.scaffolder import (
    DatabricksAssetBundleScaffolder,
)


def resolve_databricks_configs(context: ResolutionContext, model) -> DatabricksConfigs:
    return DatabricksConfigs(
        context.resolve_source_relative_path(
            context.resolve_value(model, as_type=str),
        )
    )


@scaffold_with(DatabricksAssetBundleScaffolder)
@dataclass
class DatabricksAssetBundleComponent(Component, Resolvable):
    configs: Annotated[
        DatabricksConfigs,
        Resolver(
            resolve_databricks_configs,
            model_field_type=str,
            description="The path to the databricks.yml config file.",
            examples=[
                "{{ project_root }}/path/to/databricks_yml_config_file",
            ],
        ),
    ]

    def get_asset_spec(self) -> AssetSpec:
        raise NotImplementedError()

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        raise NotImplementedError()
