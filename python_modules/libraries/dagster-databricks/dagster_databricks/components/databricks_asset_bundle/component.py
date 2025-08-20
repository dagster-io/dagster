import os
import re
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Annotated

from dagster import AssetExecutionContext, AssetSpec, MetadataValue, Resolvable, multi_asset
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
from dagster_databricks.components.databricks_asset_bundle.resource import DatabricksWorkspace
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


@dataclass
class DatabricksWorkspaceArgs(Resolvable):
    """Aligns with DatabricksWorkspace.__new__."""

    host: str
    token: str


def resolve_databricks_config_path(context: ResolutionContext, model) -> Path:
    return context.resolve_source_relative_path(
        context.resolve_value(model, as_type=str),
    )


def resolve_databricks_workspace(context: ResolutionContext, model) -> DatabricksWorkspace:
    args = DatabricksWorkspaceArgs.resolve_from_model(context, model)
    return DatabricksWorkspace(
        host=args.host,
        token=args.token,
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
    workspace: Annotated[
        DatabricksWorkspace,
        Resolver(
            resolve_databricks_workspace,
            model_field_type=DatabricksWorkspaceArgs.model(),
            description="The mapping defining a DatabricksWorkspace.",
            examples=[
                {
                    "host": "your_host",
                    "token": "your_token",
                },
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
        component_defs_path_as_python_str = str(
            os.path.relpath(context.component_path.file_path, start=context.project_root)
        ).replace("/", "_")

        @multi_asset(
            name=f"databricks_multi_asset_{component_defs_path_as_python_str}",
            specs=[self.get_asset_spec(task) for task in self.databricks_config.tasks],
            can_subset=True,
        )
        def multi_notebook_job_asset(
            context: AssetExecutionContext,
        ): ...

        return Definitions(assets=[multi_notebook_job_asset])
