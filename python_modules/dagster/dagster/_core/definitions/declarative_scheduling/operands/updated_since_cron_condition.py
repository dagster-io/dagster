import datetime

from dagster._utils.schedules import reverse_cron_string_iterator

from ..legacy.asset_condition import AssetCondition
from ..scheduling_condition import SchedulingResult
from ..scheduling_context import SchedulingContext


class UpdatedSinceCronCondition(AssetCondition):
    cron_schedule: str
    cron_timezone: str

    @property
    def condition_description(self) -> str:
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
            # never evaluated
            context.previous_evaluation_info is None
            or context.previous_evaluation_node is None
            # not evaluated since latest schedule tick
            or context.previous_evaluation_info.temporal_context.effective_dt < previous_cron_tick
            # has new set of candidates
            or context.previous_evaluation_node.candidate_slice != context.candidate_slice
            # asset updated since latest evaluation
            or context.asset_updated_since_previous_tick()
        ):
            # do a full recomputation
            updated_subset = (
                context.legacy_context.instance_queryer.get_asset_subset_updated_after_time(
                    asset_key=context.asset_key,
                    after_time=previous_cron_tick,
                )
            )
            # TODO: implement this on the AssetGraphView
            true_slice = context.candidate_slice.compute_intersection(
                context.asset_graph_view.get_asset_slice_from_subset(updated_subset)
            )
        else:
            true_slice = context.previous_evaluation_node.true_slice

        return SchedulingResult.create(context, true_slice)
