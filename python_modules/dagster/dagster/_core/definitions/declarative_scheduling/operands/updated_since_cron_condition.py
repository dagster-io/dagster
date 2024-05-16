import datetime

from dagster._serdes.serdes import whitelist_for_serdes
from dagster._utils.schedules import reverse_cron_string_iterator

from ..scheduling_condition import SchedulingCondition, SchedulingResult
from ..scheduling_context import SchedulingContext


@whitelist_for_serdes
class UpdatedSinceCronCondition(SchedulingCondition):
    cron_schedule: str
    cron_timezone: str

    @property
    def description(self) -> str:
        return f"Updated since latest tick of {self.cron_schedule} ({self.cron_timezone})"

    def _get_previous_cron_tick(self, context: SchedulingContext) -> datetime.datetime:
        previous_ticks = reverse_cron_string_iterator(
            end_timestamp=context.effective_dt.timestamp(),
            cron_string=self.cron_schedule,
            execution_timezone=self.cron_timezone,
        )
        return next(previous_ticks)

    def evaluate(self, context: SchedulingContext) -> SchedulingResult:
        previous_cron_tick = self._get_previous_cron_tick(context)

        if (
            # never evaluated or evaluation info is no longer valid
            context.previous_evaluation_info is None
            or context.previous_evaluation_node is None
            or context.previous_evaluation_node.true_slice is None
            # not evaluated since latest schedule tick
            or context.previous_evaluation_info.temporal_context.effective_dt < previous_cron_tick
            # has new set of candidates
            or context.previous_evaluation_node.candidate_slice != context.candidate_slice
        ):
            # do a full recomputation
            updated_subset = (
                context.legacy_context.instance_queryer.get_asset_subset_updated_after_time(
                    asset_key=context.asset_key,
                    after_time=previous_cron_tick,
                )
            )
            # TODO: implement this on the AssetGraphView
            true_slice = context.asset_graph_view.get_asset_slice_from_valid_subset(updated_subset)
        else:
            # do an incremental updated, adding in any asset partitions that have been materialized
            # since the previous evaluation
            true_slice = context.previous_evaluation_node.true_slice.compute_union(
                context.asset_graph_view.compute_updated_since_cursor_slice(
                    asset_key=context.asset_key, cursor=context.previous_evaluation_max_storage_id
                )
            )

        return SchedulingResult.create(
            context, context.candidate_slice.compute_intersection(true_slice)
        )
