import os
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Annotated

from dagster import (
    AssetExecutionContext,
    AssetKey,
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
from dagster_databricks.components.shared import (
    DatabricksWorkspaceArgs,
    resolve_databricks_workspace,
)
from dagster_databricks.utils import snake_case


def resolve_databricks_config_path(context: ResolutionContext, model) -> Path:
    return context.resolve_source_relative_path(
        context.resolve_value(model, as_type=str),
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
        ResolvedDatabricksNewClusterConfig
        | ResolvedDatabricksExistingClusterConfig
        | ResolvedDatabricksServerlessConfig,
        Resolver.default(
            model_field_type=ResolvedDatabricksNewClusterConfig
            | ResolvedDatabricksExistingClusterConfig
            | ResolvedDatabricksServerlessConfig,
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
        OpSpec | None,
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
    assets_by_job_task_key: Annotated[
        dict[str, dict[str, list[ResolvedAssetSpec]]] | None,
        Resolver.default(
            description="Optional mapping of Databricks job names to task keys to lists of Dagster AssetSpecs. "
            "Structure: {job_name: {task_key: [AssetSpec, ...]}}. "
            "Both job name and task key are required to uniquely identify a task.",
        ),
    ] = None

    @cached_property
    def databricks_config(self) -> DatabricksConfig:
        return DatabricksConfig(databricks_config_path=self.databricks_config_path)

    @cached_property
    def asset_specs_by_job_task_key(self) -> dict[str, dict[str, list[AssetSpec]]]:
        tasks_by_job_and_task_key = self.databricks_config.tasks_by_job_and_task_key

        # Build default specs for all tasks
        default_specs: dict[str, dict[str, AssetSpec]] = {}
        for job_name, tasks_map in tasks_by_job_and_task_key.items():
            default_specs[job_name] = {}
            for task_key, task in tasks_map.items():
                default_specs[job_name][task_key] = self.get_asset_spec(task=task)

        # Determine which tasks have user-provided specs
        provided_specs = self.assets_by_job_task_key or {}

        result: dict[str, dict[str, list[AssetSpec]]] = {}
        for job_name, default_tasks in default_specs.items():
            result[job_name] = {}
            for task_key, default_spec in default_tasks.items():
                user_specs = (provided_specs.get(job_name) or {}).get(task_key)
                if user_specs is None:
                    result[job_name][task_key] = [default_spec]
                else:
                    merged: list[AssetSpec] = []
                    for spec in user_specs:
                        curr_spec = spec
                        if not curr_spec.description:
                            curr_spec = curr_spec.replace_attributes(
                                description=default_spec.description
                            )
                        curr_spec = curr_spec.merge_attributes(
                            metadata=default_spec.metadata,
                            kinds=default_spec.kinds,
                        )
                        merged.append(curr_spec)
                    result[job_name][task_key] = merged

        return result

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
            metadata={
                "task_key": MetadataValue.text(task.task_key),
                "job_name": MetadataValue.text(task.job_name),
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
        component_defs_path_as_python_str = snake_case(
            str(os.path.relpath(context.component_path.file_path, start=context.project_root))
        )

        databricks_assets = []
        for job_name, tasks_map in self.asset_specs_by_job_task_key.items():
            # Collect all specs for this job and build a task_key_map
            job_specs: list[AssetSpec] = []
            task_key_map: dict[AssetKey, str] = {}
            for task_key, asset_specs in tasks_map.items():
                for spec in asset_specs:
                    job_specs.append(spec)
                    task_key_map[spec.key] = task_key

            op_prefix = self.op.name if self.op and self.op.name else "databricks"
            safe_job_name = snake_case(job_name)

            @multi_asset(
                name=f"{op_prefix}_{safe_job_name}_multi_asset_{component_defs_path_as_python_str}",
                specs=job_specs,
                can_subset=True,
                op_tags=self.op.tags if self.op else None,
                description=self.op.description if self.op else None,
                pool=self.op.pool if self.op else None,
                backfill_policy=self.op.backfill_policy if self.op else None,
            )
            def _databricks_job_multi_asset(
                context: AssetExecutionContext,
                databricks: DatabricksWorkspace,
            ):
                """Multi-asset that runs tasks of a Databricks job."""
                yield from databricks.submit_and_poll(
                    component=self,
                    context=context,
                )

            databricks_assets.append(_databricks_job_multi_asset)

        return Definitions(assets=databricks_assets, resources={"databricks": self.workspace})
