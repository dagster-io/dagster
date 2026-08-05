# ruff: noqa
from datetime import datetime

import dagster as dg


# start_time_aware_condition
automation_condition = (
    dg.AutomationCondition.any_deps_match(
        dg.AutomationCondition.newly_updated().since(
            dg.AutomationCondition.cron_tick_passed("0 0 * * *")
        )
        & ~dg.AutomationCondition.executed_with_root_target()
    ).newly_true()
    & ~dg.AutomationCondition.in_progress()
    & dg.AutomationCondition.in_latest_time_window()
)
# end_time_aware_condition


# Replace with a real cutoff for your deployment.
CUTOFF_DATETIME = datetime(2025, 1, 1)


# start_recent_partitions_only
class RecentPartitionsOnlyCondition(dg.AutomationCondition):
    """Only allow materialization of partitions whose key is on or after CUTOFF_DATETIME."""

    def evaluate(self, context: dg.AutomationContext) -> dg.AutomationResult:
        if not context.partitions_def:
            return dg.AutomationResult(context, context.candidate_subset)

        all_partitions = context.candidate_subset.expensively_compute_partition_keys()
        recent_partitions = {
            pk for pk in all_partitions if datetime.fromisoformat(pk) >= CUTOFF_DATETIME
        }

        true_subset = context.candidate_subset.compute_intersection_with_partition_keys(
            recent_partitions
        )
        return dg.AutomationResult(context, true_subset=true_subset)


# end_recent_partitions_only
