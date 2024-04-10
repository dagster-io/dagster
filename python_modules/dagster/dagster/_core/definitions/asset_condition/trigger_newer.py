from typing import NamedTuple

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_subset import AssetSubset
from dagster._serdes.serdes import whitelist_for_serdes

from .asset_condition import AssetCondition, AssetConditionResult
from .asset_condition_evaluation_context import AssetConditionEvaluationContext


@whitelist_for_serdes
class TriggerNewerAssetCondition(  # type: ignore
    NamedTuple("_TriggerNewerAssetCondition", [("trigger", AssetKey)]),
    AssetCondition,
):
    @property
    def description(self) -> str:
        return "The specified trigger has updated since the last time this was requested."

    def evaluate(self, context: AssetConditionEvaluationContext) -> "AssetConditionResult":
        # all asset partitions of the trigger which have a new version since the previous tick
        newly_updated_trigger_asset_partititons = (
            context.instance_queryer.get_asset_partitions_updated_after_cursor(
                asset_key=self.trigger,
                asset_partitions=None,
                after_cursor=context.previous_max_storage_id,
                respect_materialization_data_versions=False,
            )
        )

        # to keep the code simple for now, we'll assume that the trigger always shares a
        # PartitionsDefinition with the evaluated asset, and so we don't need to do any partition
        # mapping stuff
        has_newly_updated_trigger_asset_subset = AssetSubset.from_asset_partitions_set(
            asset_key=context.asset_key,
            partitions_def=context.partitions_def,
            asset_partitions_set=newly_updated_trigger_asset_partititons,
        )

        true_subset = (
            # if something had a newly updated trigger on the previous tick, and hasn't been
            # materialized requested or discarded since then, it still has a newly updated trigger
            context.previous_true_subset.as_valid(context.partitions_def)
            - context.materialized_requested_or_discarded_since_previous_tick_subset
        ) | has_newly_updated_trigger_asset_subset

        return AssetConditionResult.create(context, true_subset=true_subset)
