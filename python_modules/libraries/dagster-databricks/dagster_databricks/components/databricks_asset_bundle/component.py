import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Annotated, Optional, Union

from dagster import (
    AssetExecutionContext,
    AssetSpec,
    MetadataValue,
    Resolvable,
    ResolvedAssetSpec,
    multi_asset,
)
from dagster._annotations import preview, public
from dagster._core.definitions.definitions_class import Definitions
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext
from dagster.components.resolved.core_models import OpSpec, ResolutionContext
from dagster.components.resolved.model import Resolver
from dagster.components.scaffold.scaffold import scaffold_with

from dagster_databricks.components.databricks_asset_bundle.configs import (
    DATABRICKS_UNKNOWN_TASK_TYPE,
    DatabricksBaseTask,
    DatabricksConfig,
    DatabricksUnknownTask,
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
    compute_config: Annotated[
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
                "databricks_asset_bundle.configs.ResolvedDatabricksServerlessConfig."
            ),
            examples=[
                {
                    "spark_version": "some_spark_version",
                    "node_type_id": "some_node_type_id",
                    "num_workers": 1,
                },
                {
                    "existing_cluster_id": "some_existing_cluster_id",
                },
                {
                    "is_serverless": True,
                },
            ],
        ),
    ] = field(default_factory=ResolvedDatabricksServerlessConfig)
    op: Annotated[
        Optional[OpSpec],
        Resolver.default(
            description="Op related arguments to set on the generated @multi_asset",
            examples=[
                {
                    "name": "some_op",
                    "tags": {"some_tag": "some_value"},
                    "description": "some_description",
                    "pool": "some_pool",
                    "backfill_policy": {"type": "single_run"},
                },
            ],
        ),
    ] = None
    assets_by_task_key: Optional[dict[str, list[ResolvedAssetSpec]]] = None

    @cached_property
    def databricks_config(self) -> DatabricksConfig:
        return DatabricksConfig(databricks_config_path=self.databricks_config_path)

    @cached_property
    def asset_specs_by_task_key(self) -> dict[str, list[AssetSpec]]:
        tasks_by_task_key = self.databricks_config.tasks_by_task_key
        default_asset_specs_by_task_key = {
            task_key: self.get_asset_spec(task=task) for task_key, task in tasks_by_task_key.items()
        }

        provided_asset_specs_by_task_key = self.assets_by_task_key or {}

        provided_task_keys = provided_asset_specs_by_task_key.keys()
        missing_task_keys = tasks_by_task_key.keys() - provided_task_keys

        missing_asset_specs_by_task_key = {
            task_key: [asset_spec]
            for task_key, asset_spec in default_asset_specs_by_task_key.items()
            if task_key in missing_task_keys
        }

        updated_provided_asset_specs = defaultdict(list)
        for task_key, asset_specs in provided_asset_specs_by_task_key.items():
            for asset_spec in asset_specs:
                curr_spec = asset_spec
                # replace with default attributes
                if not curr_spec.description:
                    curr_spec = curr_spec.replace_attributes(
                        description=default_asset_specs_by_task_key[task_key].description
                    )
                # merge default attributes
                curr_spec = curr_spec.merge_attributes(
                    metadata=default_asset_specs_by_task_key[task_key].metadata,
                    kinds=default_asset_specs_by_task_key[task_key].kinds,
                )
                updated_provided_asset_specs[task_key].append(curr_spec)

        return {**missing_asset_specs_by_task_key, **updated_provided_asset_specs}

    @public
    def get_asset_spec(self, task: DatabricksBaseTask) -> AssetSpec:
        """Generates an AssetSpec for a given Databricks task.

        This method can be overridden in a subclass to customize how Databricks Asset Bundle
        tasks are converted to Dagster asset specs. By default, it creates an asset spec with
        metadata about the task type, configuration, and dependencies.

        Args:
            task: The DatabricksBaseTask containing information about the Databricks job task

        Returns:
            An AssetSpec that represents the Databricks task as a Dagster asset

        Example:
            Override this method to add custom tags or modify the asset key:

            .. code-block:: python

                from dagster_databricks import DatabricksAssetBundleComponent
                from dagster import AssetSpec

                class CustomDatabricksAssetBundleComponent(DatabricksAssetBundleComponent):
                    def get_asset_spec(self, task):
                        base_spec = super().get_asset_spec(task)
                        return base_spec.replace_attributes(
                            tags={
                                **base_spec.tags,
                                "job_name": task.job_name,
                                "environment": "production"
                            }
                        )
        """
        return AssetSpec(
            key=snake_case(task.task_key),
            description=f"{task.task_key} task from {task.job_name} job",
            kinds={
                "databricks",
                *([task.task_type] if task.task_type is not DATABRICKS_UNKNOWN_TASK_TYPE else []),
            },
            skippable=True,
            metadata={
                "task_key": MetadataValue.text(task.task_key),
                "task_type": MetadataValue.text(task.task_type),
                **(
                    {"task_config": MetadataValue.json(task.task_config_metadata)}
                    if task.task_config_metadata
                    else {}
                ),
                **({"libraries": MetadataValue.json(task.libraries)} if task.libraries else {}),
            },
            deps=[
                self.get_asset_spec(
                    task=DatabricksUnknownTask.from_job_task_config(
                        {"task_key": dep_config.task_key}
                    )
                ).key
                for dep_config in task.depends_on
            ],
        )

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        component_defs_path_as_python_str = str(
            os.path.relpath(context.component_path.file_path, start=context.project_root)
        ).replace("/", "_")

        databricks_assets = []
        for task_key, asset_specs in self.asset_specs_by_task_key.items():

            @multi_asset(
                name=self.op.name
                if self.op and self.op.name
                else f"databricks_{task_key}_multi_asset_{component_defs_path_as_python_str}",
                specs=asset_specs,
                can_subset=False,
                op_tags=self.op.tags if self.op else None,
                description=self.op.description if self.op else None,
                pool=self.op.pool if self.op else None,
                backfill_policy=self.op.backfill_policy if self.op else None,
            )
            def _databricks_task_multi_asset(
                context: AssetExecutionContext,
                databricks: DatabricksWorkspace,
            ):
                """Multi-asset that runs multiple assets of a task as a single Databricks job."""
                yield from databricks.submit_and_poll(
                    component=self,
                    context=context,
                )

            databricks_assets.append(_databricks_task_multi_asset)

        return Definitions(assets=databricks_assets, resources={"databricks": self.workspace})
