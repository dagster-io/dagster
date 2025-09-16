from collections.abc import Mapping, Sequence, Set
from typing import TYPE_CHECKING, Optional

from dagster_shared.serdes import whitelist_for_serdes

from dagster._core.asset_graph_view.entity_subset import EntitySubset
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.declarative_automation.automation_context import AutomationContext
from dagster._core.definitions.declarative_automation.operands.subset_automation_condition import (
    SubsetAutomationCondition,
)
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.loader import LoadingContext
from dagster._record import record

if TYPE_CHECKING:
    from dagster._core.event_api import EventLogRecord
    from dagster._core.storage.dagster_run import RunRecord


@whitelist_for_serdes
@record
class LatestRunExecutedWithRootTargetCondition(SubsetAutomationCondition):
    @property
    def name(self) -> str:
        return "executed_with_root_target"

    async def compute_subset(self, context: AutomationContext) -> EntitySubset:  # pyright: ignore[reportIncompatibleMethodOverride]
        def _filter_fn(run_record: "RunRecord") -> bool:
            if context.key == context.root_context.key:
                # this happens when this is evaluated for a self-dependent asset. in these cases,
                # it does not make sense to consider the asset as having been executed with itself
                # as the partition key of the target is necessarily different than the partition
                # key of the query key
                return False
            asset_selection = run_record.dagster_run.asset_selection or set()
            check_selection = run_record.dagster_run.asset_check_selection or set()
            return context.root_context.key in (asset_selection | check_selection)

        return await context.asset_graph_view.compute_latest_run_matches_subset(
            from_subset=context.candidate_subset, filter_fn=_filter_fn
        )


def _run_tag_filter_fn(
    run_record: "RunRecord",
    tag_keys: Optional[Set[str]],
    tag_values: Optional[Mapping[str, str]],
) -> bool:
    if tag_keys and not all(key in run_record.dagster_run.tags for key in tag_keys):
        return False
    if tag_values and not all(
        run_record.dagster_run.tags.get(key) == value for key, value in tag_values.items()
    ):
        return False
    return True


async def _get_run_records_from_materializations(
    materializations: Sequence["EventLogRecord"],
    context: LoadingContext,
) -> Sequence["RunRecord"]:
    from dagster._core.storage.dagster_run import RunRecord

    run_ids = list({record.run_id for record in materializations if record.run_id})
    if not run_ids:
        return []

    run_records = await RunRecord.gen_many(context, run_ids)
    return [record for record in run_records if record]


def _get_run_tag_filter_name(
    base_name: str,
    tag_keys: Optional[Set[str]],
    tag_values: Optional[Mapping[str, str]],
) -> str:
    props = []
    name = base_name
    if tag_keys is not None:
        tag_key_str = ",".join(sorted(tag_keys))
        props.append(f"tag_keys={{{tag_key_str}}}")
    if tag_values is not None:
        tag_value_str = ",".join([f"{key}:{value}" for key, value in sorted(tag_values.items())])
        props.append(f"tag_values={{{tag_value_str}}}")

    if props:
        name += f"({', '.join(props)})"
    return name


@whitelist_for_serdes
@record
class LatestRunExecutedWithTagsCondition(SubsetAutomationCondition):
    tag_keys: Optional[Set[str]] = None
    tag_values: Optional[Mapping[str, str]] = None

    @property
    def name(self) -> str:
        return _get_run_tag_filter_name("executed_with_tags", self.tag_keys, self.tag_values)

    async def compute_subset(self, context: AutomationContext) -> EntitySubset:  # pyright: ignore[reportIncompatibleMethodOverride]
        return await context.asset_graph_view.compute_latest_run_matches_subset(
            from_subset=context.candidate_subset,
            filter_fn=lambda run_record: _run_tag_filter_fn(
                run_record, self.tag_keys, self.tag_values
            ),
        )


@whitelist_for_serdes
@record
class AnyNewUpdateHasRunTagsCondition(SubsetAutomationCondition[AssetKey]):
    tag_keys: Optional[Set[str]] = None
    tag_values: Optional[Mapping[str, str]] = None

    @property
    def name(self) -> str:
        return _get_run_tag_filter_name(
            "any_new_update_has_run_tags", self.tag_keys, self.tag_values
        )

    async def compute_subset(self, context: AutomationContext[AssetKey]) -> EntitySubset[AssetKey]:  # pyright: ignore[reportIncompatibleMethodOverride]
        if (
            not context.previous_temporal_context
            or not context.previous_temporal_context.last_event_id
        ):
            return context.get_empty_subset()

        new_materializations = context.asset_graph_view.get_inner_queryer_for_back_compat().get_asset_materializations_updated_after_cursor(
            asset_key=context.key,
            after_cursor=context.previous_temporal_context.last_event_id,
        )
        if not new_materializations:
            return context.get_empty_subset()

        run_records = await _get_run_records_from_materializations(
            new_materializations,
            context.asset_graph_view,
        )

        valid_run_ids: Set[str] = {
            run_record.dagster_run.run_id
            for run_record in run_records
            if _run_tag_filter_fn(run_record, self.tag_keys, self.tag_values)
        }

        valid_partition_keys = set()

        for materialization in new_materializations:
            if materialization.run_id and (materialization.run_id in valid_run_ids):
                valid_partition_keys.add(materialization.partition_key)

        return context.asset_graph_view.get_asset_subset_from_asset_partitions(
            key=context.key,
            asset_partitions={
                AssetKeyPartitionKey(context.key, partition_key)
                for partition_key in valid_partition_keys
            },
            validate_existence=True,
        )


@whitelist_for_serdes
@record
class AllNewUpdatesHaveRunTagsCondition(SubsetAutomationCondition[AssetKey]):
    tag_keys: Optional[Set[str]] = None
    tag_values: Optional[Mapping[str, str]] = None

    @property
    def name(self) -> str:
        return _get_run_tag_filter_name(
            "all_new_updates_have_run_tags", self.tag_keys, self.tag_values
        )

    async def compute_subset(self, context: AutomationContext[AssetKey]) -> EntitySubset[AssetKey]:  # pyright: ignore[reportIncompatibleMethodOverride]
        if (
            not context.previous_temporal_context
            or not context.previous_temporal_context.last_event_id
        ):
            return context.get_empty_subset()

        new_materializations = context.asset_graph_view.get_inner_queryer_for_back_compat().get_asset_materializations_updated_after_cursor(
            asset_key=context.key,
            after_cursor=context.previous_temporal_context.last_event_id,
        )
        if not new_materializations:
            return context.get_empty_subset()

        run_records = await _get_run_records_from_materializations(
            new_materializations,
            context.asset_graph_view,
        )

        invalid_run_ids = {
            run_record.dagster_run.run_id
            for run_record in run_records
            if not _run_tag_filter_fn(run_record, self.tag_keys, self.tag_values)
        }

        materialized_partition_keys = set()
        invalid_partition_keys = set()

        for materialization in new_materializations:
            materialized_partition_keys.add(materialization.partition_key)
            if not materialization.run_id or (materialization.run_id in invalid_run_ids):
                invalid_partition_keys.add(materialization.partition_key)

        valid_partition_keys = materialized_partition_keys - invalid_partition_keys

        return context.asset_graph_view.get_asset_subset_from_asset_partitions(
            key=context.key,
            asset_partitions={
                AssetKeyPartitionKey(context.key, partition_key)
                for partition_key in valid_partition_keys
            },
            validate_existence=True,
        )
