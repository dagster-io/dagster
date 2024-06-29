from typing import List, Literal, Sequence

from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.declarative_scheduling.scheduling_condition import (
    SchedulingCondition,
)
from dagster._core.errors import DagsterInvalidDefinitionError

from .blueprint import Blueprint, BlueprintDefinitions


class ScheduledAssetsBlueprint(Blueprint):
    """A set of assets on a common schedule.

    Example YAML file:

    .. code-block:: yaml

            type: dagster/scheduled_assets
            cron_schedule: "0 0 * * *"
            assets:
            - type: dagster/shell_command
              command: ["echo", "'hello'"]
              assets:
                key: asset1
            - type: dagster/shell_command
              command: ["echo", "'hello again'"]
              assets:
                key: asset2
                deps: asset1
    """

    type: Literal["dagster/scheduled_assets"] = "dagster/scheduled_assets"
    assets: Sequence[Blueprint]
    cron_schedule: str

    def build_defs(self) -> BlueprintDefinitions:
        cron_auto_materialize_policy = AutoMaterializePolicy.from_scheduling_condition(
            SchedulingCondition.on_cron(cron_schedule=self.cron_schedule)
        )

        assets_with_schedule: List[AssetsDefinition] = []

        for asset_blueprint in self.assets:
            asset_blueprint_defs = asset_blueprint.build_defs_add_context_to_errors()

            if BlueprintDefinitions(assets=asset_blueprint_defs.assets) != asset_blueprint_defs:
                raise DagsterInvalidDefinitionError(
                    "ScheduledAssetsBlueprint must only contain assets, found other definitions"
                )

            assets_defs = list(asset_blueprint_defs.assets)
            if len(assets_defs) != 1:
                raise DagsterInvalidDefinitionError(
                    f"Blueprint must define exactly one AssetsDefinition, found {len(assets_defs)}"
                )

            assets_def = assets_defs[0]
            if not isinstance(assets_def, AssetsDefinition):
                raise DagsterInvalidDefinitionError(
                    f"Expected AssetsDefinition, found {type(assets_def).__name__}"
                )

            assets_with_schedule.append(
                AssetsDefinition.dagster_internal_init(
                    **{
                        **assets_def.get_attributes_dict(),
                        "auto_materialize_policy": cron_auto_materialize_policy,
                    }
                )
            )

        return BlueprintDefinitions(assets=assets_with_schedule)
