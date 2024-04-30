import datetime

from dagster._utils.schedules import reverse_cron_string_iterator

from .asset_condition import AssetCondition, AssetConditionResult
from .scheduling_condition_evaluation_context import SchedulingConditionEvaluationContext


class UpdatedSinceCronCondition(AssetCondition):
    cron_schedule: str
    cron_timezone: str

    @property
    def condition_description(self) -> str:
        return f"Updated since latest tick of {self.cron_schedule} ({self.cron_timezone})"

    def _get_previous_cron_tick(
        self, context: SchedulingConditionEvaluationContext
    ) -> datetime.datetime:
        previous_ticks = reverse_cron_string_iterator(
            end_timestamp=context.effective_dt.timestamp(),
            cron_string=self.cron_schedule,
            execution_timezone=self.cron_timezone,
        )
        return next(previous_ticks)

    def evaluate(self, context: SchedulingConditionEvaluationContext) -> AssetConditionResult:
        previous_cron_tick = self._get_previous_cron_tick(context)

        if (
            # never evaluated
            context.previous_evaluation is None
            # partitions def has changed
            or not context.previous_evaluation.true_subset.is_compatible_with_partitions_def(
                context.partitions_def
            )
            # not evaluated since latest schedule tick
            or (context.previous_evaluation_timestamp or 0) < previous_cron_tick.timestamp()
            # has new set of candidates
            or context.has_new_candidate_subset()
            # asset updated since latest evaluation
            or context.target_asset_updated_since_previous_evaluation()
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
            true_subset = context.previous_evaluation.true_subset.as_valid(context.partitions_def)

        return AssetConditionResult.create(context, true_subset)
