import json
from enum import Enum
from typing import List, Literal, Optional, cast

from dagster import AssetExecutionContext
from dagster._core.blueprints.blueprint import Blueprint, BlueprintDefinitions
from dagster._core.definitions.time_window_partitions import (
    DailyPartitionsDefinition,
    HourlyPartitionsDefinition,
)
from pydantic import BaseModel, Field

from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.core.resources_v2 import DbtCliResource
from dagster_dbt.dbt_project import DbtProject


class DbtInvocationPartitionType(Enum):
    DAILY = "daily"
    HOURLY = "hourly"


class DbtInvocationPartitionDefinition(BaseModel):
    type: DbtInvocationPartitionType = Field(
        ..., description="The type of partitioning to use for the dbt invocation."
    )
    start_date: str = Field(..., description="The start date for the partitioning.")
    timezone: Optional[str] = Field(None, description="The timezone to use for the partitioning.")

    partition_start_var_name: str = Field(
        "start_date",
        description="The name of the dbt variable to use for the start date in the dbt invocation.",
    )
    partition_end_var_name: str = Field(
        "end_date",
        description="The name of the dbt variable to use for the end date in the dbt invocation.",
    )


class DbtInvocationBlueprint(Blueprint):
    """Blueprint which creates a set of Dagster assets for a dbt invocation."""

    type: Literal["dagster_dbt/invication_assets"] = "dagster_dbt/invication_assets"
    name: str = Field(..., description="The name of the dagster op.")

    dbt_resource_key: str = Field(
        "dbt", description="The name of the dbt resource to use for the invocation."
    )

    project_dir: str = Field(..., description="The directory of the dbt project.")
    target: Optional[str] = Field(
        None, description="The target from your dbt `profiles.yml` to use for execution."
    )

    select: str = Field(
        "fqn:*",
        description=(
            "A dbt selection string for the models in the project to run. "
            "Defaults to ``fqn:*`` which selects all models."
        ),
    )
    exclude: Optional[str] = Field(
        None,
        description="A dbt selection string for the models in the project to exclude.",
    )

    command: str = Field(
        "build",
        description="The dbt command to run. Defaults to `build`.",
    )
    command_args: List[str] = Field(
        [],
        description="Additional arguments to pass to the dbt command.",
    )

    partition: Optional[DbtInvocationPartitionDefinition] = Field(
        None,
        description="Partitioning configuration for the dbt invocation.",
    )

    def build_defs(self) -> BlueprintDefinitions:
        project = DbtProject(self.project_dir, target=self.target)

        partition_definition = None
        if self.partition:
            if self.partition.type == DbtInvocationPartitionType.DAILY:
                partition_definition = DailyPartitionsDefinition(
                    start_date=self.partition.start_date, timezone=self.partition.timezone
                )
            elif self.partition.type == DbtInvocationPartitionType.HOURLY:
                partition_definition = HourlyPartitionsDefinition(
                    start_date=self.partition.start_date, timezone=self.partition.timezone
                )

        @dbt_assets(
            name=self.name,
            manifest=project.manifest_path,
            select=self.select,
            exclude=self.exclude,
            required_resource_keys={self.dbt_resource_key},
            partitions_def=partition_definition,
        )
        def _dbt_invocation_assets(context: AssetExecutionContext):
            args_to_pass = self.command_args
            if self.partition:
                dbt_vars = {
                    self.partition.partition_start_var_name: context.partition_time_window.start.isoformat(),
                    self.partition.partition_end_var_name: context.partition_time_window.end.isoformat(),
                }
                args_to_pass += ["--vars", json.dumps(dbt_vars)]

            dbt = cast(DbtCliResource, getattr(context.resources, self.dbt_resource_key))
            yield from dbt.cli(["build", *self.command_args], context=context).stream()

        return BlueprintDefinitions(assets=[_dbt_invocation_assets])
