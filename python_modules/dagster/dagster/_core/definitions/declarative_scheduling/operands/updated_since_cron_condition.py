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
            # partitions def has changed
            or not context.previous_evaluation_node.true_subset.is_compatible_with_partitions_def(
                context.partitions_def
            )
            # not evaluated since latest schedule tick
            or context.previous_evaluation_info.temporal_context.effective_dt < previous_cron_tick
            # has new set of candidates
            or context.has_new_candidate_subset()
            # asset updated since latest evaluation
            or context.asset_updated_since_previous_tick()
        ):
            # do a full recomputation
            true_subset = (
                context.candidate_subset
                & context._queryer.get_asset_subset_updated_after_time(  # noqa
                    asset_key=context.asset_key,
                    after_time=previous_cron_tick,
                )
            )
        else:
            true_subset = context.previous_evaluation_node.true_subset.as_valid(
                context.partitions_def
            )

        return SchedulingResult.create(context, true_subset)
