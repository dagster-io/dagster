import os
import re
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Annotated, Optional, Union

from dagster import AssetExecutionContext, AssetSpec, MetadataValue, Resolvable, multi_asset
from dagster._annotations import preview
from dagster._core.definitions.definitions_class import Definitions
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext
from dagster.components.resolved.core_models import OpSpec, ResolutionContext
from dagster.components.resolved.model import Resolver
from dagster.components.scaffold.scaffold import scaffold_with

from dagster_databricks.components.databricks_asset_bundle.configs import (
    DatabricksConfig,
    DatabricksTaskAssetSpecData,
    ResolvedDatabricksExistingClusterConfig,
    ResolvedDatabricksNewClusterConfig,
    ResolvedDatabricksServerlessConfig,
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


@preview
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
    compute_config: Optional[
        Annotated[
            Union[
                ResolvedDatabricksNewClusterConfig,
                ResolvedDatabricksExistingClusterConfig,
                ResolvedDatabricksServerlessConfig,
            ],
            Resolver.default(
                model_field_type=Union[
                    ResolvedDatabricksNewClusterConfig,
                    ResolvedDatabricksExistingClusterConfig,
                    ResolvedDatabricksServerlessConfig,
                ],
                description=(
                    "A mapping defining a Databricks compute config. "
                    "Allowed types are databricks_asset_bundle.configs.ResolvedDatabricksNewClusterConfig, "
                    "databricks_asset_bundle.configs.ResolvedDatabricksExistingClusterConfig and "
                    "databricks_asset_bundle.configs.ResolvedDatabricksServerlessConfig. Optional."
                ),
                examples=[
                    {
                        "spark_version": "test_spark_version",
                        "node_type_id": "node_type_id",
                        "num_workers": 1,
                    },
                    {
                        "existing_cluster_id": "existing_cluster_id",
                    },
                    {
                        "is_serverless": True,
                    },
                ],
            ),
        ]
    ] = field(default_factory=ResolvedDatabricksNewClusterConfig)
    op: Annotated[
        Optional[OpSpec],
        Resolver.default(
            description="Op related arguments to set on the generated @multi_asset",
            examples=[
                {
                    "name": "some_op",
                },
            ],
        ),
    ] = None

    @cached_property
    def databricks_config(self) -> DatabricksConfig:
        return DatabricksConfig(databricks_config_path=self.databricks_config_path)

    def get_asset_spec(self, data: DatabricksTaskAssetSpecData) -> AssetSpec:
        return AssetSpec(
            key=snake_case(data.task_key),
            description=f"{data.task_key} task from {data.job_name or 'unknown'} job",
            kinds={"databricks", *([data.task_type] if data.task_type else [])},
            skippable=True,
            metadata={
                "task_key": MetadataValue.text(data.task_key),
                **({"task_type": MetadataValue.text(data.task_type)} if data.task_type else {}),
                **(
                    {"task_config": MetadataValue.json(data.task_config_metadata)}
                    if data.task_config_metadata
                    else {}
                ),
                **({"libraries": MetadataValue.json(data.libraries)} if data.libraries else {}),
            },
            deps=[snake_case(dep_config.task_key) for dep_config in data.depends_on or []],
        )

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        component_defs_path_as_python_str = str(
            os.path.relpath(context.component_path.file_path, start=context.project_root)
        ).replace("/", "_")

        @multi_asset(
            name=self.op.name
            if self.op
            else f"databricks_tasks_multi_asset_{component_defs_path_as_python_str}",
            specs=[
                self.get_asset_spec(data=task.to_databricks_task_spec_data())
                for task in self.databricks_config.tasks
            ],
            can_subset=True,
        )
        def databricks_tasks_multi_asset(
            context: AssetExecutionContext,
            databricks: DatabricksWorkspace,
        ):
            """Multi-asset that runs multiple tasks as a single Databricks job."""
            yield from databricks.submit_and_poll(
                component=self,
                context=context,
            )

        return Definitions(
            assets=[databricks_tasks_multi_asset], resources={"databricks": self.workspace}
        )
