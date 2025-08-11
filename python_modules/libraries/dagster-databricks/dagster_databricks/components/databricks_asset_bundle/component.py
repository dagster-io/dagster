import re
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Annotated

from dagster import AssetSpec, MetadataValue, Resolvable
from dagster._core.definitions.definitions_class import Definitions
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext
from dagster.components.resolved.core_models import ResolutionContext
from dagster.components.resolved.model import Resolver
from dagster.components.scaffold.scaffold import scaffold_with

from dagster_databricks.components.databricks_asset_bundle.configs import (
    DatabricksBaseTask,
    DatabricksConfig,
)
from dagster_databricks.components.databricks_asset_bundle.scaffolder import (
    DatabricksAssetBundleScaffolder,
)


def snake_case(name: str) -> str:
    """Convert a string to snake_case."""
    # Remove file extension if present
    name = Path(name).stem
    # Replace special characters and spaces with underscores
    name = re.sub(r"[^a-zA-Z0-9]+", "_", name)
    # Convert CamelCase to snake_case
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    return name.lower().strip("_")


def resolve_databricks_config_path(context: ResolutionContext, model) -> Path:
    return context.resolve_source_relative_path(
        context.resolve_value(model, as_type=str),
    )


@scaffold_with(DatabricksAssetBundleScaffolder)
@dataclass
class DatabricksAssetBundleComponent(Component, Resolvable):
    databricks_config_path: Annotated[
        Path,
        Resolver(
            resolve_databricks_config_path,
            model_field_type=str,
            description="The path to the databricks.yml config file.",
            examples=[
                "{{ project_root }}/path/to/databricks_yml_config_file",
            ],
        ),
    ]

    @cached_property
    def databricks_config(self) -> DatabricksConfig:
        return DatabricksConfig(databricks_config_path=self.databricks_config_path)

    def get_asset_spec(self, task: DatabricksBaseTask) -> AssetSpec:
        return AssetSpec(
            key=snake_case(task.task_key),
            description=f"{task.task_key} task from {task.job_name} job",
            kinds={"databricks", task.task_type},
            skippable=True,
            metadata={
                "task_key": MetadataValue.text(task.task_key),
                "task_type": MetadataValue.text(task.task_type),
                "task_config": MetadataValue.json(task.task_config_metadata),
                **({"libraries": MetadataValue.json(task.libraries)} if task.libraries else {}),
            },
            deps=[snake_case(dep_task_key) for dep_task_key in task.depends_on],
        )

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        raise NotImplementedError()
