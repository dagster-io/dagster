from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
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


def resolve_databricks_configs_path(context: ResolutionContext, model) -> Path:
    return context.resolve_source_relative_path(
        context.resolve_value(model, as_type=str),
    )


@scaffold_with(DatabricksAssetBundleScaffolder)
@dataclass
class DatabricksAssetBundleComponent(Component, Resolvable):
    databricks_configs_path: Annotated[
        Path,
        Resolver(
            resolve_databricks_configs_path,
            model_field_type=str,
            description="The path to the databricks.yml config file.",
            examples=[
                "{{ project_root }}/path/to/databricks_yml_config_file",
            ],
        ),
    ]

    @cached_property
    def databricks_configs(self) -> DatabricksConfigs:
        return DatabricksConfigs(databricks_configs_path=self.databricks_configs_path)

    def get_asset_spec(self) -> AssetSpec:
        raise NotImplementedError()

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        raise NotImplementedError()
